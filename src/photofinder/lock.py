"""Single-instance lock: only one Photo Finder window may write to the database at a time."""
import os
from pathlib import Path

try:
    import msvcrt
except ImportError:  # non-Windows
    msvcrt = None
    import fcntl


class SingleInstance:
    def __init__(self, path):
        self.path = Path(path)
        self._f = None

    def acquire(self):
        """True if this process now holds the lock, False if another instance has it."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        f = open(self.path, "a+b")
        try:
            if msvcrt is not None:
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            f.close()
            return False
        self._f = f
        return True

    def release(self):
        """Release the lock. The lock file itself is left in place (this app never deletes files)."""
        if self._f is None:
            return
        try:
            if msvcrt is not None:
                self._f.seek(0)
                msvcrt.locking(self._f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(self._f.fileno(), fcntl.LOCK_UN)
        finally:
            self._f.close()
            self._f = None
