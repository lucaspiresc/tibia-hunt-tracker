import tempfile
import unittest
from pathlib import Path

from tibia_hunt_tracker.inventory_area import capture_area, load_area, save_area


class InventoryAreaTests(unittest.TestCase):
    def setUp(self):
        self.monitor = {"left": -1920, "top": 0, "width": 1920, "height": 1080}

    def test_capture_uses_selected_region_on_negative_offset_monitor(self):
        self.assertEqual(capture_area(self.monitor, (100, 200, 160, 220)),
                         {"left": -1820, "top": 200, "width": 160, "height": 220})

    def test_persist_coordinates_and_invalidate_changed_monitor(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "selection.json"
            box = (100, 200, 160, 220)
            save_area(self.monitor, box, path)
            self.assertEqual(load_area(self.monitor, path), box)
            self.assertIsNone(load_area(dict(self.monitor, width=1280), path))
            self.assertIsNone(load_area(dict(self.monitor, left=0), path))

    def test_invalid_and_out_of_bounds_regions_are_rejected(self):
        for box in ((0, 0, 0, 0), (-1, 0, 160, 220), (1800, 900, 160, 220)):
            with self.subTest(box=box), self.assertRaises(ValueError):
                capture_area(self.monitor, box)

    def test_corrupt_saved_selection_is_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "selection.json"
            path.write_text("not json")
            self.assertIsNone(load_area(self.monitor, path))
