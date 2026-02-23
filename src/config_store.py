"""Persists AppConfig as JSON in the data directory."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from .config import AppConfig


class ConfigStore:
    def __init__(self, path: Optional[Path] = None) -> None:
        data_dir = Path(os.environ.get("DATA_DIR", "./data"))
        self.path = path or data_dir / "7dtd-modmaker-config.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> AppConfig:
        if not self.path.exists():
            return AppConfig.from_env()
        try:
            return AppConfig.from_dict(json.loads(self.path.read_text()))
        except Exception:
            return AppConfig.from_env()

    def save(self, cfg: AppConfig) -> None:
        cfg.ensure_dirs()
        self.path.write_text(json.dumps(cfg.to_dict(), indent=2))

    def ensure(self) -> AppConfig:
        cfg = self.load()
        cfg.ensure_dirs()
        return cfg
