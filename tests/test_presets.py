import json
import tempfile
import unittest
from pathlib import Path

from tibia_hunt_tracker.models import TimerConfig
from tibia_hunt_tracker.presets import PresetStore


class PresetStoreTests(unittest.TestCase):
    def test_preset_round_trip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "presets.json"
            store = PresetStore(path)
            source = TimerConfig("item_sword_ring", "Sword Ring", "Sword Ring", 1800, 30, True)
            store.save("Solo", [source])
            reloaded = PresetStore(path)
            self.assertEqual(reloaded.names, ["Minha Hunt", "Solo"])
            self.assertEqual(reloaded.get("Solo")[0].to_dict(), source.to_dict())
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["schema_version"], 2)

    def test_old_voice_setting_is_migrated(self):
        config = TimerConfig.from_dict(
            {
                "catalog_id": "spell_recovery",
                "name": "Recovery",
                "voice_label": "utura",
                "duration_seconds": 60,
                "warning_seconds": 10,
                "voice_enabled": False,
                "notification_enabled": True,
            }
        )
        self.assertFalse(config.audio_enabled)
        self.assertNotIn("voice_enabled", config.to_dict())
        self.assertNotIn("notification_enabled", config.to_dict())

    def test_delete_last_preset_restores_default(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = PresetStore(Path(temp_dir) / "presets.json")
            store.delete("Minha Hunt")
            self.assertEqual(store.names, ["Minha Hunt"])


if __name__ == "__main__":
    unittest.main()
