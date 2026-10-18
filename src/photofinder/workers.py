"""Background workers: heavy work never runs on the UI thread."""
import threading

import numpy as np
from PySide6.QtCore import QObject, QRunnable, QThread, Signal
from PySide6.QtGui import QImage

from . import copier, matcher, scanner, thumbs
from .i18n import tr


class ScanWorker(QThread):
    """One search: first copy the matches among photos that are already scanned (so a new search over
    scanned folders is almost instant and its folder is complete), then scan the rest."""
    progress = Signal(int, int, str)
    matched = Signal(str, float, str, object)   # tier, score, path, face box
    phase = Signal(str)
    done = Signal(dict)
    failed = Signal(str)

    def __init__(self, folders, index, engine, refs, low, high, out_root):
        super().__init__()
        self.folders, self.index, self.engine = folders, index, engine
        self.refs, self.low, self.high, self.out_root = refs, low, high, out_root
        self.stop_event = threading.Event()

    def stop(self):
        self.stop_event.set()

    def run(self):
        try:
            live = copier.LiveCopier(self.refs, self.low, self.high, self.out_root, self.folders,
                                     on_match=lambda *a: self.matched.emit(*a))
            try:
                results, boxes = matcher.score_photos(self.index, self.refs, self.folders)
                known = [(s, p) for s, p in results if s >= self.low]
                if known:
                    self.phase.emit(tr("先複製已掃描過嘅 {n} 張符合嘅相…", n=len(known)))
                    live.copy_existing(known, boxes, self.stop_event,
                                       progress_cb=lambda *a: self.progress.emit(*a))
                self.phase.emit(tr("掃描新相…可以隨時停止,下次會由停低嗰度繼續。"))
                res = scanner.scan([(f, True) for f in self.folders], self.index, self.engine,
                                   progress_cb=lambda *a: self.progress.emit(*a),
                                   stop_event=self.stop_event, on_result=live)
            except copier.DiskLow:
                res = {"total": 0, "scanned": 0, "skipped": 0, "failed": 0, "disk_low": True, "stopped": False}
            finally:
                live.close()
            res["copied"] = dict(live.counts)
            self.done.emit(res)
        except Exception as e:
            self.failed.emit(str(e))


class RefWorker(QThread):
    """Finds the faces in the reference images (and their mirror images). Choosing which face is the
    person happens afterwards on the UI thread, because it may need to ask the user."""
    done = Signal(list, list)   # items, notes
    failed = Signal(str)

    def __init__(self, engine, image_paths):
        super().__init__()
        self.engine, self.image_paths = engine, image_paths

    def run(self):
        try:
            items, notes = matcher.analyse_reference_images(self.engine, self.image_paths)
            self.done.emit(items, notes)
        except Exception as e:
            self.failed.emit(str(e))


class CopyWorker(QThread):
    progress = Signal(int, int, str)
    done = Signal(dict, str)
    failed = Signal(str)

    def __init__(self, confirmed, maybe, out_root, folders):
        super().__init__()
        self.confirmed, self.maybe, self.out_root, self.folders = confirmed, maybe, out_root, folders
        self.stop_event = threading.Event()

    def stop(self):
        self.stop_event.set()

    def run(self):
        try:
            counts, log = copier.copy_tiers(self.confirmed, self.maybe, self.out_root, self.folders,
                                            progress_cb=lambda *a: self.progress.emit(*a),
                                            stop_event=self.stop_event)
            self.done.emit(counts, str(log))
        except Exception as e:
            self.failed.emit(str(e))


class ExportWorker(QThread):
    """Copies the reviewed final set into <search>/final/."""
    progress = Signal(int, int, str)
    done = Signal(dict, str)
    failed = Signal(str)

    def __init__(self, items, run_dir, folders):
        super().__init__()
        self.items, self.run_dir, self.folders = items, run_dir, folders
        self.stop_event = threading.Event()

    def stop(self):
        self.stop_event.set()

    def run(self):
        try:
            counts, log = copier.export_final(self.items, self.run_dir, self.folders,
                                              progress_cb=lambda *a: self.progress.emit(*a),
                                              stop_event=self.stop_event)
            self.done.emit(counts, str(log))
        except Exception as e:
            self.failed.emit(str(e))


class _ThumbSignals(QObject):
    ready = Signal(str, QImage)


class ThumbTask(QRunnable):
    """Builds one thumbnail off the UI thread; the UI turns the QImage into a pixmap."""

    def __init__(self, path, size, box, signals, square=False):
        super().__init__()
        self.path, self.size, self.box, self.signals, self.square = path, size, box, signals, square

    def run(self):
        try:
            im = (thumbs.face_tile(self.path, self.size, self.box) if self.square
                  else thumbs.thumbnail(self.path, self.size, self.box)).convert("RGBA")
        except Exception:
            im = thumbs.Image.new("RGBA", (self.size, self.size), (90, 90, 90, 255))
        data = np.asarray(im).tobytes()
        qimg = QImage(data, im.width, im.height, im.width * 4, QImage.Format_RGBA8888).copy()
        self.signals.ready.emit(self.path, qimg)


def make_thumb_signals():
    return _ThumbSignals()
