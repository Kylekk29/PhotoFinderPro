import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

DIM = 128


def snap(p):
    """(sha256, mtime_ns, size) of a file, to prove it was not changed."""
    import hashlib
    import os
    st = os.stat(p)
    return hashlib.sha256(Path(p).read_bytes()).hexdigest(), st.st_mtime_ns, st.st_size


def vec(*pairs):
    """Unit 128-d vector from (index, value) pairs."""
    v = np.zeros(DIM, np.float32)
    for i, x in pairs:
        v[i] = x
    return v / np.linalg.norm(v)


# Colour value of a solid synthetic image -> fake face embedding (0 = no face).
REF = vec((0, 1.0))
FAKE = {
    5: [((10.0, 10.0, 40.0, 40.0), 0.99, REF)],                        # same as reference: score 1.0
    6: [((10.0, 10.0, 40.0, 40.0), 0.99, vec((0, 0.4), (1, 0.9)))],     # about 0.40 -> "maybe"
    7: [((10.0, 10.0, 40.0, 40.0), 0.99, vec((2, 1.0)))],               # orthogonal: no match
    0: [],                                                              # no face
}


class FakeEngine:
    """Deterministic stand-in for FaceEngine: the top-left pixel value picks the faces."""
    version = "fake/v1"

    def __init__(self):
        self.calls = 0

    def faces(self, img):
        self.calls += 1
        return FAKE[int(img[0, 0, 0])]


@pytest.fixture
def home(tmp_path, monkeypatch):
    h = tmp_path / "home"
    monkeypatch.setenv("PHOTOFINDER_HOME", str(h))
    return h


@pytest.fixture
def make_photo(tmp_path):
    def _make(folder, name, value, size=(64, 64)):
        d = tmp_path / folder
        d.mkdir(parents=True, exist_ok=True)
        p = d / name
        Image.new("RGB", size, (value, value, value)).save(p)  # PNG: exact pixel values
        return p
    return _make
