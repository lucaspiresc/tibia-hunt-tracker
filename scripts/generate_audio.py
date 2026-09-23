from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tibia_hunt_tracker.alerts import generate_audio_files, phrases_for_config  # noqa: E402
from tibia_hunt_tracker.catalog import load_catalog  # noqa: E402
from tibia_hunt_tracker.models import TimerConfig  # noqa: E402


def main() -> None:
    phrases: list[str] = ["Reequipar anel.", "Reequipar colar."]
    for entry in load_catalog(ROOT / "data" / "tracker_catalog.json"):
        if entry.entity_type != "spell":
            continue
        config = TimerConfig(
            catalog_id=entry.id,
            name=entry.name,
            voice_label=entry.voice_label,
            duration_seconds=entry.duration_seconds,
            warning_seconds=entry.default_warning_seconds,
        )
        phrases.extend(phrases_for_config(config))

    output_dir = ROOT / "data" / "audio"
    files = generate_audio_files(phrases, output_dir)
    print(f"Áudios prontos: {len(files)} em {output_dir}")


if __name__ == "__main__":
    main()
