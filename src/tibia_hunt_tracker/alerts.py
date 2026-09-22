from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import platform

from .timer_engine import EventKind, TimerEvent


class AlertDispatcher:
    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="alerts")

    def dispatch(self, event: TimerEvent) -> None:
        self._executor.submit(self._deliver, event)

    def close(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)

    @staticmethod
    def _deliver(event: TimerEvent) -> None:
        config = event.config
        if event.kind is EventKind.WARNING:
            title = f"{config.name} em {config.warning_seconds}s"
            spoken = f"{config.voice_label} em {config.warning_seconds} segundos"
            message = "Prepare-se para renovar."
        else:
            title = config.name
            spoken = config.voice_label
            message = "Renove agora. O timer foi reiniciado."

        delivered = False
        requested = config.notification_enabled or config.voice_enabled
        if config.notification_enabled and platform.system() == "Windows":
            try:
                from winotify import Notification

                Notification(app_id="Tibia Hunt Tracker", title=title, msg=message).show()
                delivered = True
            except Exception:
                pass

        if config.voice_enabled:
            try:
                import pyttsx3

                engine = pyttsx3.init()
                engine.say(spoken)
                engine.runAndWait()
                delivered = True
            except Exception:
                pass

        if requested and not delivered and platform.system() == "Windows":
            try:
                import winsound

                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            except Exception:
                pass
