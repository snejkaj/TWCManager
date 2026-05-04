from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path


@dataclass
class TibberConfig:
    enabled: bool = False
    access_token: str = ""
    home_id: str = ""


@dataclass
class Settings:
    rs485_adapter: str = "/dev/ttyUSB0"
    baud: int = 9600
    fake_master: bool = True
    fake_twc_id_hex: str = "7777"
    min_amps_per_twc: float = 12.0
    wiring_max_amps_all_twcs: float = 40.0
    wiring_max_amps_per_twc: float = 40.0
    green_energy_amps_offset: float = 0.0
    main_fuse_amps: float = 25.0
    safety_margin_amps: float = 2.0
    tibber: TibberConfig = field(default_factory=TibberConfig)


DEFAULT_PATH = Path("settings.json")


def load_settings(path: Path = DEFAULT_PATH) -> Settings:
    if not path.exists():
        return Settings()
    data = json.loads(path.read_text())
    tibber = TibberConfig(**data.get("tibber", {}))
    data["tibber"] = tibber
    return Settings(**data)


def save_settings(settings: Settings, path: Path = DEFAULT_PATH) -> None:
    serializable = {
        **settings.__dict__,
        "tibber": settings.tibber.__dict__,
    }
    path.write_text(json.dumps(serializable, indent=2, sort_keys=True))
