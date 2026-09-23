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

            source = TimerConfig(
                "spell_recovery",
                "Recovery",
                "utura",
                60,
                10,
                True,
            )

            store.save("Solo", [source])
            reloaded = PresetStore(path)

            self.assertEqual(reloaded.names, ["Minha Hunt", "Solo"])
            self.assertEqual(
                reloaded.get("Solo")[0].to_dict(),
                source.to_dict(),
            )
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8"))["schema_version"],
                4,
            )

    def test_items_and_spells_are_saved_as_manual_timers(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "presets.json"
            store = PresetStore(path)

            ring = TimerConfig(
                "item_sword_ring",
                "Sword Ring",
                "Sword Ring",
                1800,
                30,
                True,
            )

            amulet = TimerConfig(
                "item_enchanted_werewolf_amulet",
                "Enchanted Werewolf Amulet",
                "Colar",
                3600,
                20,
                False,
            )
            spell = TimerConfig("spell_recovery", "Recovery", "utura", 60, 10)
            configs = [ring, amulet, spell]
            store.save("Solo", configs)
            reloaded = PresetStore(path)
            self.assertEqual(
                [config.to_dict() for config in reloaded.get("Solo")],
                [config.to_dict() for config in configs],
            )
            reloaded.duplicate("Solo", "Cópia")
            self.assertEqual(reloaded.get("Cópia"), configs)

    def test_existing_presets_keep_items_spells_and_custom_settings(self):
        ring = TimerConfig("item_sword_ring", "Sword Ring", "Anel", 900, 15, False)
        spell = TimerConfig("spell_recovery", "Recovery", "utura", 60, 5)
        for version, configs in ((2, [ring, spell]), (3, [spell])):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as temp_dir:
                path = Path(temp_dir) / "presets.json"
                path.write_text(json.dumps({
                    "schema_version": version,
                    "presets": {"Solo": [config.to_dict() for config in configs]},
                }), encoding="utf-8")
                store = PresetStore(path)
                self.assertEqual(store.get("Solo"), configs)
                restored = store.get("Solo")
                if ring not in restored:
                    restored.append(ring)
                store.save("Solo", restored)
                self.assertEqual(PresetStore(path).get("Solo"), restored)

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
