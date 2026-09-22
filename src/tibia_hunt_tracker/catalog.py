from __future__ import annotations

import json
import sys
from pathlib import Path

from .models import CatalogEntry


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parents[2]


def load_catalog(path: Path | None = None) -> list[CatalogEntry]:
    catalog_path = path or project_root() / "data" / "tracker_catalog.json"
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    entries = [CatalogEntry.from_dict(row) for row in payload["entries"]]
    ids = [entry.id for entry in entries]
    if len(ids) != len(set(ids)):
        raise ValueError("O catálogo contém IDs duplicados.")
    return sorted(entries, key=lambda entry: (entry.entity_type, entry.name.casefold()))
