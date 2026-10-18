"""Date sort, settings (threads, window geometry), grid keys and the About box. Synthetic images only."""
import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pytest
from PIL import Image

pytest.importorskip("PySide6")
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from conftest import snap


def _wait(app, cond, ms=10000):
    end = time.time() + ms / 1000
    while time.time() < end and not cond():
        app.processEvents()
        time.sleep(0.01)
    return cond()


def _jpeg(path, taken=None, original=None):
    ex = Image.Exif()
    if taken:
        ex[0x0132] = taken
    if original:
        ex[0x8769] = {0x9003: original}
    Image.new("RGB", (16, 16), (90, 90, 90)).save(path, exif=ex)
    return str(path)


# ---- dates ------------------------------------------------------------------------------------

def test_exif_original_beats_datetime_beats_file_time(tmp_path):
    from photofinder import dates
    a = _jpeg(tmp_path / "a.jpg", taken="2020:01:01 10:00:00", original="2019:05:03 14:20:11")
    b = _jpeg(tmp_path / "b.jpg", taken="2020:01:01 10:00:00")
    c = _jpeg(tmp_path / "c.jpg")
    os.utime(c, (1_000_000_000, 1_000_000_000))
    assert dates.taken(a) == "2019-05-03 14:20:11"
    assert dates.taken(b) == "2020-01-01 10:00:00"
    assert dates.taken(c) == time.strftime(dates.FMT, time.localtime(1_000_000_000))


def test_junk_exif_date_falls_back(tmp_path):
    from photofinder import dates
    p = _jpeg(tmp_path / "x.jpg", original="0000:00:00 00:00:00")
    assert dates.taken(p).startswith(str(time.localtime(os.stat(p).st_mtime).tm_year))
    (tmp_path / "broken.jpg").write_bytes(b"nope")
    assert dates.taken(str(tmp_path / "broken.jpg"))   # unreadable header: still a file-time date


def test_dates_are_cached_and_photo_untouched(tmp_path, home):
    from photofinder.index import Index
    from photofinder.workers import DateWorker
    p = _jpeg(tmp_path / "a.jpg", original="2018:02:03 04:05:06")
    before, idx, got = snap(p), Index(), {}
    w = DateWorker(idx, [p])
    w.got.connect(got.update)
    w.run()   # in this thread: no event loop needed for a direct call
    assert got == {p: "2018-02-03 04:05:06"}
    assert idx.get_date(p, os.stat(p).st_mtime_ns) == "2018-02-03 04:05:06"
    assert idx.get_date(p, 1) is None   # a changed file is not served from the cache
    assert snap(p) == before


# ---- settings -----------------------------------------------------------------------------------

def test_scan_threads_setting_is_validated():
    from photofinder import settings
    assert settings._clean({"scan_threads": 4})["scan_threads"] == 4
    for bad in (-1, 99, "4", 2.5, True, None):
        assert settings._clean({"scan_threads": bad})["scan_threads"] == 0
    assert settings.scan_threads({"scan_threads": 3}) == 3
    assert settings.scan_threads({"scan_threads": 0}, cpus=12) == 6
    assert settings.scan_threads({"scan_threads": 0}, cpus=2) == 1
    assert settings.scan_threads({}, cpus=None) >= 1


def test_geometry_setting_is_validated():
    import base64
    from photofinder import settings
    good = base64.b64encode(bytes.fromhex("01d9d0cb") + b"\0" * 40).decode()
    assert settings._clean({"geometry": good})["geometry"] == good
    for bad in ("", "!!!", "aGVsbG8=", 5, None, "A" * 5000):
        assert settings._clean({"geometry": bad})["geometry"] == ""
    assert settings._clean({"sort": "date"})["sort"] == "date" and settings._clean({"sort": "x"})["sort"] == "score"


def test_bad_geometry_never_stops_startup(tmp_path, home):
    import json
    from photofinder import ui
    home.mkdir(parents=True)
    (home / "settings.json").write_text(json.dumps({"geometry": "!!!not base64!!!", "sort": 7}))
    app = QApplication.instance() or QApplication([])
    win = ui.MainWindow()
    win.close()
    win2 = ui.MainWindow()   # the geometry saved by the first run is restored without trouble
    assert win2.cfg["geometry"]
    win2.close()


def test_window_geometry_round_trip(home):
    from photofinder import settings, ui
    app = QApplication.instance() or QApplication([])
    win = ui.MainWindow()
    win.show()
    win.resize(1180, 740)
    app.processEvents()
    win.close()   # the close event saves the window state
    assert settings.load()["geometry"]
    win2 = ui.MainWindow()
    # (the offscreen screen is only 800 px wide, so Qt clamps the width to the 1100 minimum; height is exact)
    assert (win2.width(), win2.height()) == (1100, 740)
    win2.close()


# ---- sort by date taken ---------------------------------------------------------------------------

def _window(tmp_path, home):
    from photofinder import ui
    app = QApplication.instance() or QApplication([])
    d = tmp_path / "ph"
    d.mkdir()
    paths_ = [_jpeg(d / "old.jpg", original="2001:01:01 00:00:00"),
              _jpeg(d / "new.jpg", original="2022:12:31 23:59:59"),
              _jpeg(d / "mid.jpg", original="2010:06:15 12:00:00")]
    win = ui.MainWindow()
    win.grid_ok.set_items([(0.9, paths_[0]), (0.8, paths_[1]), (0.7, paths_[2])])   # by similarity: old, new, mid
    return app, win, paths_


