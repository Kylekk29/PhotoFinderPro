"""Copy-only output. Never overwrites, never deletes, verifies every copy by SHA-256.

Safety contract:
  * Every file written must pass inside_roots(): only the app data folder and the chosen output folder.
  * The output folder may not be inside a scanned folder (or contain one), so copies are never re-scanned
    and originals are never mixed with copies.
"""
import csv
import hashlib
import json
import os
import shutil
import time
from pathlib import Path

import numpy as np

from . import paths
from .matcher import TIER_CONFIRMED, TIER_MAYBE, tier_of
from .scanner import DiskLow

MIN_FREE_BYTES = 5 * 1024 ** 3  # live copying stops when the output drive has less free space


def _resolved(p):
    return Path(p).resolve()


def inside_roots(path, roots):
    """Return the resolved path, or raise PermissionError if it is outside every allowed root."""
    p = _resolved(path)
    for r in roots:
        r = _resolved(r)
        if p == r or r in p.parents:
            return p
    raise PermissionError(f"Refusing to write outside allowed folders: {p}")


def validate_output_root(output_root, source_folders):
    """The output folder must not sit inside a scanned folder, nor contain one."""
    out = _resolved(output_root)
    for s in source_folders:
        s = _resolved(s)
        if out == s or s in out.parents:
            raise PermissionError(f"Output folder is inside a scanned folder: {out} in {s}")
        if out in s.parents:
            raise PermissionError(f"Output folder contains a scanned folder: {out} contains {s}")


_FORBIDDEN_NAME_CHARS = '<>:"/\\|?*'


def safe_name(text, fallback="搜尋"):
    """A folder-name-safe version of `text` (Windows forbids <>:"/\\|?* and trailing dots/spaces)."""
    s = "".join(c for c in (text or "") if c not in _FORBIDDEN_NAME_CHARS and ord(c) >= 32)
    return s.strip().rstrip(". ")[:60] or fallback


def new_run_dir(output_root, name):
    """Create a NEW results folder '<date time> <name>' inside output_root. Never reuses an existing one."""
    out = Path(output_root)
    base = f"{time.strftime('%Y-%m-%d %H%M')} {safe_name(name)}"
    cand, n = out / base, 2
    while cand.exists():
        cand = out / f"{base} ({n})"
        n += 1
    inside_roots(cand, [out])
    cand.mkdir(parents=True, exist_ok=False)
    return cand


def unique_path(folder, stem, suffix):
    """folder/stem+suffix, or stem_2+suffix ... so nothing is ever overwritten."""
    p, n = Path(folder) / f"{stem}{suffix}", 2
    while p.exists():
        p = Path(folder) / f"{stem}_{n}{suffix}"
        n += 1
    return p


