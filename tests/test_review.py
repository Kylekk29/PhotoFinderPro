"""Review labels (Y / N), final export, settings validation, theme / language switches. Synthetic data only."""
import json
import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pytest
from PySide6.QtWidgets import QApplication

from conftest import REF, FakeEngine, snap
from photofinder import copier, i18n, matcher, settings, theme
from photofinder.index import Index


def _wait(app, cond, ms=15000):
    end = time.time() + ms / 1000
    while time.time() < end and not cond():
        app.processEvents()
        time.sleep(0.01)
    return cond()


def _scanned_window(tmp_path, make_photo, home, values=((5, "a.png"), (5, "b.png"), (6, "c.png"))):
    from photofinder import ui
    app = QApplication.instance() or QApplication([])
    photos = [make_photo("trip", name, v) for v, name in values]
    win = ui.MainWindow()
    win._engine = FakeEngine()
    win.refs, win.ref_paths, win.ref_counts = np.vstack([REF]), ["ref.png"], [1]
    win._add_folder_item(str(tmp_path / "trip"))
    win.out_edit.setText(str(tmp_path / "found"))
    win.name_edit.setText("test")
    win.start_scan()
    assert _wait(app, lambda: win.worker is not None and win.worker.isFinished())
    app.processEvents()
    return app, win, [str(p) for p in photos]


# ---- database / matcher ------------------------------------------------------------------------
def test_verdicts_set_clear_and_cleanup(home):
    ix = Index()
    r1 = ix.create_run("a", ["f"], "d1", 0.3, 0.5)
    r2 = ix.create_run("b", ["f"], "d2", 0.3, 0.5)
    ix.set_verdicts(r1, ["x", "y"], "no")
    ix.set_verdicts(r1, ["y"], "yes")          # replaces
    ix.set_verdicts(r2, ["x"], "yes")
    assert ix.verdicts(r1) == {"x": "no", "y": "yes"} and ix.verdicts(r2) == {"x": "yes"}
    ix.set_verdicts(r1, ["x"], None)           # clears
    assert ix.verdicts(r1) == {"y": "yes"}
    with pytest.raises(ValueError):
        ix.set_verdicts(r1, ["x"], "maybe")
    ix.delete_run(r1)
    assert ix.verdicts(r1) == {} and ix.verdicts(r2) == {"x": "yes"}
    ix.close()


def test_apply_verdicts_moves_between_tiers():
    results = [(0.9, "hi"), (0.4, "mid"), (0.1, "lo"), (0.8, "hi2"), (0.35, "mid2")]
    verdicts = {"hi": "no", "lo": "yes", "mid": "no", "bogus": "yes"}
    confirmed, maybe, rejected = matcher.apply_verdicts(results, verdicts, 0.3, 0.5)
    assert [p for _, p in confirmed] == ["lo", "hi2"]
    assert [p for _, p in maybe] == ["mid2"]
    assert [p for _, p in rejected] == ["hi", "mid"]
    assert matcher.apply_verdicts(results, {}, 0.3, 0.5)[2] == []


# ---- final export ------------------------------------------------------------------------------
def test_export_final_copies_only_and_never_overwrites(tmp_path, make_photo):
    a, b = make_photo("trip", "a.png", 5), make_photo("trip", "b.png", 6)
    before = {p: snap(p) for p in (a, b)}
    run_dir = tmp_path / "found" / "run"
    run_dir.mkdir(parents=True)
    counts, log = copier.export_final([(0.9, str(a)), (0.7, str(b))], run_dir, [str(tmp_path / "trip")])
    assert counts == {"copied": 2}
    finals = sorted((run_dir / "final").rglob("*.png"))
    assert len(finals) == 2 and os.path.isfile(log)
    assert {p: snap(p) for p in (a, b)} == before
    # again: identical copies are recognised, nothing is duplicated or rewritten
    stamp = {p: snap(p) for p in finals}
    counts2, _ = copier.export_final([(0.9, str(a)), (0.7, str(b))], run_dir, [str(tmp_path / "trip")])
    assert counts2 == {"already_there": 2} and {p: snap(p) for p in finals} == stamp
    assert len(list((run_dir / "final").rglob("*.png"))) == 2
    # a different file already sits at the destination: it stays, the new copy gets another name
    target = finals[0]
    target.write_bytes(b"not an image")
    held = snap(target)
    copier.export_final([(0.9, str(a)), (0.7, str(b))], run_dir, [str(tmp_path / "trip")])
    assert snap(target) == held and {p: snap(p) for p in (a, b)} == before
    assert len(list((run_dir / "final").rglob("*.png"))) == 3


