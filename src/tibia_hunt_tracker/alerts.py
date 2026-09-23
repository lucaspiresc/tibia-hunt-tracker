from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import platform
from pathlib import Path
from typing import Iterable

from .catalog import project_root
from .models import TimerConfig
from .presets import default_data_dir
from .timer_engine import EventKind, TimerEvent


def normalize_phrase(phrase: str) -> str:
    return " ".join(phrase.split()).casefold()


def phrase_filename(phrase: str) -> str:
    digest = hashlib.sha256(normalize_phrase(phrase).encode("utf-8")).hexdigest()[:24]
    return f"{digest}.wav"


def event_phrase(config: TimerConfig, kind: EventKind) -> str:
    label = " ".join(config.voice_label.split()) or config.name
    if kind is EventKind.WARNING:
        return f"{label}. Em {config.warning_seconds} segundos."
    return f"{label}."


def phrases_for_config(config: TimerConfig) -> tuple[str, ...]:
    if not config.audio_enabled:
        return ()
    phrases = [event_phrase(config, EventKind.EXPIRED)]
    if config.warning_seconds > 0:
        phrases.append(event_phrase(config, EventKind.WARNING))
    return tuple(phrases)


def _voice_description(voice: object) -> str:
    parts: list[str] = []
    for attribute in ("name", "id", "languages"):
        value = getattr(voice, attribute, "")
        if isinstance(value, (list, tuple)):
            parts.extend(str(item) for item in value)
        else:
            parts.append(str(value))
    return " ".join(parts).casefold()


def _select_portuguese_voice(engine: object) -> None:
    preferred_tokens = ("pt-br", "pt_br", "brazil", "brasil", "portuguese", "português")
    try:
        voices = engine.getProperty("voices")
        match = next(
            (voice for voice in voices if any(token in _voice_description(voice) for token in preferred_tokens)),
            None,
        )
        if match is not None:
            engine.setProperty("voice", match.id)
        engine.setProperty("rate", 165)
    except Exception:
        pass


def generate_audio_files(phrases: Iterable[str], output_dir: Path) -> list[Path]:
    unique_phrases = list(dict.fromkeys(" ".join(phrase.split()) for phrase in phrases if phrase.strip()))
    output_dir.mkdir(parents=True, exist_ok=True)
    pending = []
    for phrase in unique_phrases:
        path = output_dir / phrase_filename(phrase)
        if not path.exists() or path.stat().st_size == 0:
            pending.append(phrase)
    if not pending:
        return [output_dir / phrase_filename(phrase) for phrase in unique_phrases]

    import pyttsx3

    engine = pyttsx3.init()
    _select_portuguese_voice(engine)
    for phrase in pending:
        engine.save_to_file(phrase, str(output_dir / phrase_filename(phrase)))
    engine.runAndWait()
    engine.stop()

    generated = [output_dir / phrase_filename(phrase) for phrase in unique_phrases]
    missing = [path for path in generated if not path.exists() or path.stat().st_size == 0]
    if missing:
        raise RuntimeError(f"Não foi possível gerar {len(missing)} arquivo(s) de áudio.")
    return generated


class AlertDispatcher:
    def __init__(self, bundled_dir: Path | None = None, cache_dir: Path | None = None) -> None:
        self.bundled_dir = bundled_dir or project_root() / "data" / "audio"
        self.cache_dir = cache_dir or default_data_dir() / "audio"
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="audio-alerts")

    def prepare(self, configs: Iterable[TimerConfig]) -> None:
        phrases = [phrase for config in configs for phrase in phrases_for_config(config)]
        if phrases:
            self._executor.submit(self._ensure_phrases, phrases)

    def dispatch(self, event: TimerEvent) -> None:
        if event.config.audio_enabled:
            self._executor.submit(self._deliver, event)

    def close(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)

    def _find_audio(self, phrase: str) -> Path | None:
        filename = phrase_filename(phrase)
        for directory in (self.bundled_dir, self.cache_dir):
            candidate = directory / filename
            if candidate.exists() and candidate.stat().st_size > 0:
                return candidate
        return None

    def _ensure_phrases(self, phrases: Iterable[str]) -> None:
        missing = [phrase for phrase in phrases if self._find_audio(phrase) is None]
        if not missing:
            return
        try:
            generate_audio_files(missing, self.cache_dir)
        except Exception:
            pass

    def _deliver(self, event: TimerEvent) -> None:
        phrase = event_phrase(event.config, event.kind)
        self._deliver_phrase(phrase)

    def _deliver_phrase(self, phrase: str) -> None:
        audio_path = self._find_audio(phrase)
        if audio_path is None:
            self._ensure_phrases([phrase])
            audio_path = self._find_audio(phrase)

        if audio_path is not None and platform.system() == "Windows":
            try:
                import winsound

                winsound.PlaySound(str(audio_path), winsound.SND_FILENAME | winsound.SND_NODEFAULT)
                return
            except Exception:
                pass

        try:
            import pyttsx3

            engine = pyttsx3.init()
            _select_portuguese_voice(engine)
            engine.say(phrase)
            engine.runAndWait()
            engine.stop()
        except Exception:
            if platform.system() == "Windows":
                try:
                    import winsound

                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                except Exception:
                    pass
