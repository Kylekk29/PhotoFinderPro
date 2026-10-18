"""Read-only image decoding. Source photos are only ever opened in binary read mode."""
import os

import cv2
import numpy as np

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
UNSUPPORTED_EXTS = {".tif", ".tiff"}
HEIF_EXTS = {".heic", ".heif"}
try:
    import pi_heif
    pi_heif.register_heif_opener()  # lets PIL (decoding, thumbnails) open HEIC too
    SUPPORTED_EXTS |= HEIF_EXTS
except ImportError:
    UNSUPPORTED_EXTS |= HEIF_EXTS


def read_image(path):
    """Decode an image to BGR from a read-only handle (works with non-ASCII paths)."""
    if os.path.splitext(str(path))[1].lower() in HEIF_EXTS:
        from PIL import Image, ImageOps
        with Image.open(path) as im:  # PIL opens read-only
            rgb = np.asarray(ImageOps.exif_transpose(im).convert("RGB"))
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    with open(path, "rb") as f:
        data = np.frombuffer(f.read(), np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)
