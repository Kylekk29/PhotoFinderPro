"""Headless UI smoke test: builds the window, scans a synthetic folder in the worker thread, checks results.

Uses the Qt 'offscreen' platform, a fake engine and solid-colour images. No real faces, no personal photos.
"""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication

from conftest import FakeEngine, REF, snap


def _wait(app, cond, ms=15000):
    import time
    end = time.time() + ms / 1000
    while time.time() < end and not cond():
        app.processEvents()
        time.sleep(0.01)
    return cond()


def test_window_scan_end_to_end(tmp_path, make_photo, home):
    from photofinder import ui
    app = QApplication.instance() or QApplication([])
    photos = [make_photo("trip", "a.png", 5), make_photo("trip", "b.png", 6), make_photo("trip", "c.png", 7)]
    before = {p: snap(p) for p in photos}
    win = ui.MainWindow()
    win._engine = FakeEngine()
    win.refs, win.ref_paths = np.vstack([REF]), ["ref.png"]
    win._add_folder_item(str(tmp_path / "trip"))
    win.out_edit.setText(str(tmp_path / "found"))
    win.start_scan()
    assert _wait(app, lambda: win.worker is not None and win.worker.isFinished())
    app.processEvents()
    assert len(win.grid_ok.items) == 1 and len(win.grid_maybe.items) == 1
    run_dir = tmp_path / "found" / os.path.basename(win.run["run_dir"])   # each search gets its own folder
    assert (run_dir / "confirmed" / "trip" / "a.png").exists()
    assert {p: snap(p) for p in photos} == before
    win.close()


def test_scan_refuses_output_inside_photo_folder(tmp_path, make_photo, home, monkeypatch):
    from photofinder import ui
    app = QApplication.instance() or QApplication([])
    make_photo("trip", "a.png", 5)
    shown = []
    monkeypatch.setattr(ui.QMessageBox, "critical", lambda *a, **k: shown.append(a[2]))
    win = ui.MainWindow()
    win._engine = FakeEngine()
    win.refs = np.vstack([REF])
    win._add_folder_item(str(tmp_path / "trip"))
    win.out_edit.setText(str(tmp_path / "trip" / "found"))
    win.start_scan()
    assert shown and "inside a scanned folder" in shown[0]
    assert not (tmp_path / "trip" / "found").exists()
    win.close()
