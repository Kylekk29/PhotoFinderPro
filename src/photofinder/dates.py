"""Date a photo was taken: EXIF DateTimeOriginal, else DateTime, else the file's modified time. Read-only."""
import os
import re
import time

FMT = "%Y-%m-%d %H:%M:%S"
_EXIF = re.compile(r"^\s*(\d{4})[:\-](\d{2})[:\-](\d{2})[ T](\d{2}):(\d{2}):(\d{2})")


def parse_exif(value):
    """'2019:05:03 14:20:11' -> '2019-05-03 14:20:11'; None for junk such as '0000:00:00 00:00:00'."""
    if isinstance(value, bytes):
        value = value.decode("ascii", "ignore")
    m = _EXIF.match(value) if isinstance(value, str) else None
    if not m:
        return None
    y, mo, d, h, mi, s = (int(x) for x in m.groups())
    if not (1900 <= y <= 2200 and 1 <= mo <= 12 and 1 <= d <= 31 and h < 24 and mi < 60 and s < 60):
        return None
    return f"{y:04d}-{mo:02d}-{d:02d} {h:02d}:{mi:02d}:{s:02d}"


def exif_taken(path):
    """EXIF date text, or None. Opens the file read-only; Pillow only reads the header here."""
    try:
        from PIL import Image
        with Image.open(path) as im:
            exif = im.getexif()
            for tag, ifd in ((0x9003, 0x8769), (0x0132, None)):
                v = exif.get_ifd(ifd).get(tag) if ifd else exif.get(tag)
                t = parse_exif(v)
                if t:
                    return t
    except Exception:
        pass
    return None


def taken(path, mtime_ns=None):
    """'YYYY-MM-DD HH:MM:SS' (local time) for sorting and display."""
    t = exif_taken(path)
    if t:
        return t
    if mtime_ns is None:
        mtime_ns = os.stat(path).st_mtime_ns
    return time.strftime(FMT, time.localtime(mtime_ns / 1e9))
