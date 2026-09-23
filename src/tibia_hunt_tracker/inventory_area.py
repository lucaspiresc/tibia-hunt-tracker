"""Persist coordinates only; never store the user's screen image."""
import json

from .presets import default_data_dir


def capture_area(monitor, box):
    x, y, width, height = (int(value) for value in box)
    if not (x >= 0 and y >= 0 and width >= 86 and height >= 122
            and x + width <= monitor["width"] and y + height <= monitor["height"]):
        raise ValueError("Selecione o inventário completo, incluindo suas bordas e botões.")
    return {"left": monitor["left"] + x, "top": monitor["top"] + y,
            "width": width, "height": height}


def load_area(monitor, path=None):
    path = path or default_data_dir() / "inventory-area.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data["monitor"] != monitor:
            return None
        capture_area(monitor, data["box"])
        return tuple(data["box"])
    except (OSError, ValueError, TypeError, KeyError):
        return None


def save_area(monitor, box, path=None):
    capture_area(monitor, box)
    path = path or default_data_dir() / "inventory-area.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps({"monitor": monitor, "box": box}), encoding="utf-8")
    temporary.replace(path)
