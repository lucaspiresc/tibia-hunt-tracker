"""Automatic inventory recognition from an official manual image, pixels only."""
import time

import cv2
import numpy as np

from .catalog import project_root

SLOT_PHRASES = {"anel": "Reequipar anel.", "colar": "Reequipar colar."}
SLOTS = {"colar": (3, 16, 35, 35), "anel": (3, 88, 35, 35)}
BODY_SLOTS = [(3, y, 35, 35) for y in (16, 52, 88)] + [
    (40, y, 35, 35) for y in (2, 38, 74, 110)] + [
    (77, y, 35, 35) for y in (16, 52, 88)]


class SlotTransition:
    def __init__(self):
        self.armed = False
        self.pending = None
        self.count = 0

    def observe(self, state):
        if state == "unknown":
            self.pending, self.count, self.armed = None, 0, False
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


class InventoryMatcher:
    """Locate stable controls and slot borders, ignoring every equipped item."""
    def __init__(self):
        image = cv2.imread(str(project_root() / "data" / "inventory-reference.jpg"))
        if image is None:
            raise RuntimeError("Referência visual do inventário ausente. Reinstale o app.")
        mask = np.ones(image.shape[:2], np.uint8)
        for x, y, w, h in BODY_SLOTS:
            mask[y+3:y+h-3, x+3:x+w-3] = 0
        mask[123:, :40] = 0  # Soul value varies.
        mask[123:, 75:] = 0  # Capacity value varies.
        mask[145:] = 0      # Conditions vary.
        self.variants = []
        for scale in (.75, 1., 1.25, 1.5, 1.75, 2.):
            resized = cv2.resize(image, None, fx=scale, fy=scale)
            masked = cv2.resize(mask, (resized.shape[1], resized.shape[0]), interpolation=cv2.INTER_NEAREST)
            self.variants.append((resized, masked, scale))
        self.position = None
        self.next_search = 0

    def _valid(self, crop, index):
        image, mask, scale = self.variants[index]
        if crop.shape != image.shape:
            return False
        diff = np.abs(crop.astype(np.float32) - image.astype(np.float32))
        if float(np.mean(diff[mask != 0] ** 2)) > 100:
            return False
        # Both controls must agree; plain gray boxes are not an inventory.
        for x, y, w, h in ((3, 2, 27, 12), (77, 2, 35, 12)):
            x, y, w, h = (round(v*scale) for v in (x, y, w, h))
            if float(diff[y:y+h, x:x+w].mean()) > 10:
                return False
        return True

    def _locate(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        found = []
        for index, (image, mask, _) in enumerate(self.variants):
            h, w = image.shape[:2]
            if h > frame.shape[0] or w > frame.shape[1]:
                continue
            scores = cv2.matchTemplate(gray, cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), cv2.TM_SQDIFF, mask=mask)
            scores = np.nan_to_num(scores / float(mask.sum()), nan=1e9, posinf=1e9, neginf=1e9)
            # Inspect up to two separate candidates to reject multiple inventories.
            for _ in range(2):
                score, _, (x, y), _ = cv2.minMaxLoc(scores)
                if score > 100:
                    break
                crop = frame[y:y+h, x:x+w]
                if self._valid(crop, index):
                    found.append((score, index, x, y))
                scores[max(0,y-h//2):y+h//2+1, max(0,x-w//2):x+w//2+1] = 1e9
        if not found:
            return None
        found.sort()
        best = found[0]
        if any(abs(v[2]-best[2]) > 20 or abs(v[3]-best[3]) > 20 for v in found[1:]):
            return None
        return best[1:]

    def inspect(self, frame, now):
        unknown = {name: "unknown" for name in SLOTS}
        if frame.size == 0 or frame.max() < 8:
            self.position = None
            return unknown, []
        if self.position is None and now >= self.next_search:
            started = time.perf_counter()
            self.position = self._locate(frame)
            self.next_search = now + time.perf_counter()-started + 5
        if self.position is None:
            return unknown, []
        index, px, py = self.position
        image, _, scale = self.variants[index]
        crop = frame[py:py+image.shape[0], px:px+image.shape[1]]
        if not self._valid(crop, index):
            self.position = None
            return unknown, []
        observations, boxes = {}, []
        for name, box in SLOTS.items():
            x, y, w, h = (round(v*scale) for v in box)
            inset = max(2, round(3*scale))
            actual = crop[y+inset:y+h-inset, x+inset:x+w-inset].astype(np.float32)
            empty = image[y+inset:y+h-inset, x+inset:x+w-inset].astype(np.float32)
            diff = np.abs(actual-empty)
            error = float(diff.mean())
            changed = float(np.mean(diff.max(axis=2) > 20))
            observations[name] = "empty" if error < 5 else "occupied" if error > 10 and changed > .15 else "unknown"
            boxes.append((px+x, py+y, w, h))
        return observations, boxes


class EquipmentTracker:
    def __init__(self):
        self.matcher = InventoryMatcher()
        self.states = {name: SlotTransition() for name in SLOTS}

    def inspect(self, frame, now):
        observations, boxes = self.matcher.inspect(frame, now)
        events = [name for name, state in observations.items() if self.states[name].observe(state)]
        return observations, events, boxes
