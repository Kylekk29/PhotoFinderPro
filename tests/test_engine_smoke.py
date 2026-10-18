"""Loads the real YuNet + SFace models. Uses only synthetic images (no real faces, no personal photos)."""
import numpy as np

from photofinder.engine import FaceEngine, ENGINE_VERSION
from photofinder import paths


def test_model_files_exist():
    assert (paths.model_dir() / "yunet.onnx").stat().st_size > 100_000
    assert (paths.model_dir() / "sface.onnx").stat().st_size > 1_000_000


def test_engine_runs_on_synthetic_images_and_finds_no_face():
    eng = FaceEngine()
    assert eng.version == ENGINE_VERSION
    rng = np.random.default_rng(0)
    for img in (np.zeros((200, 300, 3), np.uint8),
                rng.integers(0, 255, (480, 640, 3), dtype=np.uint8),
                np.full((3000, 2000, 3), 128, np.uint8)):  # large: exercises the two-scale path
        assert eng.faces(img) == []
