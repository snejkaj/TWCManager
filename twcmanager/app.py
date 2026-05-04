from __future__ import annotations

import time
from dataclasses import dataclass, field

from .config import Settings
from .core.load_balancer import compute_allowed_amps
from .core.charging_policy import OfferPolicyState, enforce_offer_policy
from .providers.base import MeterReading, PowerMeterProvider
from .providers.tibber import TibberPulseProvider
from .protocol.packets import (
    parse_linkready,
    parse_slave_heartbeat,
    build_master_heartbeat,
    build_master_linkready2,
)
from .protocol.transport import TwcTransport


@dataclass
class SlaveState:
    twc_id: str
    amps_actual: float = 0.0
    amps_offered: float = 0.0
    offer_policy: OfferPolicyState = field(default_factory=OfferPolicyState)


@dataclass
class TWCManagerApp:
    settings: Settings
    slaves: dict[str, SlaveState] = field(default_factory=dict)
    meter: PowerMeterProvider | None = None
    transport: TwcTransport | None = None
    meter_degraded: bool = False
    last_meter_error: str = ""

    def setup_meter(self) -> None:
        if self.settings.tibber.enabled:
            self.meter = TibberPulseProvider(
                access_token=self.settings.tibber.access_token,
                home_id=self.settings.tibber.home_id,
            )

    def setup_transport(self) -> None:
        if self.transport is not None:
            return

        import serial

        port = serial.Serial(self.settings.rs485_adapter, baudrate=self.settings.baud, timeout=0)
        self.transport = TwcTransport(port)

    def handle_protocol_payload(self, payload: bytes) -> None:
        linkready = parse_linkready(payload)
        if linkready is not None:
            key = linkready.sender_id.hex().upper()
            if key not in self.slaves:
                self.slaves[key] = SlaveState(twc_id=key)
            if self.transport is not None:
                self.transport.send_payload(build_master_linkready2(bytes.fromhex(self.settings.fake_twc_id_hex)))
            return

        heartbeat = parse_slave_heartbeat(payload)
        if heartbeat is not None:
            key = heartbeat.sender_id.hex().upper()
            if key not in self.slaves:
                self.slaves[key] = SlaveState(twc_id=key)
            self.slaves[key].amps_actual = heartbeat.amps_actual

    def total_charging_amps(self) -> float:
        return sum(slave.amps_actual for slave in self.slaves.values())

    def recalc_target(self, reading: MeterReading) -> float:
        return compute_allowed_amps(
            main_fuse_amps=self.settings.main_fuse_amps,
            household_grid_amps=reading.grid_amps,
            current_charging_amps=self.total_charging_amps(),
            min_amps_per_twc=self.settings.min_amps_per_twc,
            wiring_max_amps_all_twcs=self.settings.wiring_max_amps_all_twcs,
            safety_margin_amps=self.settings.safety_margin_amps,
        )

    def degraded_target(self) -> float:
        """Return a conservative total charging target when live meter data is unavailable."""
        installation_limit = min(
            self.settings.wiring_max_amps_all_twcs,
            max(0.0, self.settings.main_fuse_amps - self.settings.safety_margin_amps),
        )
        target = min(max(0.0, self.settings.degraded_mode_max_amps), installation_limit)
        if 0 < target < self.settings.min_amps_per_twc:
            return 0.0
        return float(int(target))

    def _distribute(self, target_total: float, force: bool = False) -> None:
        if not self.slaves:
            return

        ordered = sorted(self.slaves.values(), key=lambda s: s.twc_id)
        base = int(target_total) // len(ordered)
        remainder = int(target_total) % len(ordered)

        for i, slave in enumerate(ordered):
            offered = base + (1 if i < remainder else 0)
            if 0 < offered < self.settings.min_amps_per_twc:
                offered = 0
            if force:
                slave.amps_offered = float(offered)
                slave.offer_policy.last_offered_amps = float(offered)
                slave.offer_policy.last_change_ts = time.time()
                continue
            slave.amps_offered = enforce_offer_policy(
                desired_amps=float(offered),
                min_amps_per_twc=self.settings.min_amps_per_twc,
                state=slave.offer_policy,
            )

    def tick(self) -> tuple[MeterReading, float]:
        reading = MeterReading(grid_power_w=0.0, voltage_v=230.0)
        try:
            if self.meter is None:
                raise RuntimeError("no power meter configured")
            reading = self.meter.get_reading()
            target_total = self.recalc_target(reading)
            self.meter_degraded = False
            self.last_meter_error = ""
        except Exception as exc:
            self.meter_degraded = True
            self.last_meter_error = str(exc)
            target_total = self.degraded_target()

        self._distribute(target_total, force=self.meter_degraded)
        return reading, target_total

    def process_protocol_once(self) -> int:
        if self.transport is None:
            return 0

        payloads = self.transport.poll()
        for payload in payloads:
            self.handle_protocol_payload(payload)

        fake_master = bytes.fromhex(self.settings.fake_twc_id_hex)
        for slave in self.slaves.values():
            target = slave.amps_offered
            self.transport.send_payload(build_master_heartbeat(fake_master, bytes.fromhex(slave.twc_id), target))
        return len(payloads)

    def run(self, loop_delay_s: float = 1.0, with_serial: bool = False) -> None:
        self.setup_meter()
        if with_serial:
            self.setup_transport()

        print("Starting modern TWCManager (modular rewrite)")

        while True:
            try:
                reading, target_total = self.tick()
                msg_count = self.process_protocol_once() if with_serial else 0
                per_slave = 0.0 if not self.slaves else target_total / len(self.slaves)
                print(
                    f"mode={'degraded' if self.meter_degraded else 'normal'}, "
                    f"grid={reading.grid_amps:.1f}A, charge={self.total_charging_amps():.1f}A, "
                    f"target_total={target_total:.1f}A, per_slave={per_slave:.1f}A, "
                    f"rx_msgs={msg_count}"
                )
            except Exception as exc:
                print(f"control-loop warning: {exc}")

            time.sleep(loop_delay_s)
