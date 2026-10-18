"""Scan -> index -> match -> live copy, with a fake engine and synthetic solid-colour images."""
import threading

import numpy as np

from conftest import FakeEngine, REF, snap
from photofinder import copier, index as index_mod, matcher, scanner


def test_scan_match_and_copy_end_to_end(tmp_path, make_photo, home):
    photos = [make_photo("trip", "p5.png", 5), make_photo("trip", "p6.png", 6),
              make_photo("trip", "p7.png", 7), make_photo("trip", "p0.png", 0)]
    before = {p: snap(p) for p in photos}
    idx = index_mod.Index()
    eng = FakeEngine()
    out = tmp_path / "found"
    live = copier.LiveCopier(np.vstack([REF]), 0.30, 0.50, out, [tmp_path / "trip"])
    res = scanner.scan(str(tmp_path / "trip"), idx, eng, on_result=live)
    live.close()
    assert res["scanned"] == 4 and res["failed"] == 0
    assert live.counts == {"confirmed": 1, "maybe": 1}
    assert (out / "confirmed" / "trip" / "p5.png").exists()
    assert (out / "maybe" / "trip" / "p6.png").exists()
    assert not (out / "confirmed" / "trip" / "p7.png").exists()
    assert idx.stats() == {"ok": 3, "noface": 1}
    assert {p: snap(p) for p in photos} == before  # originals untouched
    results, boxes = matcher.score_photos(idx, np.vstack([REF]))
    assert [round(s, 2) for s, _ in results][:2] == [1.0, 0.41]
    assert str(photos[0]) in boxes


def test_rescan_skips_unchanged_files(tmp_path, make_photo, home):
    make_photo("a", "p5.png", 5)
    idx, eng = index_mod.Index(), FakeEngine()
    scanner.scan(str(tmp_path / "a"), idx, eng)
    res = scanner.scan(str(tmp_path / "a"), idx, eng)
    assert res["skipped"] == 1 and res["scanned"] == 0 and eng.calls == 1


def test_noface_photos_are_rechecked_when_engine_version_changes(tmp_path, make_photo, home):
    make_photo("a", "p0.png", 0)
    make_photo("a", "p5.png", 5)
    idx = index_mod.Index()
    old = FakeEngine()
    scanner.scan(str(tmp_path / "a"), idx, old)
    assert old.calls == 2
    new = FakeEngine()
    new.version = "fake/v2"
    res = scanner.scan(str(tmp_path / "a"), idx, new)
    assert new.calls == 1 and res["skipped"] == 1  # only the "noface" photo is looked at again


def test_changed_file_is_rescanned(tmp_path, make_photo, home):
    make_photo("a", "p.png", 5)
    idx, eng = index_mod.Index(), FakeEngine()
    scanner.scan(str(tmp_path / "a"), idx, eng)
    make_photo("a", "p.png", 7, size=(80, 80))  # different content and size
    scanner.scan(str(tmp_path / "a"), idx, eng)
    assert eng.calls == 2


def test_stop_event_stops_scan_and_resumes(tmp_path, make_photo, home):
    for i in range(4):
        make_photo("a", f"p{i}.png", 5)
    idx, eng = index_mod.Index(), FakeEngine()
    stop = threading.Event()

    def progress(i, total, path):
        if i == 2:
            stop.set()

    r1 = scanner.scan(str(tmp_path / "a"), idx, eng, progress_cb=progress, stop_event=stop)
    assert r1["stopped"] and r1["scanned"] == 2
    r2 = scanner.scan(str(tmp_path / "a"), idx, eng)
    assert r2["scanned"] == 2 and r2["skipped"] == 2


def test_failed_hook_leaves_photo_unrecorded_for_retry(tmp_path, make_photo, home):
    make_photo("a", "p5.png", 5)
    idx, eng = index_mod.Index(), FakeEngine()

    def boom(path, status, faces):
        raise RuntimeError("copy failed")

    r = scanner.scan(str(tmp_path / "a"), idx, eng, on_result=boom)
    assert r["failed"] == 1 and idx.stats() == {}
    r = scanner.scan(str(tmp_path / "a"), idx, eng)
    assert r["scanned"] == 1


def test_unreadable_file_is_recorded_as_error(tmp_path, home):
    d = tmp_path / "a"
    d.mkdir()
    (d / "broken.jpg").write_bytes(b"not an image")
    idx = index_mod.Index()
    r = scanner.scan(str(d), idx, FakeEngine())
    assert r["scanned"] == 1 and idx.stats() == {"error": 1}


def test_tiers():
    assert matcher.tier_of(0.6) == "confirmed"
    assert matcher.tier_of(0.4) == "maybe"
    assert matcher.tier_of(0.1) is None
