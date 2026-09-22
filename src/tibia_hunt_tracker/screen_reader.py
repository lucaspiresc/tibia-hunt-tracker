"""Pixel-only monitor reader. Never enumerates processes or application windows.

Geometry locates candidate HUD regions, not confirmed game identities or casts.
No captured image is persisted or transmitted.
"""
from __future__ import annotations

from dataclasses import dataclass
from queue import Empty, Full, Queue
from threading import Event, Thread
import time

import cv2
import numpy as np


@dataclass(frozen=True)
class Region:
    x: int
    y: int
    width: int
    height: int

    def near(self, other: "Region") -> bool:
        tolerance = max(10, min(self.width, self.height) * .3)
        return all(abs(a - b) <= tolerance for a, b in zip(
            (self.x, self.y, self.width, self.height),
            (other.x, other.y, other.width, other.height)))


def locate_candidates(frame: np.ndarray) -> list[Region]:
    """Find aligned square slots across positions/scales; never assert Tibia identity."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    contours, _ = cv2.findContours(cv2.Canny(gray, 50, 130), cv2.RETR_LIST,
                                  cv2.CHAIN_APPROX_SIMPLE)
    squares: list[Region] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if not (20 <= w <= 100 and .88 <= w / h <= 1.12):
            continue
        if cv2.contourArea(contour) < .65 * w * h:
            continue
        candidate = Region(x, y, w, h)
        if not any(candidate.near(old) for old in squares):
            squares.append(candidate)
        if len(squares) >= 300:
            break  # Bound work on visually dense desktops.
    groups: list[Region] = []
    for anchor in squares:
        for horizontal in (True, False):
            aligned = [s for s in squares
                       if abs(s.width - anchor.width) < anchor.width * .2
                       and abs((s.y if horizontal else s.x) -
                               (anchor.y if horizontal else anchor.x)) < anchor.width * .2]
            aligned.sort(key=lambda s: s.x if horizontal else s.y)
            run: list[Region] = []
            for slot in aligned:
                if run:
                    delta = (slot.x - run[-1].x) if horizontal else (slot.y - run[-1].y)
                    if not .8 * anchor.width <= delta <= 1.5 * anchor.width:
                        run = []
                run.append(slot)
                if len(run) >= 4:
                    left, top = min(s.x for s in run), min(s.y for s in run)
                    region = Region(left, top, max(s.x + s.width for s in run) - left,
                                    max(s.y + s.height for s in run) - top)
                    if not any(region.near(old) for old in groups):
                        groups.append(region)
    # Keep the longest overlapping runs, limiting preview noise and ROI work.
    result: list[Region] = []
    for region in sorted(groups, key=lambda r: r.width * r.height, reverse=True):
        if any(old.x <= region.x and old.y <= region.y and
               old.x + old.width >= region.x + region.width and
               old.y + old.height >= region.y + region.height for old in result):
            continue
        result.append(region)
    return result[:12]


class VisualTracker:
    def __init__(self) -> None:
        self.regions: list[Region] = []
        self._previous: list[Region] = []
        self._next_scan = 0.0

    def inspect(self, frame: np.ndarray, now: float) -> str:
        if frame.size == 0 or float(frame.max()) < 8:
            self.regions = []
            self._previous = []
            self._next_scan = 0
            return "Sem leitura: captura escura ou indisponível."
        # Validate cached regions every frame; disappearance is never a timer event.
        if self.regions:
            valid = []
            for r in self.regions:
                crop = frame[max(0, r.y-4):r.y+r.height+4, max(0, r.x-4):r.x+r.width+4]
                if crop.size and locate_candidates(crop):
                    valid.append(r)
            if len(valid) != len(self.regions):
                self.regions = []
                self._previous = []
                self._next_scan = 0
        if now >= self._next_scan:
            found = locate_candidates(frame)
            self.regions = [r for r in found if any(r.near(p) for p in self._previous)]
            self._previous = found
            self._next_scan = now + 1.0
        if self.regions:
            return f"{len(self.regions)} região(ões) candidata(s) — identidade ainda não confirmada."
        return "Procurando interface — sem leitura confirmada."


@dataclass
class ScreenResult:
    status: str
    preview: np.ndarray | None = None
    elapsed_ms: float = 0


def list_monitors() -> list[dict]:
    import mss
    with mss.mss() as capture:
        return [dict(monitor) for monitor in capture.monitors[1:]]


class ScreenReader:
    def __init__(self, monitor: dict) -> None:
        self.monitor = dict(monitor)
        self.events: Queue[str] = Queue()
        self.results: Queue[ScreenResult] = Queue(maxsize=1)
        self._stop = Event()
        self._thread = Thread(target=self._run, name="screen-reader", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def poll(self) -> ScreenResult | None:
        try:
            return self.results.get_nowait()
        except Empty:
            return None

    def _publish(self, result: ScreenResult) -> None:
        try:
            self.results.put_nowait(result)
        except Full:
            self.poll()
            self.results.put_nowait(result)

    def _run(self) -> None:
        try:
            import mss
            from .equipment import EquipmentTracker
            tracker = EquipmentTracker()
            with mss.mss() as capture:
                while not self._stop.is_set():
                    started = time.monotonic()
                    frame = np.asarray(capture.grab(self.monitor))[:, :, :3].copy()
                    observations, events, _ = tracker.inspect(frame, started)
                    for name in events:
                        self.events.put(name)
                    labels = {"empty": "vazio", "occupied": "equipado", "unknown": "sem leitura"}
                    status = " | ".join(f"{name.capitalize()}: {labels[state]}" for name, state in observations.items())
                    elapsed = time.monotonic() - started
                    self._publish(ScreenResult(status, elapsed_ms=elapsed * 1000))
                    self._stop.wait(max(0, .2 - elapsed))
        except Exception as exc:
            self._publish(ScreenResult(f"Leitura interrompida: {exc}"))
