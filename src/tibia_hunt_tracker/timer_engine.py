from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import time

from .models import TimerConfig


class EventKind(str, Enum):
    WARNING = "warning"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class TimerEvent:
    kind: EventKind
    timer_id: str
    config: TimerConfig
    occurred_at: float


@dataclass(slots=True)
class TimerState:
    config: TimerConfig
    started_at: float
    expires_at: float
    warning_sent: bool = False


class TimerEngine:
    def __init__(self) -> None:
        self._states: dict[str, TimerState] = {}
        self.started_at: float | None = None
        self.running = False

    def start(self, configs: list[TimerConfig], now: float | None = None) -> None:
        instant = time.monotonic() if now is None else now
        if not configs:
            raise ValueError("Selecione pelo menos um timer.")
        self.started_at = instant
        self.running = True
        self._states = {
            config.catalog_id: TimerState(
                config=config,
                started_at=instant,
                expires_at=instant + config.duration_seconds,
            )
            for config in configs
        }

    def stop(self) -> None:
        self.running = False
        self.started_at = None
        self._states.clear()

    def reset(self, timer_id: str, now: float | None = None) -> None:
        if timer_id not in self._states:
            raise KeyError(timer_id)
        instant = time.monotonic() if now is None else now
        state = self._states[timer_id]
        state.started_at = instant
        state.expires_at = instant + state.config.duration_seconds
        state.warning_sent = False

    def tick(self, now: float | None = None) -> list[TimerEvent]:
        if not self.running:
            return []
        instant = time.monotonic() if now is None else now
        events: list[TimerEvent] = []
        for timer_id, state in self._states.items():
            remaining = state.expires_at - instant
            if remaining <= 0:
                events.append(TimerEvent(EventKind.EXPIRED, timer_id, state.config, instant))
                state.started_at = instant
                state.expires_at = instant + state.config.duration_seconds
                state.warning_sent = False
            elif (
                state.config.warning_seconds > 0
                and remaining <= state.config.warning_seconds
                and not state.warning_sent
            ):
                events.append(TimerEvent(EventKind.WARNING, timer_id, state.config, instant))
                state.warning_sent = True
        return events

    def remaining(self, timer_id: str, now: float | None = None) -> float:
        state = self._states[timer_id]
        instant = time.monotonic() if now is None else now
        return max(0.0, state.expires_at - instant)

    def elapsed(self, now: float | None = None) -> float:
        if not self.running or self.started_at is None:
            return 0.0
        instant = time.monotonic() if now is None else now
        return max(0.0, instant - self.started_at)

    @property
    def timer_ids(self) -> tuple[str, ...]:
        return tuple(self._states)
