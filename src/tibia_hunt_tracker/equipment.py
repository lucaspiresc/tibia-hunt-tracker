"""Conservative, calibrated pixel matching; no access to game internals."""
from dataclasses import dataclass
import time

import cv2
import numpy as np


SLOT_PHRASES = {"anel": "Reequipar anel.", "colar": "Reequipar colar."}


class SlotTransition:
    """Require three consecutive observations, never treat unknown as empty."""
    def __init__(self):
        self.armed = False
        self.pending = None
        self.count = 0

    def observe(self, state):
        if state == "unknown":
            self.pending, self.count = None, 0
            self.armed = False
            return False
        self.count = self.count + 1 if state == self.pending else 1
        self.pending = state
        if self.count < 3:
            return False
        if state == "occupied":
            self.armed = True
        elif state == "empty" and self.armed:
            self.armed = False
            return True
        return False


@dataclass
class SlotReference:
    name: str
    image: np.ndarray
    box: tuple[int, int, int, int]

    @classmethod
    def capture(cls, name, frame, box):
        x, y, w, h = box
        if name not in SLOT_PHRASES or not (20 <= w <= 120 and 20 <= h <= 120 and .8 <= w / h <= 1.25):
            raise ValueError("Marque um slot quadrado completo, entre 20 e 120 pixels.")
        margin = max(10, w // 2)
        left, top = max(0, x-margin), max(0, y-margin)
        right, bottom = min(frame.shape[1], x+w+margin), min(frame.shape[0], y+h+margin)
        if x < 0 or y < 0 or x+w > frame.shape[1] or y+h > frame.shape[0]:
            raise ValueError("Slot fora da captura.")
        image = frame[top:bottom, left:right].copy()
        if image.std() < 5:
            raise ValueError("Referência sem detalhes suficientes. Marque o slot com sua borda.")
        return cls(name, image, (x-left, y-top, w, h))


class SlotMatcher:
    def __init__(self, reference):
        self.reference = reference
        self.position = None
        self.next_search = 0
        self.variants = []
        for scale in (.75, 1., 1.25, 1.5):
            image = cv2.resize(reference.image, None, fx=scale, fy=scale)
            box = tuple(round(v*scale) for v in reference.box)
            x, y, w, h = box
            mask = np.ones(image.shape, np.uint8)
            inset = max(2, round(3*scale))
            mask[y+inset:y+h-inset, x+inset:x+w-inset] = 0
            self.variants.append((image, mask, box, inset))

    def _locate(self, frame):
        candidates = []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        for index, (image, mask, _, _) in enumerate(self.variants):
            h, w = image.shape[:2]
            if h > frame.shape[0] or w > frame.shape[1]:
                continue
            scores = cv2.matchTemplate(gray, cv2.cvtColor(image, cv2.COLOR_BGR2GRAY),
                                       cv2.TM_SQDIFF, mask=mask[:, :, 0])
            scores = np.nan_to_num(scores / (float(mask[:, :, 0].sum()) * 255**2), nan=1, posinf=1, neginf=1)
            best, _, point, _ = cv2.minMaxLoc(scores)
            px, py = point
            scores[max(0,py-h//2):py+h//2+1, max(0,px-w//2):px+w//2+1] = 1
            second = float(scores.min())
            if best < .0025 and second - best > .001:
                candidates.append((best, index, px, py))
        if not candidates:
            return None
        candidates.sort()
        best = candidates[0]
        # Different scales may agree, but different locations must not compete.
        if any(abs(c[2]-best[2]) > 30 or abs(c[3]-best[3]) > 30 for c in candidates[1:]):
            return None
        return best[1:]

    def inspect(self, frame, now):
        if self.position is None and now >= self.next_search:
            started = time.perf_counter()
            self.position = self._locate(frame)
            self.next_search = now + (time.perf_counter()-started) + 5
        if self.position is None:
            return "unknown", None
        index, px, py = self.position
        image, mask, (x, y, w, h), inset = self.variants[index]
        crop = frame[py:py+image.shape[0], px:px+image.shape[1]]
        if crop.shape != image.shape:
            self.position = None
            return "unknown", None
        diff = np.abs(crop.astype(np.float32)-image.astype(np.float32))
        if float(np.mean(diff[mask != 0] ** 2)) > .0025 * 255**2:
            self.position = None
            return "unknown", None
        inside = diff[y+inset:y+h-inset, x+inset:x+w-inset]
        error = float(inside.mean())
        state = "empty" if error < 5 else "occupied" if error > 12 else "unknown"
        return state, (px+x, py+y, w, h)


class EquipmentTracker:
    def __init__(self, references):
        self.matchers = {r.name: SlotMatcher(r) for r in references}
        self.states = {name: SlotTransition() for name in self.matchers}

    def inspect(self, frame, now):
        observations, events, boxes = {}, [], []
        for name, matcher in self.matchers.items():
            state, box = matcher.inspect(frame, now)
            observations[name] = state
            if box:
                boxes.append(box)
            if self.states[name].observe(state):
                events.append(name)
        return observations, events, boxes
