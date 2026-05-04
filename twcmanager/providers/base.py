from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MeterReading:
    # Positive = import from grid, negative = export
    grid_power_w: float
    voltage_v: float = 230.0

    @property
    def grid_amps(self) -> float:
        if self.voltage_v <= 0:
            return 0.0
        return self.grid_power_w / self.voltage_v


class PowerMeterProvider:
    def get_reading(self) -> MeterReading:
        raise NotImplementedError
