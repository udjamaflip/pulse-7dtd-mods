"""Application configuration dataclass.

Supports loading from environment variables and from a persisted JSON file.
No credentials or personal data are stored here.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict


def _e(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


@dataclass
class AppConfig:
    app_port: int = 8003
    data_dir: Path = field(default_factory=lambda: Path(_e("DATA_DIR", "./data")))
    database_path: Path = field(
        default_factory=lambda: Path(_e("DATA_DIR", "./data")) / "7dtd-modmaker.db"
    )
    default_game_version: str = "v1"

    @classmethod
    def from_env(cls) -> "AppConfig":
        cfg = cls()
        cfg.app_port = int(_e("APP_PORT", str(cfg.app_port)))
        cfg.data_dir = Path(_e("DATA_DIR", str(cfg.data_dir)))
        cfg.database_path = cfg.data_dir / "7dtd-modmaker.db"
        cfg.default_game_version = _e("DEFAULT_GAME_VERSION", cfg.default_game_version)
        return cfg

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppConfig":
        cfg = cls()
        for k, v in data.items():
            if v is None:
                continue
            if k in ("data_dir", "database_path"):
                setattr(cfg, k, Path(str(v)))
            elif k == "app_port":
                setattr(cfg, k, int(v))
            else:
                setattr(cfg, k, v)
        return cfg

    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict

        d = asdict(self)
        d["data_dir"] = str(self.data_dir)
        d["database_path"] = str(self.database_path)
        return d

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
