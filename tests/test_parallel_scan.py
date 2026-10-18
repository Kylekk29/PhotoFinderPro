"""Parallel scanning gives the same results as sequential, and keeps every safety rule."""
import threading
import time

import numpy as np

from conftest import FAKE, REF, FakeEngine, snap
from photofinder import copier, index as index_mod, scanner


class SlowEngine(FakeEngine):
    """Fake engine that records which threads used it and takes a little time per photo."""
    def __init__(self, delay=0.0, owners=None):
        super().__init__()
        self.delay, self.owners = delay, owners if owners is not None else set()

    def faces(self, img):
        self.owners.add(threading.get_ident())
        time.sleep(self.delay)
        return FAKE[int(img[0, 0, 0])]


def _photos(make_photo, n=12):
    return [make_photo("a", f"p{i}.png", (5, 6, 7, 0)[i % 4]) for i in range(n)]


def _run(tmp_path, workers, out):
    idx = index_mod.Index(tmp_path / f"i{workers}.db")
    live = copier.LiveCopier(np.vstack([REF]), 0.30, 0.50, out, [tmp_path / "a"])
    seen = []
    res = scanner.scan(str(tmp_path / "a"), idx, FakeEngine(), on_result=live,
                       progress_cb=lambda i, t, p: seen.append(i), engine_factory=SlowEngine, workers=workers)
    live.close()
    return idx, res, live.counts, seen


def test_parallel_matches_sequential(tmp_path, make_photo, home):
    photos = _photos(make_photo)
    before = {p: snap(p) for p in photos}
    i1, r1, c1, _ = _run(tmp_path, 1, tmp_path / "o1")
    i4, r4, c4, seen = _run(tmp_path, 4, tmp_path / "o4")
    assert r1["scanned"] == r4["scanned"] == 12 and r4["failed"] == 0 and c1 == c4
    assert i1.stats() == i4.stats()
    assert sorted(seen) == list(range(1, 13))   # progress ticks once per photo
    names = lambda root: sorted(p.relative_to(root).as_posix() for p in root.rglob("*.png"))
    assert names(tmp_path / "o1") == names(tmp_path / "o4") and names(tmp_path / "o4")
    assert {p: snap(p) for p in photos} == before


def test_each_thread_gets_its_own_engine(tmp_path, make_photo, home):
    _photos(make_photo, 16)
    made, lock = [], threading.Lock()

    def factory():
        e = SlowEngine(delay=0.02)
        with lock:
            made.append(e)
        return e

    scanner.scan(str(tmp_path / "a"), index_mod.Index(), FakeEngine(), engine_factory=factory, workers=4)
    assert 1 < len(made) <= 4
    assert all(len(e.owners) == 1 for e in made)   # an engine is never shared between threads


def test_parallel_skips_unchanged(tmp_path, make_photo, home):
    _photos(make_photo, 6)
    idx = index_mod.Index()
    scanner.scan(str(tmp_path / "a"), idx, FakeEngine(), engine_factory=SlowEngine, workers=3)
    r = scanner.scan(str(tmp_path / "a"), idx, FakeEngine(), engine_factory=lambda: 1 / 0, workers=3)
    assert r["skipped"] == 6 and r["scanned"] == 0


def test_parallel_stop_records_only_finished_photos(tmp_path, make_photo, home):
    _photos(make_photo, 40)
    idx, stop, recorded = index_mod.Index(), threading.Event(), []

    def hook(path, status, faces):
        recorded.append(path)
        if len(recorded) == 3:
            stop.set()

    r = scanner.scan(str(tmp_path / "a"), idx, FakeEngine(), stop_event=stop, on_result=hook,
                     engine_factory=lambda: SlowEngine(0.05), workers=4)
    n = sum(idx.stats().values())
    assert r["stopped"] and 3 <= n < 40
    assert n == len(recorded) == r["scanned"]   # recorded == handed to the hook, nothing half done
    r2 = scanner.scan(str(tmp_path / "a"), idx, FakeEngine(), engine_factory=SlowEngine, workers=4)
    assert r2["scanned"] == 40 - n and r2["skipped"] == n


def test_parallel_failed_hook_leaves_photo_unrecorded(tmp_path, make_photo, home):
    _photos(make_photo, 8)
    idx = index_mod.Index()

    def hook(path, status, faces):
        if path.endswith("p3.png"):
            raise RuntimeError("copy failed")

    r = scanner.scan(str(tmp_path / "a"), idx, FakeEngine(), on_result=hook, engine_factory=SlowEngine, workers=3)
    assert r["failed"] == 1 and r["scanned"] == 7 and sum(idx.stats().values()) == 7
    assert scanner.scan(str(tmp_path / "a"), idx, FakeEngine(), engine_factory=SlowEngine, workers=3)["scanned"] == 1


def test_parallel_disk_low_stops_cleanly(tmp_path, make_photo, home):
    _photos(make_photo, 30)
    idx, calls = index_mod.Index(), []

    def hook(path, status, faces):
        calls.append(path)
        if len(calls) == 2:
            raise scanner.DiskLow()

    r = scanner.scan(str(tmp_path / "a"), idx, FakeEngine(), on_result=hook,
                     engine_factory=lambda: SlowEngine(0.02), workers=4)
    assert r["disk_low"] and sum(idx.stats().values()) == 1 and r["scanned"] == 1


def test_parallel_engine_errors_dont_stop_scan(tmp_path, make_photo, home):
    _photos(make_photo, 5)
    idx = index_mod.Index()
    r = scanner.scan(str(tmp_path / "a"), idx, FakeEngine(), engine_factory=lambda: 1 / 0, workers=3)
    assert r["scanned"] == 5 and idx.stats() == {"error": 5}
