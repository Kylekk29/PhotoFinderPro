"""SQLite cache of scan results, kept in the app data folder (never next to the photos)."""
import json
import sqlite3
import threading
import time
from pathlib import Path

import numpy as np

from . import paths
from .engine import EMB_DIM

RECHECK_STATUSES = ("noface", "error")


class Index:
    def __init__(self, path=None):
        path = Path(path) if path else paths.db_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        # The index is only a cache of scan results. If the file is damaged, start a fresh one next to it
        # (the damaged file is left alone; nothing is deleted) and the photos are simply scanned again.
        candidates = [path] + [path.with_name(f"{path.stem}.fresh{n}{path.suffix}") for n in range(1, 20)]
        for cand in candidates:
            try:
                self._open(cand)
                break
            except sqlite3.DatabaseError:
                continue
        else:
            raise sqlite3.DatabaseError(f"cannot open a scan index near {path}")

    def _open(self, path):
        db = sqlite3.connect(str(path), check_same_thread=False)
        try:
            with self.lock:
                # WAL + a commit per photo: a crash loses at most the photo being scanned.
                db.execute("PRAGMA journal_mode=WAL")
                db.execute("PRAGMA synchronous=NORMAL")
                db.execute("CREATE TABLE IF NOT EXISTS files("
                           "path TEXT PRIMARY KEY, size INTEGER, mtime_ns INTEGER,"
                           " status TEXT, engine_version TEXT)")
                db.execute("CREATE TABLE IF NOT EXISTS faces("
                           "path TEXT, mtime_ns INTEGER, idx INTEGER, x REAL, y REAL, w REAL, h REAL,"
                           " score REAL, emb BLOB, PRIMARY KEY(path, mtime_ns, idx))")
                db.execute("CREATE TABLE IF NOT EXISTS runs("
                           "id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, created TEXT, folders TEXT,"
                           " run_dir TEXT, low REAL, high REAL, finished INTEGER, confirmed INTEGER, maybe INTEGER)")
                # The user's review of a search: "yes" (it is the person) or "no" (it is not). Only a label;
                # copies already in the results folder are never moved or deleted because of it.
                db.execute("CREATE TABLE IF NOT EXISTS verdicts("
                           "run_id INTEGER, path TEXT, verdict TEXT, PRIMARY KEY(run_id, path))")
                db.commit()
        except sqlite3.DatabaseError:
            db.close()
            raise
        self.db = db

    def is_done(self, path, size, mtime_ns, engine_version):
        """True if the file is unchanged and needs no re-check.

        A photo recorded as "noface" by a different engine version is NOT done, so a better
        detector gets a second look at it. An "error" photo is never done: the cause (locked file,
        unplugged drive, half-copied file) is often temporary, so every scan tries it again.
        """
        with self.lock:
            row = self.db.execute(
                "SELECT size, mtime_ns, status, engine_version FROM files WHERE path=?", (path,)).fetchone()
        if row is None or row[0] != size or row[1] != mtime_ns:
            return False
        if row[2] == "error":
            return False
        if row[2] in RECHECK_STATUSES and row[3] != engine_version:
            return False
        return True

    def save(self, path, size, mtime_ns, status, engine_version, faces=()):
        with self.lock:
            self.db.execute("DELETE FROM faces WHERE path=?", (path,))
            self.db.execute("INSERT OR REPLACE INTO files VALUES(?,?,?,?,?)",
                            (path, size, mtime_ns, status, engine_version))
            for i, (box, score, emb) in enumerate(faces):
                self.db.execute("INSERT OR REPLACE INTO faces VALUES(?,?,?,?,?,?,?,?,?)",
                                (path, mtime_ns, i, *box, score, np.asarray(emb, np.float32).tobytes()))
            self.db.commit()

    def commit(self):
        with self.lock:
            self.db.commit()

    def close(self):
        with self.lock:
            self.db.commit()
            self.db.close()

    def embeddings(self):
        """(paths per face row, matrix N x 128, boxes) for current versions of scanned files."""
        with self.lock:
            rows = self.db.execute(
                "SELECT f.path, f.emb, f.x, f.y, f.w, f.h FROM faces f JOIN files s "
                "ON s.path=f.path AND s.mtime_ns=f.mtime_ns").fetchall()
        paths_ = [r[0] for r in rows]
        if not rows:
            mat = np.zeros((0, EMB_DIM), np.float32)
        else:
            mat = np.frombuffer(b"".join(r[1] for r in rows), np.float32).reshape(-1, EMB_DIM)
        return paths_, mat, [(r[2], r[3], r[4], r[5]) for r in rows]

    # ---- searches ("runs"): one results folder + its own reference faces each ------------------------
    _RUN_COLS = "id, name, created, folders, run_dir, low, high, finished, confirmed, maybe"

    @staticmethod
    def _run(row):
        keys = ("id", "name", "created", "folders", "run_dir", "low", "high", "finished", "confirmed", "maybe")
        d = dict(zip(keys, row))
        d["folders"] = json.loads(d["folders"] or "[]")
        return d

    def create_run(self, name, folders, run_dir, low, high):
        with self.lock:
            cur = self.db.execute(
                "INSERT INTO runs(name, created, folders, run_dir, low, high, finished, confirmed, maybe)"
                " VALUES(?,?,?,?,?,?,0,0,0)",
                (name, time.strftime("%Y-%m-%d %H:%M:%S"), json.dumps(list(folders), ensure_ascii=False),
                 str(run_dir), low, high))
            self.db.commit()
            return cur.lastrowid

    def update_run(self, run_id, **fields):
        allowed = {"name", "folders", "low", "high", "finished", "confirmed", "maybe"}
        bad = set(fields) - allowed
        if bad:
            raise ValueError(f"cannot update {bad}")
        if "folders" in fields:
            fields["folders"] = json.dumps(list(fields["folders"]), ensure_ascii=False)
        if not fields:
            return
        sets = ", ".join(f"{k}=?" for k in fields)
        with self.lock:
            self.db.execute(f"UPDATE runs SET {sets} WHERE id=?", (*fields.values(), run_id))
            self.db.commit()

    def get_run(self, run_id):
        with self.lock:
            row = self.db.execute(f"SELECT {self._RUN_COLS} FROM runs WHERE id=?", (run_id,)).fetchone()
        return self._run(row) if row else None

    def list_runs(self):
        """All searches, newest first."""
        with self.lock:
            rows = self.db.execute(f"SELECT {self._RUN_COLS} FROM runs ORDER BY id DESC").fetchall()
        return [self._run(r) for r in rows]

    def delete_run(self, run_id):
        """Forget a search. Only the history record goes; its results folder and photos are never touched."""
        with self.lock:
            self.db.execute("DELETE FROM runs WHERE id=?", (run_id,))
            self.db.execute("DELETE FROM verdicts WHERE run_id=?", (run_id,))
            self.db.commit()

    # ---- review: "yes, that's the person" / "no" per search ----------------------------------------
    VERDICTS = ("yes", "no")

    def set_verdicts(self, run_id, paths_, verdict):
        """Label photos of a search; verdict None clears the label. Only the record changes, never a file."""
        if verdict is not None and verdict not in self.VERDICTS:
            raise ValueError(f"unknown verdict {verdict!r}")
        with self.lock:
            for p in paths_:
                if verdict is None:
                    self.db.execute("DELETE FROM verdicts WHERE run_id=? AND path=?", (run_id, p))
                else:
                    self.db.execute("INSERT OR REPLACE INTO verdicts VALUES(?,?,?)", (run_id, p, verdict))
            self.db.commit()

    def verdicts(self, run_id):
        """{path: "yes"|"no"} for one search."""
        with self.lock:
            return dict(self.db.execute("SELECT path, verdict FROM verdicts WHERE run_id=?", (run_id,)).fetchall())

    def stats(self):
        with self.lock:
            return dict(self.db.execute("SELECT status, COUNT(*) FROM files GROUP BY status").fetchall())

    def paths_with_status(self, *statuses):
        marks = ",".join("?" * len(statuses))
        with self.lock:
            return self.db.execute(
                f"SELECT path, status FROM files WHERE status IN ({marks}) ORDER BY path", statuses).fetchall()
