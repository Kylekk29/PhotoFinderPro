"""QA bug hunt: each test asserts the CORRECT behaviour and fails today only if the bug is real.

Synthetic data only; PHOTOFINDER_HOME always points at a tmp_path (fixture `home`).
"""
import json
import os
import subprocess
import sys
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pytest
from PIL import Image

from conftest import FakeEngine, REF, snap


def _wait(app, cond, ms=15000):
    end = time.time() + ms / 1000
    while time.time() < end and not cond():
        app.processEvents()
        time.sleep(0.01)
    return cond()


# ---- scanner / index ---------------------------------------------------------------------------

def test_bug_junction_loop_lists_photos_repeatedly(tmp_path, home):
    """High: a directory junction pointing back at its parent must not make one photo appear many times."""
    from photofinder import scanner
    d = tmp_path / "ph"
    d.mkdir()
    Image.new("RGB", (8, 8), (5, 5, 5)).save(d / "a.png")
    r = subprocess.run(["cmd", "/c", "mklink", "/J", str(d / "loop"), str(d)], capture_output=True, text=True)
    if r.returncode != 0:
        pytest.skip("cannot create a junction here")
    try:
        found = [p for p, _ in scanner.iter_photos(str(d))]
    finally:
        os.rmdir(d / "loop")  # removes only the link
    assert len(found) == 1, f"one real photo was listed {len(found)} times through the junction loop"


def test_bug_filename_with_lone_surrogate_aborts_whole_scan(tmp_path, home):
    """Medium: one undecodable file name must not abort the scan (other photos must still be scanned)."""
    from photofinder import scanner
    from photofinder.index import Index
    d = tmp_path / "sg"
    d.mkdir()
    try:
        Image.new("RGB", (8, 8), (5, 5, 5)).save(d / "bad\ud800.png")
    except (OSError, UnicodeError):
        pytest.skip("file system refuses lone-surrogate names")
    Image.new("RGB", (8, 8), (5, 5, 5)).save(d / "good.png")
    idx = Index(tmp_path / "x.db")
    res = scanner.scan(str(d), idx, FakeEngine())  # must not raise
    assert res["total"] == 2
    assert idx.is_done(str(d / "good.png"), os.stat(d / "good.png").st_size,
                       os.stat(d / "good.png").st_mtime_ns, "fake/v1")


def test_bug_corrupt_database_file_crashes_startup(tmp_path, home):
    """Medium: a damaged photos.db (a rebuildable cache) must not make the app unable to start."""
    from photofinder.index import Index
    home.mkdir(parents=True, exist_ok=True)
    (home / "photos.db").write_bytes(b"this is not a sqlite database" * 50)
    Index()  # must recover (e.g. start a fresh cache) instead of raising DatabaseError


# ---- settings ----------------------------------------------------------------------------------

@pytest.mark.parametrize("content", ["[]", "null", "123"])
def test_bug_settings_valid_json_but_not_object_crashes(home, content):
    """Medium: settings.json that is valid JSON but not an object must load as defaults, not raise."""
    from photofinder import settings
    home.mkdir(parents=True, exist_ok=True)
    (home / "settings.json").write_text(content, encoding="utf-8")
    cfg = settings.load()
    assert cfg["low"] == settings.DEFAULTS["low"] and cfg["folders"] == []


def test_bug_settings_wrong_value_types_reach_the_ui(home):
    """Medium: settings with wrong types (low as text, folders null) must be sanitised by load()."""
    from photofinder import settings
    home.mkdir(parents=True, exist_ok=True)
    (home / "settings.json").write_text(json.dumps({"low": "x", "high": None, "folders": None}), encoding="utf-8")
    cfg = settings.load()
    assert isinstance(cfg["low"], float) and isinstance(cfg["high"], float)
    assert isinstance(cfg["folders"], list)


# ---- reference faces ---------------------------------------------------------------------------

def test_bug_zero_byte_reference_image_aborts_whole_batch(tmp_path, make_photo, home):
    """Medium: an empty/unreadable reference file is reported in notes; the other references still load."""
    from photofinder import matcher
    good = make_photo("refs", "good.png", 5)
    empty = tmp_path / "refs" / "empty.png"
    empty.write_bytes(b"")
    items, notes = matcher.analyse_reference_images(FakeEngine(), [str(empty), str(good)])
    assert [i["path"] for i in items] == [str(good)]
    assert any("empty.png" in n for n in notes)


