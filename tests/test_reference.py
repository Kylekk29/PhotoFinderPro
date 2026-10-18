"""Reference photos: automatic mirror copy, and choosing the right face when a photo has several people."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PySide6.QtWidgets import QApplication

from conftest import FakeEngine, REF, vec
from photofinder import matcher

BOX = (10.0, 10.0, 40.0, 40.0)
OTHER = vec((3, 1.0))


def test_one_face_is_used_without_asking():
    assert matcher.auto_pick([(BOX, 0.9, REF)], None) == 0


def test_several_faces_and_no_references_means_ask():
    faces = [(BOX, 0.9, REF), (BOX, 0.9, OTHER)]
    assert matcher.auto_pick(faces, None) is None


def test_several_faces_picks_the_one_that_clearly_matches_existing_references():
    faces = [(BOX, 0.9, OTHER), (BOX, 0.9, REF)]
    assert matcher.auto_pick(faces, np.vstack([REF])) == 1


def test_unclear_match_means_ask():
    a, b = vec((0, 0.5), (1, 0.5)), vec((0, 0.5), (2, 0.5))  # both about 0.5 similar to REF: no clear winner
    assert matcher.auto_pick([(BOX, 0.9, a), (BOX, 0.9, b)], np.vstack([REF])) is None
    # clear winner but too dissimilar to the references: also ask
    far = vec((7, 1.0))
    assert matcher.auto_pick([(BOX, 0.9, far), (BOX, 0.9, OTHER)], np.vstack([REF])) is None


def test_mirror_embedding_matches_the_mirrored_box():
    flipped = [((14.0, 10.0, 40.0, 40.0), 0.9, OTHER), ((200.0, 10.0, 40.0, 40.0), 0.9, REF)]
    assert matcher.mirror_embedding(BOX, flipped, 64) is OTHER      # box mirrored in a 64 px wide image
    assert matcher.mirror_embedding(BOX, [((300.0, 0.0, 10.0, 10.0), 0.9, REF)], 64) is None


def test_analyse_reference_images_reports_faces_flipped_faces_and_no_face_notes(tmp_path, make_photo):
    ok, nofa = make_photo("r", "ok.png", 5), make_photo("r", "none.png", 0)
    items, notes = matcher.analyse_reference_images(FakeEngine(), [str(ok), str(nofa), str(tmp_path / "gone.png")])
    assert len(items) == 1 and items[0]["width"] == 64 and len(items[0]["faces"]) == 1
    assert len(items[0]["flipped"]) == 1
    assert len(notes) == 2


def test_remove_reference_drops_only_that_images_rows():
    a, b, c = vec((0, 1.0)), vec((1, 1.0)), vec((2, 1.0))
    mat = np.vstack([a, a, b, c, c])
    paths_, counts, out = matcher.remove_reference(["x", "y", "z"], [2, 1, 2], mat, 1)
    assert paths_ == ["x", "z"] and counts == [2, 2]
    assert out.shape == (4, 128) and float(out[2] @ c) > 0.99 and float(out[0] @ a) > 0.99
    paths_, counts, out = matcher.remove_reference(["x", "y", "z"], [2, 1, 2], mat, 0)
    assert paths_ == ["y", "z"] and out.shape == (3, 128) and float(out[0] @ b) > 0.99


def test_save_and_load_refs_roundtrip_and_inconsistent_loads_empty(tmp_path):
    mat = np.vstack([REF, OTHER, OTHER])
    matcher.save_refs(["a.png", "b.png"], [1, 2], mat, home=tmp_path)
    p, c, m = matcher.load_refs(home=tmp_path)
    assert p == ["a.png", "b.png"] and c == [1, 2] and m.shape == (3, 128)
    matcher.save_refs(["a.png"], [5], mat, home=tmp_path)   # counts do not add up to the rows
    assert matcher.load_refs(home=tmp_path)[0] == []


def test_window_removes_one_reference_but_never_the_photo_file(tmp_path, make_photo, home, monkeypatch):
    from photofinder import ui
    app = QApplication.instance() or QApplication([])
    f1, f2 = make_photo("refs", "one.png", 5), make_photo("refs", "two.png", 6)
    win = ui.MainWindow()
    win.ref_paths, win.ref_counts = [str(f1), str(f2)], [2, 1]
    win.refs = np.vstack([REF, REF, OTHER])
    win._update_refs_label()
    monkeypatch.setattr(ui.QMessageBox, "question", lambda *a, **k: ui.QMessageBox.Yes)
    win.avatars.item(0).setSelected(True)
    win.remove_selected_ref()
    assert win.ref_paths == [str(f2)] and win.ref_counts == [1] and len(win.refs) == 1
    assert f1.exists() and f2.exists()                         # photo files are untouched
    assert matcher.load_refs()[0] == [str(f2)]                 # and the change was saved
    win.avatars.item(0).setSelected(True)
    monkeypatch.setattr(ui.QMessageBox, "question", lambda *a, **k: ui.QMessageBox.No)
    win.remove_selected_ref()                                  # declined: nothing changes
    assert win.ref_paths == [str(f2)]
    win.close()


def test_adding_the_same_reference_twice_does_not_double_it(tmp_path, home):
    from photofinder import ui
    app = QApplication.instance() or QApplication([])
    win = ui.MainWindow()
    item = {"path": str(tmp_path / "r.png"), "width": 64, "faces": [(BOX, 0.9, REF)],
            "flipped": [((14.0, 10.0, 40.0, 40.0), 0.9, REF)]}
    win._refs_analysed([item], [])
    win._refs_analysed([item], [])
    assert win.ref_paths == [item["path"]] and win.ref_counts == [2] and len(win.refs) == 2
    win.close()


def test_window_adds_chosen_face_and_its_mirror(tmp_path, home):
    from photofinder import ui
    app = QApplication.instance() or QApplication([])
    win = ui.MainWindow()
    asked = []
    win._ask_face = lambda item: (asked.append(item["path"]), 1)[1]
    other_flipped = [((14.0, 10.0, 40.0, 40.0), 0.9, OTHER), ((14.0, 10.0, 40.0, 40.0), 0.9, REF)]
    item = {"path": str(tmp_path / "group.png"), "width": 64,
            "faces": [(BOX, 0.9, OTHER), (BOX, 0.9, REF)], "flipped": other_flipped}
    win._refs_analysed([item], [])
    assert asked == [item["path"]]                 # no references yet: the user was asked
    assert len(win.refs) == 2                      # chosen face + its mirror
    assert float(win.refs[0] @ REF) > 0.99
    win.close()
