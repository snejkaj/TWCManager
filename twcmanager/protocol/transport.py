from __future__ import annotations

from dataclasses import dataclass, field

from .messages import build_twc_frame, extract_frames, parse_twc_frame


@dataclass
class TwcTransport:
    """Thin RS-485 transport wrapper for framed TWC messages."""

    serial_port: object
    rx_buffer: bytearray = field(default_factory=bytearray)

    def send_payload(self, payload: bytes) -> None:
        self.serial_port.write(build_twc_frame(payload))

    def poll(self) -> list[bytes]:
        waiting = getattr(self.serial_port, "in_waiting", 0)
        if waiting:
            self.rx_buffer.extend(self.serial_port.read(waiting))

        payloads: list[bytes] = []
        for frame in extract_frames(self.rx_buffer):
            parsed = parse_twc_frame(frame)
            if parsed.checksum_ok:
                payloads.append(parsed.payload)
        return payloads
