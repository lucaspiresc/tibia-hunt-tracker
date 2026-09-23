import unittest
from unittest.mock import Mock, patch

import cv2
import numpy as np

from tibia_hunt_tracker.catalog import project_root
from tibia_hunt_tracker.equipment import EquipmentTracker, InventoryMatcher, SlotTransition, SLOTS, BODY_SLOTS
from tibia_hunt_tracker.alerts import AlertDispatcher
from tibia_hunt_tracker.screen_reader import ScreenReader


def scene(occupied=(), scale=1, offset=(60, 50), all_items=False):
    image = cv2.imread(str(project_root() / "data" / "inventory-reference.jpg"))
    boxes = BODY_SLOTS if all_items else [SLOTS[name] for name in occupied]
    for x, y, w, h in boxes:
        cv2.circle(image, (x+w//2, y+h//2), 10, (30, 190, 230), -1)
    image = cv2.resize(image, None, fx=scale, fy=scale)
    frame = np.full((480, 700, 3), 25, np.uint8)
    x, y = offset
    frame[y:y+image.shape[0], x:x+image.shape[1]] = image
    return frame


class EquipmentTests(unittest.TestCase):
    def test_debounce_single_alert_and_rearm(self):
        tracker = SlotTransition()
        for state in ["empty"]*4 + ["occupied"]*3 + ["empty"]*2:
            self.assertFalse(tracker.observe(state))
        self.assertTrue(tracker.observe("empty"))
        for _ in range(10):
            self.assertFalse(tracker.observe("empty"))
        for _ in range(3):
            tracker.observe("occupied")
        self.assertEqual([tracker.observe("empty") for _ in range(3)], [False, False, True])

    def test_unknown_breaks_evidence_and_disarms(self):
        tracker = SlotTransition()
        for state in ["occupied"]*3 + ["empty"]*2 + ["unknown"] + ["empty"]*5:
            self.assertFalse(tracker.observe(state))

    def test_locates_already_equipped_inventory_at_multiple_scales(self):
        for scale in (.75, 1, 1.25, 1.5, 1.75, 2):
            with self.subTest(scale=scale):
                states, boxes = InventoryMatcher().inspect(scene(scale=scale, all_items=True, offset=(200, 40)), 0)
                self.assertEqual(states, {"anel": "occupied", "colar": "occupied"})
                self.assertEqual(len(boxes), 2)

    def test_official_empty_slots_are_empty(self):
        self.assertEqual(InventoryMatcher().inspect(scene(), 0)[0], {"anel": "empty", "colar": "empty"})

    def test_independent_slots_and_no_repeat(self):
        tracker = EquipmentTracker()
        events = []
        frames = [scene(("anel", "colar"))]*3 + [scene(("colar",))]*4 + [scene()]*6
        for i, frame in enumerate(frames):
            events.extend(tracker.inspect(frame, i*.2)[1])
        self.assertEqual(events, ["anel", "colar"])

    def test_occlusion_and_duplicate_inventory_are_unknown(self):
        matcher = InventoryMatcher()
        self.assertEqual(matcher.inspect(scene(("anel",)), 0)[0]["anel"], "occupied")
        self.assertEqual(matcher.inspect(np.zeros((480,700,3),np.uint8), .2)[0]["anel"], "unknown")
        duplicated = np.concatenate((scene(), scene()), axis=1)
        self.assertEqual(InventoryMatcher().inspect(duplicated, 0)[0]["anel"], "unknown")

    def test_reacquires_moved_inventory_without_false_expiry(self):
        tracker = EquipmentTracker()
        for i in range(3):
            tracker.inspect(scene(("anel",)), i*.2)
        self.assertFalse(tracker.inspect(scene(offset=(300, 40)), 1)[1])
        self.assertFalse(tracker.inspect(scene(offset=(300, 40)), 10)[1])
        self.assertEqual(tracker.inspect(scene(offset=(300, 40)), 10.2)[0]["anel"], "empty")

    def test_gray_desktop_and_hidden_controls_do_not_match(self):
        frame = scene()
        frame[50:65, 60:175] = 25
        self.assertEqual(InventoryMatcher().inspect(frame, 0)[0]["anel"], "unknown")
        self.assertEqual(InventoryMatcher().inspect(np.full_like(frame, 40), 0)[0]["anel"], "unknown")

    def test_capture_to_audio_event_survives_result_replacement(self):
        reader = ScreenReader({})
        frames = iter([scene(("anel",))]*3 + [scene()]*3)
        count = 0
        def grab(_):
            nonlocal count
            count += 1
            if count == 6:
                reader.stop()
            return next(frames)
        with patch("mss.mss") as capture, patch.object(reader._stop, "wait"):
            capture.return_value.__enter__.return_value.grab.side_effect = grab
            reader._run()
        self.assertEqual(reader.events.get_nowait(), "anel")
        self.assertTrue(reader.events.empty())
        self.assertIn("vazio", reader.poll().status)

    def test_equipment_dispatch_uses_spoken_phrase(self):
        dispatcher = AlertDispatcher()
        dispatcher._deliver_phrase = Mock()
        dispatcher.equipment_empty("anel")
        dispatcher._executor.shutdown(wait=True)
        dispatcher._deliver_phrase.assert_called_once_with("Reequipar anel.")
