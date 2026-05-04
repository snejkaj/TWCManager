from __future__ import annotations

from dataclasses import dataclass
from .base import MeterReading, PowerMeterProvider


@dataclass
class TibberPulseProvider(PowerMeterProvider):
    """Read live household power from Tibber Home liveMeasurement.

    Uses Tibber GraphQL over HTTPS. This is poll-based and intentionally
    synchronous to keep runtime dependencies minimal.
    """

    access_token: str
    home_id: str
    timeout_s: int = 10

    def get_reading(self) -> MeterReading:
        query = {
            "query": """
            query($homeId: ID!) {
              viewer {
                home(id: $homeId) {
                  liveMeasurement {
                    power
                    powerProduction
                    voltagePhase1
                  }
                }
              }
            }
            """,
            "variables": {"homeId": self.home_id},
        }
        import requests

        response = requests.post(
            "https://api.tibber.com/v1-beta/gql",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
            json=query,
            timeout=self.timeout_s,
        )
        response.raise_for_status()
        payload = response.json()

        measurement = (
            payload.get("data", {})
            .get("viewer", {})
            .get("home", {})
            .get("liveMeasurement", {})
        )

        # Tibber 'power' is import (+) / export (-) in W. Keep that convention.
        grid_w = float(measurement.get("power") or 0.0)
        # If production is available and positive, net it out conservatively.
        production_w = float(measurement.get("powerProduction") or 0.0)
        if production_w > 0:
            grid_w -= production_w

        voltage = float(measurement.get("voltagePhase1") or 230.0)
        return MeterReading(grid_power_w=grid_w, voltage_v=voltage)
