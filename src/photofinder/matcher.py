"""Reference faces, scoring and tiers. A photo's score is its best-matching face."""
import json
import os

import cv2
import numpy as np

from . import paths
from .engine import EMB_DIM, iou
from .imageio import read_image

TIER_CONFIRMED = "confirmed"
TIER_MAYBE = "maybe"
DEFAULT_HIGH = 0.50  # confirmed
DEFAULT_LOW = 0.30   # needs your check


AUTO_MIN_SIM = 0.40     # a face must look at least this much like the existing references ...
AUTO_MARGIN = 0.10      # ... and beat the next face by this much, otherwise the user is asked
MIRROR_MIN_IOU = 0.30


def analyse_reference_images(engine, image_paths):
    """Detect faces in each reference image, and in its mirror image (done automatically).

    Returns (items, notes); item = {path, width, faces, flipped}, faces = [(box, score, emb)].
    Which face is the person is decided later (auto_pick or the user).
    """
    items, notes = [], []
    for p in image_paths:
        try:
            img = read_image(p)
        except Exception as e:  # OSError, cv2.error (empty or damaged file), PIL errors: skip this one image
            notes.append(f"{p}: read failed ({e})")
            continue
        if img is None:
            notes.append(f"{p}: cannot decode")
            continue
        faces = engine.faces(img)
        if not faces:
            notes.append(f"{p}: no face found")
            continue
        items.append({"path": p, "width": img.shape[1], "faces": faces, "flipped": engine.faces(cv2.flip(img, 1))})
    return items, notes


def auto_pick(faces, existing=None):
    """Index of the face to use, or None when the user must choose.

    One face: that one. Several faces: only if the references we already have clearly single one out.
    """
    if len(faces) == 1:
        return 0
    if existing is None or len(existing) == 0:
        return None
    sims = [float((np.asarray(existing, np.float32) @ f[2]).max()) for f in faces]
    order = sorted(range(len(faces)), key=lambda i: -sims[i])
    if sims[order[0]] >= AUTO_MIN_SIM and sims[order[0]] - sims[order[1]] >= AUTO_MARGIN:
        return order[0]
    return None


def mirror_embedding(box, flipped_faces, width):
    """Embedding of the mirrored copy of the chosen face (matched by overlap), or None."""
    x, y, w, h = box
    mirrored = (width - x - w, y, w, h)
    best, best_iou = None, MIRROR_MIN_IOU
    for fbox, _score, emb in flipped_faces:
        v = iou(mirrored, fbox)
        if v >= best_iou:
            best, best_iou = emb, v
    return best


def _under(path, prefixes):
    return os.path.normcase(os.path.normpath(path)).startswith(prefixes)


def score_photos(index, refs, folders=None):
    """([(cosine_score, path)] highest first, {path: best face box}).

    `folders` (when non-empty) limits the results to photos inside those folders. The folder name is
    matched as a whole path part, so F:\\Photos\\Trip does not pick up F:\\Photos\\Trips.
    """
    paths_, mat, boxes = index.embeddings()
    if len(paths_) == 0 or len(refs) == 0:
        return [], {}
    sims = (mat @ np.asarray(refs, np.float32).T).max(axis=1)
    prefixes = tuple(os.path.normcase(os.path.normpath(f)).rstrip("\\/") + os.sep for f in folders) if folders else None
    best, best_box = {}, {}
    for p, s, b in zip(paths_, sims, boxes):
        if prefixes is not None and not _under(p, prefixes):
            continue
        s = float(s)
        if p not in best or s > best[p]:
            best[p], best_box[p] = s, b
    return sorted(((s, p) for p, s in best.items()), reverse=True), best_box


def tier_of(score, low=DEFAULT_LOW, high=DEFAULT_HIGH):
    if score >= high:
        return TIER_CONFIRMED
    if score >= low:
        return TIER_MAYBE
    return None


def split_tiers(results, low=DEFAULT_LOW, high=DEFAULT_HIGH):
    confirmed = [(s, p) for s, p in results if s >= high]
    maybe = [(s, p) for s, p in results if low <= s < high]
    return confirmed, maybe


def apply_verdicts(results, verdicts, low=DEFAULT_LOW, high=DEFAULT_HIGH):
    """(confirmed, maybe, rejected) after the user's review.

    "yes" moves a photo to confirmed whatever its score; "no" moves it to rejected; unreviewed photos
    keep their tier. Only display and the final export use this; scanning and live copies do not.
    """
    confirmed, maybe, rejected = [], [], []
    for s, p in results:
        v = verdicts.get(p)
        if v == "no":
            rejected.append((s, p))
        elif v == "yes" or s >= high:
            confirmed.append((s, p))
        elif s >= low:
            maybe.append((s, p))
    return confirmed, maybe, rejected


def remove_reference(image_paths, counts, matrix, i):
    """Drop reference image i (and the face vectors it contributed) from the reference set.

    Only the app's reference list changes; the photo file itself is never touched.
    Returns (paths, counts, matrix).
    """
    start = sum(counts[:i])
    keep = np.ones(len(matrix), bool)
    keep[start:start + counts[i]] = False
    return image_paths[:i] + image_paths[i + 1:], counts[:i] + counts[i + 1:], matrix[keep]


def save_refs(image_paths, counts, matrix, home=None):
    """Reference set: one vector row group per image; counts[i] = rows contributed by image i."""
    home = home or paths.app_home()
    home.mkdir(parents=True, exist_ok=True)
    np.save(home / "refs.npy", matrix)
    with open(home / "refs.json", "w", encoding="utf-8") as f:
        json.dump({"images": [{"path": p, "rows": n} for p, n in zip(image_paths, counts)]}, f, ensure_ascii=False)


def load_refs(home=None):
    """(paths, counts, matrix); an unreadable or inconsistent reference set loads as empty."""
    home = home or paths.app_home()
    empty = ([], [], np.zeros((0, EMB_DIM), np.float32))
    try:
        mat = np.load(home / "refs.npy").astype(np.float32)
        with open(home / "refs.json", encoding="utf-8") as f:
            images = json.load(f)["images"]
        image_paths, counts = [d["path"] for d in images], [int(d["rows"]) for d in images]
    except (OSError, ValueError, KeyError, TypeError):
        return empty
    if mat.ndim != 2 or mat.shape[1] != EMB_DIM or sum(counts) != len(mat):
        return empty
    return image_paths, counts, mat
