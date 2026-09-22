import unittest

from tibia_hunt_tracker.models import TimerConfig
from tibia_hunt_tracker.timer_engine import EventKind, TimerEngine


def config(duration=60, warning=10):
    return TimerConfig(
        catalog_id="spell_recovery",
        name="Recovery",
        voice_label="utura",
        duration_seconds=duration,
        warning_seconds=warning,
    )


class TimerEngineTests(unittest.TestCase):
    def test_warning_fires_once_per_cycle(self):
        engine = TimerEngine()
        engine.start([config()], now=100.0)
        self.assertEqual(engine.tick(now=149.9), [])
        self.assertEqual([event.kind for event in engine.tick(now=150.0)], [EventKind.WARNING])
        self.assertEqual(engine.tick(now=155.0), [])

    def test_expiry_restarts_cycle_and_rearms_warning(self):
        engine = TimerEngine()
        engine.start([config()], now=100.0)
        engine.tick(now=150.0)
        self.assertEqual([event.kind for event in engine.tick(now=160.0)], [EventKind.EXPIRED])
        self.assertEqual(engine.remaining("spell_recovery", now=160.0), 60)
        self.assertEqual([event.kind for event in engine.tick(now=210.0)], [EventKind.WARNING])

    def test_manual_reset_discards_current_warning_state(self):
        engine = TimerEngine()
        engine.start([config()], now=100.0)
        engine.tick(now=150.0)
        engine.reset("spell_recovery", now=155.0)
        self.assertEqual(engine.remaining("spell_recovery", now=155.0), 60)
        self.assertEqual([event.kind for event in engine.tick(now=205.0)], [EventKind.WARNING])

    def test_tick_after_expiry_does_not_emit_late_warning(self):
        engine = TimerEngine()
        engine.start([config()], now=100.0)
        self.assertEqual([event.kind for event in engine.tick(now=165.0)], [EventKind.EXPIRED])


if __name__ == "__main__":
    unittest.main()
