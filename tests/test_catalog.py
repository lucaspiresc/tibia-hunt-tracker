import unittest

from tibia_hunt_tracker.catalog import load_catalog


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries = load_catalog()
        cls.by_name = {entry.name: entry for entry in cls.entries}

    def test_expected_entry_count_and_unique_ids(self):
        self.assertEqual(len(self.entries), 67)
        self.assertEqual(len({entry.id for entry in self.entries}), 67)

    def test_critical_durations(self):
        expected = {
            "Sword Ring": 1800,
            "Enchanted Werewolf Amulet": 3600,
            "Recovery": 60,
            "Intense Recovery": 60,
            "Magic Shield": 180,
        }
        for name, duration in expected.items():
            with self.subTest(name=name):
                self.assertEqual(self.by_name[name].duration_seconds, duration)

    def test_magic_shield_can_end_early(self):
        self.assertTrue(self.by_name["Magic Shield"].can_end_early)


if __name__ == "__main__":
    unittest.main()