def test_sort_by_date_and_back(tmp_path, home):
    app, win, (old, new, mid) = _window(tmp_path, home)
    assert [p for _, p in win.grid_ok.items] == [old, new, mid]
    win.sort.buttons["date"].click()
    assert _wait(app, lambda: len(win.dates) == 3)
    app.processEvents()
    assert [p for _, p in win.grid_ok.items] == [new, mid, old]
    assert win.cfg["sort"] == "date"
    assert "2022-12-31 23:59:59" in win.grid_ok.rows[new].toolTip()
    # a live match arriving during a scan lands in date order too
    win.grid_ok.add_if_new(0.99, old)   # already known: ignored
    win.sort.buttons["score"].click()
    assert [p for _, p in win.grid_ok.items] == [old, new, mid]
    win.close()


def test_sort_keeps_selection_and_viewer_copy(tmp_path, home):
    from photofinder import ui
    app, win, (old, new, mid) = _window(tmp_path, home)
    win.grid_ok.rows[mid].setSelected(True)
    viewer = ui.ViewerDialog(win, win.grid_ok.items, {}, 2, dates={mid: "2010-06-15 12:00:00"})
    assert "2010-06-15 12:00:00" in viewer.path.text()
    win.sort.buttons["date"].click()
    assert _wait(app, lambda: len(win.dates) == 3)
    app.processEvents()
    assert win.grid_ok.selected_paths() == [mid]               # selection survives the re-sort
    assert viewer.items[viewer.i][1] == mid                    # the viewer keeps its own copy of the list
    viewer.close()
    win.close()


# ---- keyboard ---------------------------------------------------------------------------------------

def test_grid_keys_review_the_selection(tmp_path, home):
    app, win, (old, new, mid) = _window(tmp_path, home)
    win.run = win.index.get_run(win.index.create_run("t", [], str(tmp_path / "r"), 0.3, 0.5))
    win._update_review_state()
    view = win.grid_ok.view
    QTest.keyClick(view, Qt.Key_A, Qt.ControlModifier)
    assert len(win.grid_ok.selected_paths()) == 3
    QTest.keyClick(view, Qt.Key_N)
    assert win.index.verdicts(win.run["id"]) == {old: "no", new: "no", mid: "no"}
    win.grid_ok.set_items([(0.9, old), (0.8, new), (0.7, mid)])   # the fake window has no scored results
    win.grid_ok.view.selectAll()
    QTest.keyClick(win.grid_ok.view, Qt.Key_U)
    assert win.index.verdicts(win.run["id"]) == {}
    win.close()


def test_grid_review_keys_do_nothing_without_a_search(tmp_path, home):
    app, win, (old, new, mid) = _window(tmp_path, home)
    assert win.run is None
    win.grid_ok.view.selectAll()
    QTest.keyClick(win.grid_ok.view, Qt.Key_Y)
    assert win.verdicts == {}
    win.close()


def test_enter_opens_viewer_on_current_item(tmp_path, home, monkeypatch):
    from photofinder.ui import grid
    app, win, (old, new, mid) = _window(tmp_path, home)
    opened = []

    class Fake:
        def __init__(self, parent, items, boxes, idx, **kw):
            opened.append(items[idx][1])

        def exec(self):
            pass

    monkeypatch.setattr(grid, "ViewerDialog", Fake)
    win.grid_ok.view.setCurrentItem(win.grid_ok.rows[new])
    QTest.keyClick(win.grid_ok.view, Qt.Key_Return)
    assert opened == [new]
    win.close()


# ---- about / links ------------------------------------------------------------------------------------

def test_about_dialog_and_links(tmp_path, home, monkeypatch):
    from photofinder import __version__
    from photofinder.ui import about
    app, win, _ = _window(tmp_path, home)
    opened = []
    monkeypatch.setattr(about.QDesktopServices, "openUrl", lambda u: opened.append(u.toString()))
    dlg = about.AboutDialog(win)
    texts = " ".join(w.text() for w in dlg.findChildren(about.label("").__class__))
    assert __version__ in texts and "MIT" in texts
    dlg.b_github.click()
    win.act_updates.trigger()
    assert opened == ["https://github.com/Kylekk29/PhotoFinderPro", "https://github.com/Kylekk29/PhotoFinderPro/releases"]
    assert dlg.notices is not None and dlg.notices.name == "THIRD_PARTY_NOTICES.txt"   # repo root, from source
    dlg.b_notices.click()
    assert opened[-1].startswith("file:///") and opened[-1].endswith("THIRD_PARTY_NOTICES.txt")
    win.close()


def test_about_hides_notices_button_when_missing(tmp_path, home, monkeypatch):
    from photofinder.ui import about
    app, win, _ = _window(tmp_path, home)
    monkeypatch.setattr(about, "find_notices", lambda: None)
    assert about.AboutDialog(win).b_notices.isHidden()
    win.close()
