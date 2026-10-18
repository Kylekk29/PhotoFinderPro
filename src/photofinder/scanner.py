"""Read-only folder scan. Resumable: unchanged files already in the index are skipped."""
import os
import sqlite3
import threading
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

from .imageio import SUPPORTED_EXTS, UNSUPPORTED_EXTS, read_image


class DiskLow(Exception):
    """Raised by a result hook when the output drive is nearly full; the scan stops cleanly."""


def iter_photos(folder, recursive=True):
    """Yield (path, supported). Only lists directories; never touches file contents.

    A folder reached twice (a Windows junction or symlink pointing back up the tree) is listed once,
    otherwise one photo would show up many times under ever longer paths.
    """
    visited = set()
    for dirpath, dirs, files in os.walk(folder):
        real = os.path.normcase(os.path.realpath(dirpath))
        if real in visited:
            dirs[:] = []
            continue
        visited.add(real)
        if not recursive:
            dirs[:] = []
        for name in files:
            ext = os.path.splitext(name)[1].lower()
            if ext in SUPPORTED_EXTS:
                yield os.path.join(dirpath, name), True
            elif ext in UNSUPPORTED_EXTS:
                yield os.path.join(dirpath, name), False


def analyse(path, supported, engine):
    """(status, faces) for one photo; read-only."""
    if not supported:
        return "unsupported", []
    try:
        img = read_image(path)
        if img is None:
            return "error", []
        faces = engine.faces(img)
        return ("ok" if faces else "noface"), faces
    except Exception:
        return "error", []


def scan(folders, index, engine, progress_cb=None, stop_event=None, on_result=None,
         engine_factory=None, workers=1):
    """Scan `folders` (a path or a list of (path, recursive)) read-only.

    on_result(path, status, faces) runs for each newly analysed photo BEFORE it is recorded
    as done (live copying hooks in here). If it fails the photo is not recorded, so the next
    scan retries it; DiskLow stops the scan cleanly.

    With `engine_factory` and workers > 1 the photos are analysed in a thread pool (each thread builds its
    own engine: OpenCV's detector/recogniser are not thread-safe). Everything else stays on this thread.
    """
    targets = [(folders, True)] if isinstance(folders, (str, os.PathLike)) else list(folders)
    version = getattr(engine, "version", "unknown")
    stopped = lambda: stop_event is not None and stop_event.is_set()
    # List first. Each photo once, even when folders overlap or are listed twice. Stop works while listing.
    entries, seen = [], set()
    for f, rec in targets:
        for path, supported in iter_photos(f, rec):
            key = os.path.normcase(os.path.abspath(path))
            if key in seen:
                continue
            seen.add(key)
            entries.append((path, supported))
            if len(entries) % 500 == 0:
                if progress_cb:
                    progress_cb(0, 0, path)  # total 0 = still listing
                if stopped():
                    break
        if stopped():
            break
    total = len(entries)
    if engine_factory is not None and workers > 1:
        return _scan_parallel(entries, index, version, progress_cb, stopped, on_result,
                              engine_factory, workers)
    done = skipped = failed = 0
    disk_low = False
    for i, (path, supported) in enumerate(entries, 1):
        if stopped():
            break
        try:
            try:
                st = os.stat(path)
            except OSError:
                index.save(path, 0, 0, "error", version)
                continue
            if index.is_done(path, st.st_size, st.st_mtime_ns, version):
                skipped += 1
            else:
                status, faces = analyse(path, supported, engine)
                try:
                    if on_result is not None:
                        on_result(path, status, faces)
                except DiskLow:
                    disk_low = True
                    break
                except Exception:
                    failed += 1
                    status = None
                if status is not None:
                    index.save(path, st.st_size, st.st_mtime_ns, status, version, faces)
                    done += 1
        except (UnicodeError, sqlite3.Error):
            failed += 1  # e.g. a file name that cannot be stored: skip that one photo, keep scanning
        if progress_cb:
            progress_cb(i, total, path)
    index.commit()
    return {"total": total, "scanned": done, "skipped": skipped, "failed": failed,
            "disk_low": disk_low,
            "stopped": stopped()}


def _scan_parallel(entries, index, version, progress_cb, stopped, on_result, engine_factory, workers):
    """Same rules as the sequential loop; only analyse() runs in the pool. At most 2*workers photos are in
    flight, so memory stays bounded and Stop reacts within a couple of photos."""
    local = threading.local()

    def job(path, supported):
        if not supported:
            return "unsupported", []
        try:
            if getattr(local, "engine", None) is None:
                local.engine = engine_factory()
        except Exception:
            return "error", []
        return analyse(path, supported, local.engine)

    total = len(entries)
    done = skipped = failed = n = 0
    disk_low = False
    pending = {}   # future -> (path, size, mtime_ns)

    def tick(path):
        nonlocal n
        n += 1
        if progress_cb:
            progress_cb(n, total, path)

    def finish(fut):
        nonlocal done, failed, disk_low
        path, size, mtime_ns = pending.pop(fut)
        if fut.cancelled() or disk_low:
            return
        try:
            status, faces = fut.result()
            try:
                if on_result is not None:
                    on_result(path, status, faces)
            except DiskLow:
                disk_low = True
                return
            except Exception:
                failed += 1
                status = None
            if status is not None:
                index.save(path, size, mtime_ns, status, version, faces)
                done += 1
        except (UnicodeError, sqlite3.Error):
            failed += 1
        except Exception:
            failed += 1
        tick(path)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        try:
            for path, supported in entries:
                if stopped() or disk_low:
                    break
                try:
                    st = os.stat(path)
                except OSError:
                    try:
                        index.save(path, 0, 0, "error", version)
                    except (UnicodeError, sqlite3.Error):
                        failed += 1
                    tick(path)
                    continue
                try:
                    is_done = index.is_done(path, st.st_size, st.st_mtime_ns, version)
                except (UnicodeError, sqlite3.Error):
                    failed += 1
                    tick(path)
                    continue
                if is_done:
                    skipped += 1
                    tick(path)
                    continue
                while len(pending) >= 2 * workers and not (stopped() or disk_low):
                    for fut in wait(list(pending), return_when=FIRST_COMPLETED)[0]:
                        finish(fut)
                if stopped() or disk_low:
                    break
                pending[pool.submit(job, path, supported)] = (path, st.st_size, st.st_mtime_ns)
            # Drop photos that have not started; the ones already running finish and are recorded normally.
            if stopped() or disk_low:
                for fut in list(pending):
                    fut.cancel()
            while pending:
                for fut in wait(list(pending))[0]:
                    finish(fut)
        finally:
            for fut in pending:
                fut.cancel()
    index.commit()
    return {"total": total, "scanned": done, "skipped": skipped, "failed": failed,
            "disk_low": disk_low, "stopped": stopped()}