def write_run_json(run_dir, data):
    """run.json inside the run folder: what this search was. Contains NO face vectors (biometric data)."""
    run_dir = Path(run_dir)
    inside_roots(run_dir / "run.json", [run_dir])
    with open(run_dir / "run.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def sha256_of(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            block = f.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def _candidates(dest_dir, name):
    yield dest_dir / name
    stem, ext = os.path.splitext(name)
    n = 2
    while True:
        yield dest_dir / f"{stem}__{n}{ext}"
        n += 1


def safe_copy(src, tier, out_root, extra_roots=()):
    """Copy src into <out_root>/<tier>/<parent folder name>/ with shutil.copy2.

    An identical copy under ANY numbered name is left alone ("already_there"); a same-named file with
    different content gets a numbered name. Returns (status, dest).
    """
    out_root = Path(out_root)
    roots = [paths.app_home(), out_root, *extra_roots]
    parent = os.path.basename(os.path.dirname(src)) or "root"
    dest_dir = inside_roots(out_root / tier / parent, roots)
    dest_dir.mkdir(parents=True, exist_ok=True)
    name = os.path.basename(src)
    src_hash = sha256_of(src)
    dest = None
    for cand in _candidates(dest_dir, name):
        if not cand.exists():
            dest = cand
            break
        if sha256_of(cand) == src_hash:
            return "already_there", cand
    dest = inside_roots(dest, roots)
    shutil.copy2(src, dest)
    return ("copied" if sha256_of(dest) == src_hash else "HASH_MISMATCH"), dest


LOG_HEADER = ["tier", "similarity_%", "source", "copy", "status"]


def open_append_log(path):
    """Open the copy journal for appending; returns (file, csv writer)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not path.exists()
    f = open(path, "a", newline="", encoding="utf-8-sig")
    w = csv.writer(f)
    if is_new:
        w.writerow(LOG_HEADER)
        f.flush()
    return f, w


class LiveCopier:
    """scan() hook: the moment a photo matches, copy it into the output folder (copy only).

    Photos with no face or unreadable photos are NOT copied; they stay in the index.
    Every copy is verified by SHA-256 and written to live_copy_log.csv immediately.
    """

    def __init__(self, refs, low, high, out_root, source_folders=(), on_match=None):
        if len(refs) == 0:
            raise ValueError("need at least one reference face before scanning")
        validate_output_root(out_root, source_folders)
        self.refs = np.asarray(refs, np.float32)
        self.low, self.high = low, high
        self.on_match = on_match  # on_match(tier, score, path, face_box) after each verified copy
        self.out_root = Path(out_root)
        self.out_root.mkdir(parents=True, exist_ok=True)
        self.log_file, self.writer = open_append_log(self.out_root / "live_copy_log.csv")
        self.counts = {}

    def __call__(self, path, status, faces):
        if status != "ok":
            return
        best = max(faces, key=lambda f: float((self.refs @ f[2]).max()))
        self._copy(path, float((self.refs @ best[2]).max()), best[0])

    def _copy(self, path, score, box):
        tier = tier_of(score, self.low, self.high)
        if tier is None:
            return
        if shutil.disk_usage(self.out_root).free < MIN_FREE_BYTES:
            raise DiskLow(str(self.out_root))
        result, dest = safe_copy(path, tier, self.out_root)
        self.writer.writerow([tier, f"{score * 100:.1f}", path, str(dest), result])
        self.log_file.flush()
        if result == "HASH_MISMATCH":
            raise RuntimeError(f"copy verification failed for {path}")
        self.counts[tier] = self.counts.get(tier, 0) + 1
        if self.on_match is not None:
            self.on_match(tier, score, path, box)

    def copy_existing(self, results, boxes, stop_event=None, progress_cb=None):
        """Copy matches among photos that were already scanned (a new search over scanned folders).

        results = [(score, path)]. A photo that can no longer be read is logged and skipped.
        """
        for i, (score, path) in enumerate(results, 1):
            if stop_event is not None and stop_event.is_set():
                break
            try:
                self._copy(path, score, boxes.get(path))
            except DiskLow:
                raise
            except Exception as e:
                self.writer.writerow(["", f"{score * 100:.1f}", path, "", f"ERROR: {e}"])
                self.log_file.flush()
            if progress_cb:
                progress_cb(i, len(results), path)

    def close(self):
        self.log_file.close()


def copy_tiers(confirmed, maybe, out_root, source_folders=(), progress_cb=None, stop_event=None):
    """Copy both result lists (copy only) and write a log. Returns (counts, log_path)."""
    validate_output_root(out_root, source_folders)
    jobs = [(TIER_CONFIRMED, s, p) for s, p in confirmed] + [(TIER_MAYBE, s, p) for s, p in maybe]
    counts, rows = {}, []
    for i, (tier, score, src) in enumerate(jobs, 1):
        if stop_event is not None and stop_event.is_set():
            break
        try:
            status, dest = safe_copy(src, tier, out_root)
        except Exception as e:
            status, dest = f"ERROR: {e}", ""
        key = "ERROR" if status.startswith("ERROR") else status
        counts[key] = counts.get(key, 0) + 1
        rows.append([tier, f"{score * 100:.1f}", src, str(dest), status])
        if progress_cb:
            progress_cb(i, len(jobs), src)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    log_path = Path(out_root) / f"copy_log_{stamp}.csv"
    n = 2
    while log_path.exists():  # two runs in the same second must not overwrite each other's log
        log_path = Path(out_root) / f"copy_log_{stamp}_{n}.csv"
        n += 1
    return counts, write_csv(log_path, LOG_HEADER, rows, out_root)


FINAL_DIR = "final"


def export_final(items, run_dir, source_folders=(), progress_cb=None, stop_event=None):
    """Copy the reviewed result set [(score, path)] into <run_dir>/final/ (copy only, verified, never
    overwrites). Earlier copies in confirmed/ and maybe/ stay where they are. Returns (counts, log_path)."""
    validate_output_root(run_dir, source_folders)
    counts, rows = {}, []
    for i, (score, src) in enumerate(items, 1):
        if stop_event is not None and stop_event.is_set():
            break
        try:
            status, dest = safe_copy(src, FINAL_DIR, run_dir)
        except Exception as e:
            status, dest = f"ERROR: {e}", ""
        key = "ERROR" if status.startswith("ERROR") else status
        counts[key] = counts.get(key, 0) + 1
        rows.append([FINAL_DIR, f"{score * 100:.1f}", src, str(dest), status])
        if progress_cb:
            progress_cb(i, len(items), src)
    log = unique_path(Path(run_dir), f"final_log_{time.strftime('%Y%m%d_%H%M%S')}", ".csv")
    return counts, write_csv(log, LOG_HEADER, rows, run_dir)


def write_csv(path, header, rows, root):
    """Write a CSV report; only inside `root` (the output folder) or the app data folder."""
    path = Path(path)
    inside_roots(path, [paths.app_home(), root])
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    return path


__all__ = ["safe_copy", "LiveCopier", "validate_output_root", "inside_roots", "sha256_of",
           "TIER_CONFIRMED", "TIER_MAYBE", "DiskLow"]