def test_export_final_refuses_run_folder_inside_photos(tmp_path, make_photo):
    a = make_photo("trip", "a.png", 5)
    with pytest.raises(Exception):
        copier.export_final([(0.9, str(a))], tmp_path / "trip" / "run", [str(tmp_path / "trip")])
    assert not (tmp_path / "trip" / "run").exists()


# ---- window ------------------------------------------------------------------------------------
def test_verdict_moves_photo_to_excluded_and_survives_reopen(tmp_path, make_photo, home):
    from photofinder import ui
    app, win, photos = _scanned_window(tmp_path, make_photo, home)
    before = {p: snap(p) for p in photos}
    assert len(win.grid_ok.items) == 2 and len(win.grid_maybe.items) == 1 and not win.grid_rej.items
    a = photos[0]
    win.set_verdict(a, "no")
    assert [p for _, p in win.grid_rej.items] == [a] and len(win.grid_ok.items) == 1
    assert win.tabs.tabText(2).endswith("1") and win.tabs.tabText(0).endswith("1")
    win.set_verdicts([photos[2]], "yes")                      # a "maybe" confirmed by hand
    assert len(win.grid_ok.items) == 2 and not win.grid_maybe.items
    rid = win.run["id"]
    win.close()
    win2 = ui.MainWindow()                                   # last search reopens with its labels
    assert win2.run["id"] == rid and win2.verdicts == {a: "no", photos[2]: "yes"}
    assert [p for _, p in win2.grid_rej.items] == [a] and len(win2.grid_ok.items) == 2
    win2.set_verdict(a, None)
    assert not win2.grid_rej.items and len(win2.grid_ok.items) == 3
    assert {p: snap(p) for p in photos} == before             # labels never touch files
    win2.close()


def test_verdict_buttons_need_a_search_and_bulk_mark_clears_selection(tmp_path, make_photo, home):
    from photofinder import ui
    app = QApplication.instance() or QApplication([])
    win = ui.MainWindow()
    assert win.run is None and not win.b_yes.isEnabled() and win.b_yes.toolTip()
    win.set_verdict("x.png", "no")                            # no search: ignored
    assert win.verdicts == {}
    win.close()
    app, win, photos = _scanned_window(tmp_path, make_photo, home)
    assert win.b_yes.isEnabled() and win.b_no.isEnabled()
    win.grid_ok.view.selectAll()
    win.show()
    assert win.selbar.isVisible() and "2" in win.sel_label.text()
    win.b_no.click()
    assert len(win.grid_rej.items) == 2 and not win.grid_ok.items and win.selbar.isHidden()
    win.close()


def test_scan_routes_matches_by_verdict(tmp_path, make_photo, home):
    app, win, photos = _scanned_window(tmp_path, make_photo, home)
    win.set_verdict(photos[0], "no")
    win.start_scan()                                          # same search again: nothing new to scan
    assert _wait(app, lambda: win.worker.isFinished())
    app.processEvents()
    assert [p for _, p in win.grid_rej.items] == [photos[0]] and len(win.grid_ok.items) == 1
    win.close()


def test_export_final_from_window(tmp_path, make_photo, home, monkeypatch):
    from photofinder import ui
    app, win, photos = _scanned_window(tmp_path, make_photo, home)
    win.set_verdict(photos[0], "no")
    asked = []
    monkeypatch.setattr(ui.QMessageBox, "question", lambda *a, **k: (asked.append(a[2]), ui.QMessageBox.Yes)[1])
    monkeypatch.setattr(os, "startfile", lambda p: None, raising=False)
    win.export_final()
    assert "1" in asked[0] and "final" in asked[0]
    assert _wait(app, lambda: win.worker.isFinished())
    app.processEvents()
    final = os.path.join(win.run["run_dir"], "final")
    assert [f for _, _, fs in os.walk(final) for f in fs] == ["b.png"]
    assert win.b_start.isEnabled()
    win.close()


