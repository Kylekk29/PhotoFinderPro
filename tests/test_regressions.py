"""Regression tests for bugs found by the self-check (2026-10-18)."""
import os
import threading

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PIL import Image
from PySide6.QtWidgets import QApplication

from conftest import FakeEngine, REF
from photofinder import index as index_mod, matcher, paths, scanner, thumbs


def test_damaged_thumbnail_cache_is_rebuilt_not_grey(tmp_path, home):
    src = tmp_path / "a.jpg"
    im = Image.new("RGB", (400, 300))
    for x in range(400):
        for y in range(300):
            im.putpixel((x, y), (x % 255, y % 255, 120))
    im.save(src)
    thumbs.thumbnail(str(src), 160)
    cache = next(paths.thumb_dir().glob("*.jpg"))
    data = cache.read_bytes()
    cache.write_bytes(data[: len(data) // 2])          # crash in the middle of a write
    t = np.asarray(thumbs.thumbnail(str(src), 160))
    assert t.std() > 5                                  # a real picture, not the flat grey placeholder


def test_results_only_from_selected_folders_and_trip_is_not_trips(tmp_path, make_photo, home):
    make_photo("Trip", "a.png", 5)
    make_photo("Trips", "b.png", 5)
    idx = index_mod.Index()
    scanner.scan([(str(tmp_path / "Trip"), True), (str(tmp_path / "Trips"), True)], idx, FakeEngine())
    refs = np.vstack([REF])
    assert len(matcher.score_photos(idx, refs)[0]) == 2                       # no filter: both
    only_trip = matcher.score_photos(idx, refs, [str(tmp_path / "Trip")])[0]
    assert [os.path.basename(os.path.dirname(p)) for _, p in only_trip] == ["Trip"]
    # trailing separators and different case (Windows) do not matter
    assert len(matcher.score_photos(idx, refs, [str(tmp_path / "TRIP") + os.sep])[0]) == 1


def test_error_photo_is_retried_on_every_scan(tmp_path, home):
    d = tmp_path / "a"
    d.mkdir()
    bad = d / "b.png"
    bad.write_bytes(b"not an image yet")
    idx, eng = index_mod.Index(), FakeEngine()
    assert scanner.scan(str(d), idx, eng)["scanned"] == 1
    again = scanner.scan(str(d), idx, eng)
    assert again["scanned"] == 1 and again["skipped"] == 0
    Image.new("RGB", (64, 64), (5, 5, 5)).save(bad)       # the cause went away (same name, now readable)
    assert scanner.scan(str(d), idx, eng)["scanned"] == 1 and idx.stats() == {"ok": 1}


def test_overlapping_or_repeated_folders_count_each_photo_once(tmp_path, make_photo, home):
    make_photo("Family/2019", "p.png", 5)
    idx = index_mod.Index()
    r = scanner.scan([(str(tmp_path / "Family"), True), (str(tmp_path / "Family" / "2019"), True),
                      (str(tmp_path / "Family"), True)], idx, FakeEngine())
    assert r["total"] == 1 and r["scanned"] == 1


def test_stop_works_while_listing_photos(tmp_path, home):
    d = tmp_path / "many"
    d.mkdir()
    for i in range(1100):
        (d / f"f{i}.png").write_bytes(b"x")
    stop = threading.Event()
    seen = []

    def progress(i, total, path):
        seen.append(total)
        if total == 0:
            stop.set()

    r = scanner.scan(str(d), index_mod.Index(), FakeEngine(), progress_cb=progress, stop_event=stop)
    assert r["stopped"] and r["scanned"] == 0 and 0 in seen


def test_selection_survives_a_refresh_of_the_grid(tmp_path, make_photo, home):
    from photofinder import ui
    app = QApplication.instance() or QApplication([])
    win = ui.MainWindow()
    paths_ = [str(make_photo("a", f"p{i}.png", 5)) for i in range(3)]
    win.grid_ok.set_items([(0.9 - i * 0.1, p) for i, p in enumerate(paths_)])
    win.grid_ok.view.item(1).setSelected(True)
    assert win.grid_ok.selected_paths() == [paths_[1]]
    win.grid_ok.add_if_new(0.95, str(tmp_path / "new.png"))   # a live match arrives during a scan
    win.grid_ok.render()
    assert win.grid_ok.selected_paths() == [paths_[1]]
    assert win.selbar.isHidden() is False
    win.close()
