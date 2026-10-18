"""Small JSON settings file in the app data folder. A damaged file never stops the app from starting."""
import json

from . import paths

DEFAULTS = {"folders": [], "output": "", "low": 0.30, "high": 0.50, "last_run": None,
            "theme": "dark", "lang": "zh", "thumb": 200}
CHOICES = {"theme": ("dark", "light"), "lang": ("zh", "en")}
THUMB_RANGE = (120, 320)


def _clean(data):
    """Defaults for anything missing or of the wrong type."""
    cfg = dict(DEFAULTS)
    if not isinstance(data, dict):
        return cfg
    if isinstance(data.get("folders"), list):
        cfg["folders"] = [f for f in data["folders"] if isinstance(f, str) and f]
    if isinstance(data.get("output"), str):
        cfg["output"] = data["output"]
    if isinstance(data.get("last_run"), int) and not isinstance(data.get("last_run"), bool):
        cfg["last_run"] = data["last_run"]
    for key in ("low", "high"):
        v = data.get(key)
        if isinstance(v, (int, float)) and not isinstance(v, bool) and 0.01 <= float(v) <= 0.99:
            cfg[key] = float(v)
    for key, allowed in CHOICES.items():
        if data.get(key) in allowed:
            cfg[key] = data[key]
    t = data.get("thumb")
    if isinstance(t, int) and not isinstance(t, bool) and THUMB_RANGE[0] <= t <= THUMB_RANGE[1]:
        cfg["thumb"] = t
    return cfg


def load():
    try:
        with open(paths.app_home() / "settings.json", encoding="utf-8") as f:
            return _clean(json.load(f))
    except (OSError, ValueError):
        return dict(DEFAULTS)


def save(data):
    home = paths.app_home()
    home.mkdir(parents=True, exist_ok=True)
    with open(home / "settings.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
