"""Searches ("runs"): own results folder, own references, history, and no re-scan needed for a new search."""
import json
import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pytest
from PySide6.QtWidgets import QApplication

from conftest import FakeEngine, REF
from photofinder import copier, index as index_mod, matcher, settings

OTHER_REF = np.zeros(128, np.float32)
OTHER_REF[2] = 1.0   # matches the "7" photos in the fake engine


def _wait(app, cond, ms=15000):
    end = time.time() + ms / 1000
    while time.time() < end and not cond():
        app.processEvents()
        time.sleep(0.01)
    return cond()


def _scan_in_window(app, win):
    win.start_scan()
    assert _wait(app, lambda: win.worker is not None and win.worker.isFinished())
    app.processEvents()


def _window(tmp_path, home, refs):
    from photofinder import ui
    app = QApplication.instance() or QApplication([])
    win = ui.MainWindow()
    win._engine = FakeEngine()
    win.refs, win.ref_paths, win.ref_counts = np.vstack(refs), ["ref.png"], [len(refs)]
    win._add_folder_item(str(tmp_path / "trip"))
    win.out_edit.setText(str(tmp_path / "found"))
    return app, win


def test_run_folder_name_is_safe_unique_and_never_reused(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    a = copier.new_run_dir(out, 'Gong: "Gong"/<x>?*. ')
    b = copier.new_run_dir(out, 'Gong: "Gong"/<x>?*. ')
    assert a != b and a.is_dir() and b.is_dir() and a.parent == out
    assert not set('<>:"/\\|?*') & set(a.name) and not a.name.endswith((".", " "))
    assert copier.safe_name("") == "搜尋" and copier.safe_name("???") == "搜尋"
    assert len(copier.safe_name("x" * 500)) == 60


def test_each_search_gets_its_own_folder_and_a_second_search_over_scanned_photos_is_filled(tmp_path, make_photo, home):
    make_photo("trip", "a.png", 5)
    make_photo("trip", "b.png", 7)
    app, win = _window(tmp_path, home, [REF])
    win.name_edit.setText("公公")
    _scan_in_window(app, win)
    run1 = win.run["run_dir"]
    assert (tmp_path / "found" / os.path.basename(run1) / "confirmed" / "trip" / "a.png").exists()
    assert os.path.basename(run1).endswith("公公")
    # a different person over the SAME, already scanned folder: nothing is re-scanned, yet the folder is filled
    win.new_search()
    assert win.run is None and len(win.refs) == 0
    win.refs, win.ref_paths, win.ref_counts = np.vstack([OTHER_REF]), ["other.png"], [1]
    win.name_edit.setText("第二個人")
    eng = win._engine
    calls_before = eng.calls
    _scan_in_window(app, win)
    run2 = win.run["run_dir"]
    assert run2 != run1 and eng.calls == calls_before                       # no photo was analysed again
    assert (tmp_path / "found" / os.path.basename(run2) / "confirmed" / "trip" / "b.png").exists()
    assert not (tmp_path / "found" / os.path.basename(run2) / "confirmed" / "trip" / "a.png").exists()
    assert (tmp_path / "found" / os.path.basename(run1) / "live_copy_log.csv").exists()
    assert (tmp_path / "found" / os.path.basename(run2) / "live_copy_log.csv").exists()
    win.close()


def test_start_on_an_open_search_continues_in_the_same_folder(tmp_path, make_photo, home):
    make_photo("trip", "a.png", 5)
    app, win = _window(tmp_path, home, [REF])
    _scan_in_window(app, win)
    folder = win.run["run_dir"]
    make_photo("trip", "c.png", 5)                                           # a new photo appears
    _scan_in_window(app, win)
    assert win.run["run_dir"] == folder
    assert sorted(os.listdir(tmp_path / "found")) == [os.path.basename(folder)]   # still one folder
    assert (tmp_path / "found" / os.path.basename(folder) / "confirmed" / "trip" / "c.png").exists()
    win.close()


def test_run_json_has_no_face_vectors(tmp_path, make_photo, home):
    make_photo("trip", "a.png", 5)
    app, win = _window(tmp_path, home, [REF])
    win.name_edit.setText("公公")
    _scan_in_window(app, win)
    text = (tmp_path / "found" / os.path.basename(win.run["run_dir"]) / "run.json").read_text(encoding="utf-8")
    data = json.loads(text)
    assert data["name"] == "公公" and data["confirmed"] == 1 and data["finished"] is True
    assert "emb" not in text and "vector" not in text and len(text) < 2000
    assert not any(isinstance(v, list) and v and isinstance(v[0], float) for v in data.values())
    win.close()


def test_history_lists_filters_reopens_with_own_references_and_forget_keeps_files(tmp_path, make_photo, home, monkeypatch):
    from photofinder import ui
    make_photo("trip", "a.png", 5)
    make_photo("trip", "b.png", 7)
    app, win = _window(tmp_path, home, [REF])
    win.name_edit.setText("公公")
    _scan_in_window(app, win)
    run1 = win.run["id"]
    win.new_search()
    win.refs, win.ref_paths, win.ref_counts = np.vstack([OTHER_REF]), ["other.png"], [1]
    win.name_edit.setText("阿嬸")
    _scan_in_window(app, win)
    run2 = win.run["id"]
    assert [r["id"] for r in win.index.list_runs()] == [run2, run1]            # newest first
    h = win.history
    assert h.list.count() == 2
    h.filter.setText("公公")
    assert h.list.count() == 1 and h.list.item(0).data(ui.Qt.UserRole) == run1
    h.filter.setText("trip")                                                    # folders are searched too
    assert h.list.count() == 2
    h.filter.setText("")
    # reopen the first search: its own references and folders come back
    h.list.item(1).setSelected(True)
    win.open_selected_run()
    assert win.run["id"] == run1 and win.ref_paths == ["ref.png"] and float(win.refs[0] @ REF) > 0.99
    assert win.name_edit.text() == "公公" and win.folders() == [str(tmp_path / "trip")]
    assert len(win.grid_ok.items) == 1
    # forgetting a search only removes the record
    folder2 = win.index.get_run(run2)["run_dir"]
    h.list.item(0).setSelected(True)
    monkeypatch.setattr(ui.QMessageBox, "question", lambda *a, **k: ui.QMessageBox.Yes)
    win.forget_selected_run()
    assert [r["id"] for r in win.index.list_runs()] == [run1]
    assert os.path.isdir(folder2) and (tmp_path / "trip" / "a.png").exists()
    win.close()


def test_last_search_is_reopened_on_next_start(tmp_path, make_photo, home):
    from photofinder import ui
    make_photo("trip", "a.png", 5)
    app, win = _window(tmp_path, home, [REF])
    win.name_edit.setText("公公")
    _scan_in_window(app, win)
    rid = win.run["id"]
    win.close()
    win2 = ui.MainWindow()
    assert win2.run and win2.run["id"] == rid and win2.name_edit.text() == "公公" and len(win2.refs) == 1
    win2.close()


def test_old_global_references_still_load_as_the_new_search(home):
    """Migration: references saved before searches existed become the starting point of a new search."""
    from photofinder import ui
    QApplication.instance() or QApplication([])
    matcher.save_refs(["old.png"], [1], np.vstack([REF]))
    win = ui.MainWindow()
    assert win.run is None and win.ref_paths == ["old.png"] and len(win.refs) == 1
    win.close()


def test_index_runs_crud_and_rejects_unknown_fields(tmp_path):
    idx = index_mod.Index(tmp_path / "x.db")
    rid = idx.create_run("n", ["F:\\a"], "F:\\out\\r", 0.3, 0.5)
    idx.update_run(rid, name="m", confirmed=3, finished=1)
    r = idx.get_run(rid)
    assert (r["name"], r["confirmed"], r["finished"], r["folders"]) == ("m", 3, 1, ["F:\\a"])
    with pytest.raises(ValueError):
        idx.update_run(rid, run_dir="x")
    idx.delete_run(rid)
    assert idx.get_run(rid) is None and idx.list_runs() == []


def test_settings_last_run_is_validated(home):
    home.mkdir(parents=True, exist_ok=True)
    (home / "settings.json").write_text(json.dumps({"last_run": "x"}), encoding="utf-8")
    assert settings.load()["last_run"] is None
    (home / "settings.json").write_text(json.dumps({"last_run": 4}), encoding="utf-8")
    assert settings.load()["last_run"] == 4