def test_bug_load_refs_accepts_wrong_embedding_dimension(home):
    """Medium: a reference matrix that is not N x 128 loads as empty (docstring: inconsistent set -> empty)."""
    from photofinder import matcher
    matcher.save_refs(["a.png"], [2], np.ones((2, 64), np.float32))
    _, counts, mat = matcher.load_refs()
    assert mat.shape[1] == 128 and sum(counts) == len(mat)


# ---- copier ------------------------------------------------------------------------------------

def test_bug_copy_log_overwritten_when_two_copies_start_in_same_second(tmp_path, make_photo, home, monkeypatch):
    """Low: two copy runs must not overwrite each other's copy_log (log name is only second-resolution)."""
    import time as _t
    from photofinder import copier
    a = make_photo("trip", "a.png", 5)
    b = make_photo("trip2", "b.png", 6)
    monkeypatch.setattr(_t, "strftime", lambda *a, **k: "20260101_000000")
    out = tmp_path / "out"
    _, log1 = copier.copy_tiers([(0.9, str(a))], [], out)
    first = log1.read_text(encoding="utf-8-sig")
    _, log2 = copier.copy_tiers([(0.9, str(b))], [], out)
    assert log1 != log2 or log1.read_text(encoding="utf-8-sig") == first, "first copy log was overwritten"


# ---- UI ----------------------------------------------------------------------------------------

def test_bug_viewer_shows_other_photo_when_grid_changes_during_scan(tmp_path, home):
    """Medium: the open viewer must keep showing the same photo when the live grid list is re-sorted."""
    from PySide6.QtWidgets import QApplication
    from photofinder import ui
    app = QApplication.instance() or QApplication([])
    pa, pb = tmp_path / "a.png", tmp_path / "b.png"
    Image.new("RGB", (30, 30), (1, 1, 1)).save(pa)
    Image.new("RGB", (30, 30), (2, 2, 2)).save(pb)
    win = ui.MainWindow()
    win.grid_ok.set_items([(0.9, str(pa)), (0.6, str(pb))])
    viewer = ui.ViewerDialog(win, win.grid_ok.items, {}, 1)  # same list object the grid keeps for live results
    assert viewer.items[viewer.i][1] == str(pb)
    win.grid_ok.add_if_new(0.8, str(tmp_path / "c.png"))     # a live match arrives and re-sorts the list
    assert viewer.items[viewer.i][1] == str(pb), "viewer index now points at a different photo"
    viewer.close()
    win.close()


class _SlowEngine(FakeEngine):
    def faces(self, img):
        time.sleep(0.25)
        return super().faces(img)


def test_bug_closing_window_during_scan_runs_slots_on_closed_database(tmp_path, make_photo, home, monkeypatch):
    """Medium: after closeEvent the queued worker signals must not touch the already closed index."""
    from PySide6.QtWidgets import QApplication
    from photofinder import ui
    app = QApplication.instance() or QApplication([])
    for i in range(6):
        make_photo("trip", f"p{i}.png", 5)
    errors = []
    monkeypatch.setattr(sys, "excepthook", lambda t, v, tb: errors.append(repr(v)))
    win = ui.MainWindow()
    win._engine = _SlowEngine()
    win.refs, win.ref_paths = np.vstack([REF]), ["ref.png"]
    win._add_folder_item(str(tmp_path / "trip"))
    win.out_edit.setText(str(tmp_path / "found"))
    win.start_scan()
    assert _wait(app, lambda: win.bar.value() >= 1 or win.bar.maximum() > 1)
    win.close()
    for _ in range(40):
        app.processEvents()
        time.sleep(0.01)
    assert not errors, f"slot raised after the window closed: {errors[:1]}"


def test_bug_settings_with_text_threshold_cannot_open_window(tmp_path, home):
    """Medium: a hand-damaged settings.json must not make the main window impossible to open."""
    from PySide6.QtWidgets import QApplication
    from photofinder import ui
    QApplication.instance() or QApplication([])
    home.mkdir(parents=True, exist_ok=True)
    (home / "settings.json").write_text(json.dumps({"low": "x", "folders": None}), encoding="utf-8")
    win = ui.MainWindow()  # must not raise
    win.close()
