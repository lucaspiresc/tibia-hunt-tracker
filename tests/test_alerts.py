import unittest

from tibia_hunt_tracker.alerts import event_phrase, phrase_filename, phrases_for_config
from tibia_hunt_tracker.models import TimerConfig
from tibia_hunt_tracker.timer_engine import EventKind


def config(**changes):
    values = {
        "catalog_id": "spell_recovery",
        "name": "Recovery",
        "voice_label": "utura",
        "duration_seconds": 60,
        "warning_seconds": 10,
        "audio_enabled": True,
    }
    values.update(changes)
    return TimerConfig(**values)


class AlertTests(unittest.TestCase):
    def test_spoken_phrases(self):
        self.assertEqual(event_phrase(config(), EventKind.WARNING), "utura. Em 10 segundos.")
        self.assertEqual(event_phrase(config(), EventKind.EXPIRED), "utura.")

    def test_phrase_filename_is_normalized_and_stable(self):
        self.assertEqual(phrase_filename("  Utura.   Em 10 segundos. "), phrase_filename("utura. em 10 segundos."))
        self.assertTrue(phrase_filename("utura.").endswith(".wav"))

    def test_disabled_audio_has_no_phrases(self):
        self.assertEqual(phrases_for_config(config(audio_enabled=False)), ())

    def test_zero_warning_only_generates_expiry_phrase(self):
        self.assertEqual(phrases_for_config(config(warning_seconds=0)), ("utura.",))


if __name__ == "__main__":
    unittest.main()
