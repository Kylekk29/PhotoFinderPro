"""YuNet detector + SFace recognizer. Tuned loose: prefer finding too many faces."""
import cv2
import numpy as np

from . import paths

EMB_DIM = 128
# Bump when detection/recognition behaviour changes: photos recorded as "no face" or "error"
# by an older version are re-checked on the next scan.
ENGINE_VERSION = "yunet+sface/ms1280-2560/v1"


def unit(v):
    v = np.asarray(v, dtype=np.float32).reshape(-1)
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


def iou(a, b):
    ax2, ay2, bx2, by2 = a[0] + a[2], a[1] + a[3], b[0] + b[2], b[1] + b[3]
    iw = min(ax2, bx2) - max(a[0], b[0])
    ih = min(ay2, by2) - max(a[1], b[1])
    if iw <= 0 or ih <= 0:
        return 0.0
    inter = iw * ih
    return inter / (a[2] * a[3] + b[2] * b[3] - inter)


class FaceEngine:
    version = ENGINE_VERSION

    def __init__(self, det_threshold=0.6, model_dir=None):
        mdir = model_dir or paths.model_dir()
        self.det = cv2.FaceDetectorYN.create(
            str(mdir / "yunet.onnx"), "", (320, 320), det_threshold, 0.3, 5000)
        self.rec = cv2.FaceRecognizerSF.create(str(mdir / "sface.onnx"), "")

    def _detect(self, img):
        h, w = img.shape[:2]
        self.det.setInputSize((w, h))
        _, faces = self.det.detect(img)
        return [] if faces is None else list(faces)

    def faces(self, img):
        """Return [(box_xywh_in_original_coords, det_score, unit_embedding)]."""
        h, w = img.shape[:2]
        longest = max(h, w)
        scales = [min(1.0, 1280 / longest)]
        if longest > 1280:
            scales.append(min(1.0, 2560 / longest))
        found = []
        for s in scales:
            small = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) if s < 1.0 else img
            for row in self._detect(small):
                row = np.array(row, dtype=np.float32)
                row[:14] /= s
                found.append(row)
        found.sort(key=lambda r: -float(r[14]))
        kept = []
        for row in found:
            if all(iou(row[:4], k[:4]) < 0.4 for k in kept):
                kept.append(row)
        out = []
        for row in kept:
            try:
                aligned = self.rec.alignCrop(img, row)
                emb = unit(self.rec.feature(aligned))
            except cv2.error:
                continue
            out.append((tuple(float(x) for x in row[:4]), float(row[14]), emb))
        return out
