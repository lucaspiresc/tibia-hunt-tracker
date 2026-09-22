from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .models import TimerConfig
from .catalog import load_catalog


def default_data_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "TibiaHuntTracker"
    return Path.home() / ".tibia_hunt_tracker"


class PresetStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_data_dir() / "presets.json"
        self.spell_ids = {entry.id for entry in load_catalog() if entry.entity_type == "spell"}
        self._presets: dict[str, list[TimerConfig]] = {}
        self.load()

    @property
    def names(self) -> list[str]:
        return sorted(self._presets, key=str.casefold)

    def load(self) -> None:
        if not self.path.exists():
            self._presets = {"Minha Hunt": []}
            return
        try:
            payload: dict[str, Any] = json.loads(self.path.read_text(encoding="utf-8"))
            self._presets = {
                name: [TimerConfig.from_dict(row) for row in rows if row.get("catalog_id") in self.spell_ids]
                for name, rows in payload.get("presets", {}).items()
            }
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            self._presets = {"Minha Hunt": []}
        if not self._presets:
            self._presets = {"Minha Hunt": []}

    def get(self, name: str) -> list[TimerConfig]:
        return [TimerConfig.from_dict(config.to_dict()) for config in self._presets.get(name, [])]

    def save(self, name: str, configs: list[TimerConfig]) -> None:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("O preset precisa de um nome.")
        self._presets[clean_name] = [TimerConfig.from_dict(config.to_dict()) for config in configs
                                     if config.catalog_id in self.spell_ids]
        self._write()

    def delete(self, name: str) -> None:
        if name in self._presets:
            del self._presets[name]
        if not self._presets:
            self._presets["Minha Hunt"] = []
        self._write()

    def duplicate(self, source: str, target: str) -> None:
        if source not in self._presets:
            raise KeyError(source)
        self.save(target, self.get(source))

    def _write(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 3,
            "presets": {
                name: [config.to_dict() for config in configs]
                for name, configs in sorted(self._presets.items())
            },
        }
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.path)
