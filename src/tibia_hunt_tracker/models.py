from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    id: str
    name: str
    entity_type: str
    duration_seconds: int
    default_warning_seconds: int
    voice_label: str
    words: str | None = None
    vocations: tuple[str, ...] = ()
    item_category: str | None = None
    effect_kind: str | None = None
    can_end_early: bool = False

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CatalogEntry":
        return cls(
            id=payload["id"],
            name=payload["name"],
            entity_type=payload["entity_type"],
            duration_seconds=int(payload["duration_seconds"]),
            default_warning_seconds=int(payload["default_warning_seconds"]),
            voice_label=payload.get("voice_label") or payload["name"],
            words=payload.get("words"),
            vocations=tuple(payload.get("vocations", ())),
            item_category=payload.get("item_category"),
            effect_kind=payload.get("effect_kind"),
            can_end_early=bool(payload.get("can_end_early", False)),
        )


@dataclass(slots=True)
class TimerConfig:
    catalog_id: str
    name: str
    voice_label: str
    duration_seconds: int
    warning_seconds: int
    voice_enabled: bool = True
    notification_enabled: bool = True

    def __post_init__(self) -> None:
        if self.duration_seconds <= 0:
            raise ValueError("A duração deve ser maior que zero.")
        if not 0 <= self.warning_seconds < self.duration_seconds:
            raise ValueError("O pré-alerta deve ser menor que a duração.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TimerConfig":
        return cls(
            catalog_id=str(payload["catalog_id"]),
            name=str(payload["name"]),
            voice_label=str(payload.get("voice_label") or payload["name"]),
            duration_seconds=int(payload["duration_seconds"]),
            warning_seconds=int(payload.get("warning_seconds", 0)),
            voice_enabled=bool(payload.get("voice_enabled", True)),
            notification_enabled=bool(payload.get("notification_enabled", True)),
        )