def test_export_final_needs_a_search(home, monkeypatch):
    from photofinder import ui
    QApplication.instance() or QApplication([])
    shown = []
    monkeypatch.setattr(ui.QMessageBox, "information", lambda *a, **k: shown.append(a[2]))
    win = ui.MainWindow()
    win.export_final()
    assert shown and win.worker is None
    win.close()


def test_viewer_judge_calls_on_verdict_and_undoes(tmp_path, make_photo, home):
    from photofinder import ui
    QApplication.instance() or QApplication([])
    a, b = make_photo("trip", "a.png", 5), make_photo("trip", "b.png", 6)
    got = []
    v = ui.ViewerDialog(None, [(0.9, str(a)), (0.6, str(b))], {}, 0, on_verdict=lambda p, x: got.append((p, x)))
    v._judge("yes")
    assert got == [(str(a), "yes")] and v.i == 1               # moved on to the next photo
    v._judge("no")
    v._step(-1)
    v._judge("yes")                                            # same label again undoes it
    assert got[-1] == (str(a), None)
    plain = ui.ViewerDialog(None, [(0.9, str(a))], {}, 0)     # no search open: no review buttons, no crash
    plain._judge("yes")
    assert plain.btn_yes.isHidden()


# ---- settings, theme, language -----------------------------------------------------------------
def test_settings_validate_theme_lang_thumb(home):
    c = settings._clean({"theme": "light", "lang": "en", "thumb": 240})
    assert (c["theme"], c["lang"], c["thumb"]) == ("light", "en", 240)
    for bad in ({"theme": "neon", "lang": "fr", "thumb": 9000}, {"theme": 3, "lang": None, "thumb": "x"},
                {"thumb": True}, {"thumb": 119}, {"thumb": 321}, "junk", None):
        c = settings._clean(bad)
        assert (c["theme"], c["lang"], c["thumb"]) == ("dark", "zh", 200)
    settings.save({**settings.DEFAULTS, "theme": "light", "thumb": 280})
    assert settings.load()["theme"] == "light" and settings.load()["thumb"] == 280


def test_theme_language_and_zoom_switches(tmp_path, make_photo, home):
    from photofinder import ui
    app, win, photos = _scanned_window(tmp_path, make_photo, home)
    try:
        win.show()
        app.processEvents()
        win.toggle_theme()
        assert theme.mode == "light" and settings.load()["theme"] == "light"
        win.toggle_theme()
        assert theme.mode == "dark"
        win.zoom.setValue(260)
        assert win.thumb_size == 260 and settings.load()["thumb"] == 260
        assert win.grid_ok.view.iconSize().width() == 260
        win.zoom.setValue(125)                                 # snaps to the 20 px steps
        assert win.zoom.value() % 20 == 0
        win.toggle_lang()                                      # applies after a restart, saved now
        assert settings.load()["lang"] == "en" and win.b_lang.text() == "中"
        win.high.setValue(60)
        win.low.setValue(40)
        assert win.presets.buttons["strict"].isChecked()
        win.low.setValue(33)
        assert not any(b.isChecked() for b in win.presets.buttons.values())
        win.close()
        en = ui.MainWindow()                                   # next start is English
        assert en.b_start.text() == "Start search" and en.tabs.tabText(0).startswith("Confirmed")
        en.close()
    finally:
        i18n.set_lang("zh")
        theme.set_mode("dark")


def test_drop_adds_folders_and_ignores_while_busy(tmp_path, home):
    from PySide6.QtCore import QMimeData, QUrl
    from photofinder import ui
    QApplication.instance() or QApplication([])
    folder = tmp_path / "pics"
    folder.mkdir()
    win = ui.MainWindow()
    md = QMimeData()
    md.setUrls([QUrl.fromLocalFile(str(folder))])
    assert win._droppable(type("E", (), {"mimeData": lambda self: md})())
    win._busy = True
    assert not win._droppable(type("E", (), {"mimeData": lambda self: md})())
    win._busy = False
    win.close()
