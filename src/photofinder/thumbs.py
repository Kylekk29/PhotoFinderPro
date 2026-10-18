"""Thumbnails and the green face frame. Photos are opened read-only; the cache lives in the app data folder."""
import hashlib
import io
import os

from PIL import Image, ImageDraw, ImageOps

from . import paths


def oriented_size(path):
    """Image size as displayed (EXIF rotation applied), from the header only."""
    with Image.open(path) as im:
        w, h = im.size
        if im.getexif().get(0x0112) in (5, 6, 7, 8):
            w, h = h, w
    return w, h


def draw_box(pil_img, box, full_size, color=(40, 200, 80), width=3):
    """Copy of pil_img with the face box drawn (box is in full-size coordinates)."""
    out = pil_img.copy()
    sx, sy = out.width / full_size[0], out.height / full_size[1]
    x, y, w, h = box
    ImageDraw.Draw(out).rectangle([x * sx, y * sy, (x + w) * sx, (y + h) * sy], outline=color, width=width)
    return out


def thumbnail(path, size=160, box=None):
    try:
        st = os.stat(path)
        key = hashlib.sha1(f"{path}|{st.st_mtime_ns}|{size}".encode("utf-8")).hexdigest()
        cache_file = paths.thumb_dir() / f"{key}.jpg"
        im = None
        if cache_file.exists():
            try:
                with Image.open(cache_file) as t:
                    im = t.convert("RGB")  # a truncated file raises here
            except Exception:
                im = None  # damaged cache entry (crash mid-write, two threads): rebuild it below
        if im is None:
            with Image.open(path) as src:
                src.draft("RGB", (size * 2, size * 2))
                im = ImageOps.exif_transpose(src).convert("RGB")
            im.thumbnail((size, size))
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=80)
            cache_file.write_bytes(buf.getvalue())  # one write call keeps the damaged-file window tiny
        if box is not None:
            im = draw_box(im, box, oriented_size(path), width=2)
        return im
    except Exception:
        return Image.new("RGB", (size, size), (90, 90, 90))


def face_tile(path, size=400, box=None):
    """Square thumbnail cropped around the matched face (centre crop without a face), face framed."""
    im = thumbnail(path, size)
    side = min(im.width, im.height)
    cx, cy = im.width / 2, im.height / 2
    sx = sy = 1.0
    if box is not None:
        try:
            fw, fh = oriented_size(path)
            sx, sy = im.width / fw, im.height / fh
            cx, cy = (box[0] + box[2] / 2) * sx, (box[1] + box[3] / 2) * sy
        except Exception:
            box = None
    left = int(min(max(cx - side / 2, 0), im.width - side))
    top = int(min(max(cy - side / 2, 0), im.height - side))
    out = im.crop((left, top, left + side, top + side))
    if box is not None:
        x, y, w, h = box[0] * sx - left, box[1] * sy - top, box[2] * sx, box[3] * sy
        ImageDraw.Draw(out).rounded_rectangle([x, y, x + w, y + h], radius=max(2, int(w / 8)),
                                              outline=(40, 210, 90), width=max(2, side // 130))
    return out


def full_image(path, box=None):
    """Full-size RGB image (EXIF-rotated) with the matched face framed."""
    with Image.open(path) as src:
        im = ImageOps.exif_transpose(src).convert("RGB")
    if box is not None:
        im = draw_box(im, box, im.size, width=max(3, im.width // 300))
    return im
