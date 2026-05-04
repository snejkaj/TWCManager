from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
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
    degraded_mode_max_amps: float = 0.0
    tibber: TibberConfig = field(default_factory=TibberConfig)


DEFAULT_PATH = Path("settings.json")


def _reject_unknown_fields(data: dict[str, object], cls: type, label: str) -> None:
    known = {item.name for item in fields(cls)}
    unknown = sorted(set(data) - known)
    if unknown:
        raise ValueError(f"Unknown {label} setting(s): {', '.join(unknown)}")


def load_settings(path: Path = DEFAULT_PATH) -> Settings:
    if not path.exists():
        return Settings()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Invalid settings in {path}: top-level value must be an object")

    _reject_unknown_fields(data, Settings, "top-level")
    tibber_data = data.get("tibber", {})
    if not isinstance(tibber_data, dict):
        raise ValueError(f"Invalid settings in {path}: tibber must be an object")
    _reject_unknown_fields(tibber_data, TibberConfig, "tibber")

    tibber = TibberConfig(**tibber_data)
    data["tibber"] = tibber
    return Settings(**data)


def save_settings(settings: Settings, path: Path = DEFAULT_PATH) -> None:
    path.write_text(json.dumps(asdict(settings), indent=2, sort_keys=True), encoding="utf-8")
