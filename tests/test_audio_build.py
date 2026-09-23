import runpy
import unittest
from pathlib import Path
from unittest.mock import patch

from tibia_hunt_tracker.alerts import event_phrase
from tibia_hunt_tracker.catalog import load_catalog
from tibia_hunt_tracker.models import TimerConfig
from tibia_hunt_tracker.timer_engine import EventKind


class AudioBuildTests(unittest.TestCase):
    def test_build_includes_spoken_alerts_for_items_and_spells(self):
        script = Path(__file__).resolve().parents[1] / "scripts" / "generate_audio.py"
        with patch("tibia_hunt_tracker.alerts.generate_audio_files", return_value=[]) as generate:
            with patch("builtins.print"):
                runpy.run_path(str(script), run_name="__main__")

        phrases, output_dir = generate.call_args.args
        self.assertEqual(output_dir.name, "audio")
        entries = load_catalog()
        self.assertTrue(any(entry.item_category == "ring" for entry in entries))
        self.assertTrue(any(entry.entity_type == "spell" for entry in entries))
        for entry in entries:
            config = TimerConfig(entry.id, entry.name, entry.voice_label,
                                 entry.duration_seconds, entry.default_warning_seconds)
            with self.subTest(entry=entry.name):
                self.assertIn(event_phrase(config, EventKind.EXPIRED), phrases)
                if config.warning_seconds:
                    self.assertIn(event_phrase(config, EventKind.WARNING), phrases)


if __name__ == "__main__":
    unittest.main()
