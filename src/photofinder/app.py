"""Entry point: one window at a time (single-instance lock). `--selftest` checks the engine without any window."""
import os
import sys
from pathlib import Path

from . import APP_NAME, __version__, paths
from .i18n import tr

APP_ID = "PhotoFinderPro.App"


def asset_path(name):
    """Bundled asset file (works from source and inside a PyInstaller bundle)."""
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "photofinder" / "assets"
    else:
        base = Path(__file__).parent / "assets"
    return base / name


def selftest():
    """Headless check: models load, face detection runs, HEIC support present. Returns 0 on success."""
    lines, ok = [f"{APP_NAME} {__version__} selftest", f"frozen: {bool(getattr(sys, 'frozen', False))}"], True
    try:
        import numpy as np
        from . import imageio
        from .engine import FaceEngine
        mdir = paths.model_dir()
        lines.append(f"model_dir: {mdir}")
        engine = FaceEngine()
        lines.append("models loaded: yes (yunet + sface)")
        img = np.random.default_rng(0).integers(90, 170, (480, 640, 3), dtype=np.uint8)
        lines.append(f"faces() on synthetic 640x480 noise: {len(engine.faces(img))} faces (ran without error)")
        import pi_heif
        heic = ".heic" in imageio.SUPPORTED_EXTS
        lines.append(f"pi_heif {pi_heif.__version__}: .heic supported: {heic}")
        from . import ui  # a Qt module left out of the bundle only fails here, not in the engine checks above
        lines.append(f"ui imports: yes ({ui.__name__})")
        ok = heic
    except Exception as e:  # report any failure
        ok = False
        lines.append(f"ERROR: {type(e).__name__}: {e}")
    lines.append("RESULT: " + ("OK" if ok else "FAIL"))
    text = "\n".join(lines)
    try:
        print(text)
    except Exception:  # windowed exe has no stdout
        pass
    try:
        tmp = os.environ.get("TEMP") or os.environ.get("TMP") or str(Path.home())
        (Path(tmp) / "photofinderpro_selftest.txt").write_text(text + "\n", encoding="utf-8")
    except OSError:
        pass
    return 0 if ok else 1


def _set_app_id():
    """Windows: own taskbar identity so the taskbar shows our icon, not python's."""
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except Exception:
        pass


def main():
    if "--selftest" in sys.argv:
        return selftest()
    from PySide6.QtGui import QFont, QIcon
    from PySide6.QtWidgets import QApplication, QMessageBox
    from .lock import SingleInstance
    _set_app_id()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setOrganizationName(APP_NAME)
    app.setWindowIcon(QIcon(str(asset_path("app.ico"))))
    app.setFont(QFont("Microsoft YaHei UI", 10))
    lock = SingleInstance(paths.app_home() / "app.lock")
    if not lock.acquire():
        QMessageBox.warning(None, APP_NAME, tr("Photo Finder Pro 已經開咗一個視窗。一次只可以開一個。"))
        return 1
    try:
        from .ui import MainWindow
        win = MainWindow()
        win.show()
        return app.exec()
    finally:
        lock.release()


if __name__ == "__main__":
    sys.exit(main())
