import unittest
from unittest.mock import patch

import cv2
import numpy as np

from tibia_hunt_tracker.screen_reader import ScreenReader, ScreenResult, VisualTracker, locate_candidates


def scene(x=80, y=90, size=32, vertical=False):
    image = np.full((600, 1000, 3), 35, dtype=np.uint8)
    for i in range(6):
        left = x if vertical else x + i * (size + 4)
        top = y + i * (size + 4) if vertical else y
        cv2.rectangle(image, (left, top), (left+size, top+size), (190, 190, 190), 2)
    return image


class ScreenReaderTests(unittest.TestCase):
    def test_translated_scaled_and_vertical_grids(self):
        for size in (24, 32, 48, 64):
            for vertical in (False, True):
                with self.subTest(size=size, vertical=vertical):
                    regions = locate_candidates(scene(320, 100, size, vertical))
                    self.assertTrue(regions)
                    self.assertLess(abs(regions[0].x - 320), 5)
                    self.assertLess(abs(regions[0].y - 100), 5)

    def test_blank_frames_never_confirm(self):
        tracker = VisualTracker()
        for now in (0, 1, 2):
            self.assertIn("Sem leitura", tracker.inspect(np.zeros((300, 400, 3), np.uint8), now))
            self.assertEqual(tracker.regions, [])

    def test_requires_repeated_evidence_and_reacquires_after_move(self):
        tracker = VisualTracker()
        tracker.inspect(scene(), 0)
        self.assertFalse(tracker.regions)
        tracker.inspect(scene(), 1.1)
        self.assertTrue(tracker.regions)
        tracker.inspect(scene(400, 300), 1.3)
        self.assertFalse(tracker.regions)
        tracker.inspect(scene(400, 300), 2.4)
        self.assertTrue(tracker.regions)
        self.assertGreater(tracker.regions[0].x, 390)

    def test_occlusion_discards_regions_without_timer_events(self):
        tracker = VisualTracker()
        tracker.inspect(scene(), 0)
        tracker.inspect(scene(), 1.1)
        tracker.inspect(np.full((600, 1000, 3), 35, np.uint8), 1.3)
        self.assertEqual(tracker.regions, [])

    def test_latest_result_replaces_old_frame(self):
        reader = ScreenReader({})
        reader._publish(ScreenResult("old"))
        reader._publish(ScreenResult("new"))
        self.assertEqual(reader.poll().status, "new")
        self.assertIsNone(reader.poll())

    def test_capture_error_is_reported(self):
        reader = ScreenReader({})
        with patch("mss.mss", side_effect=RuntimeError("monitor unavailable")):
            reader._run()
        self.assertIn("monitor unavailable", reader.poll().status)
