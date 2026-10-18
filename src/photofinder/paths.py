"""Where the app keeps its files. Nothing here touches the user's photos."""
import os
import sys
from pathlib import Path


def app_home():
    """Per-user data folder (database, thumbnails, reference data). PHOTOFINDER_HOME overrides it (tests)."""
    env = os.environ.get("PHOTOFINDER_HOME")
    if env:
        return Path(env)
    base = os.environ.get("LOCALAPPDATA") or str(Path.home())
    return Path(base) / "PhotoFinderPro"


def model_dir():
    """Folder holding yunet.onnx and sface.onnx (inside the bundle when frozen by PyInstaller)."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "models"
    return Path(__file__).resolve().parents[2] / "models"


def db_path():
    return app_home() / "photos.db"


def thumb_dir():
    return app_home() / "thumbs"


def run_dir(run_id):
    """App data folder of one search (its reference-face snapshot). The results folder is elsewhere."""
    return app_home() / "runs" / str(run_id)


def default_output_dir():
    return app_home() / "output"
