"""Store screenshots (1920x1080), offscreen, synthetic gradient images only - no real photos or faces.
Usage: venv/Scripts/python.exe docs/store/make_screenshots.py OUT_PNG MODE(dark|light) LANG(zh|en) SCENARIO(empty|grid|scan|viewer)
All five at once: see docs/store/SUBMIT.md (Screenshots)."""
import json, os, sys, tempfile, time
from pathlib import Path

home = tempfile.mkdtemp()
os.environ["PHOTOFINDER_HOME"] = home
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
out, mode, lang, scen = sys.argv[1:5]
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
fake = lambda *p: "C:\\Users\\You\\Pictures\\" + "\\".join(p)  # display text only; these folders do not exist
json.dump({"theme": mode, "lang": lang, "thumb": 220,
           "folders": [fake("Family", "Trip 2019"), fake("Family", "Birthdays")] if scen != "empty" else [],
           "output": fake("PhotoFinder results")}, open(os.path.join(home, "settings.json"), "w"))
import numpy as np
from PIL import Image
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication
app = QApplication([])
for f in ("msjh.ttc", "msjhbd.ttc", "segoeui.ttf", "segoeuib.ttf", "seguiemj.ttf", "seguisym.ttf"):
    QFontDatabase.addApplicationFont("C:/Windows/Fonts/" + f)
app.setFont(QFont("Microsoft JhengHei UI", 10))
from photofinder import ui
w = ui.MainWindow(); w.resize(1920, 1080); w.show()


def pump(n=20, ms=0):
    end = time.time() + ms / 1000
    for _ in range(n): app.processEvents()
    while time.time() < end: app.processEvents(); time.sleep(0.01)


def make_image(i, size):
    wd, h = size
    a = np.linspace(0, 1, wd)[None, :, None] * np.array([(i * 37) % 255, 120, 255 - (i * 23) % 255])[None, None, :]
    b = np.linspace(0, 1, h)[:, None, None] * np.array([40, (i * 53) % 255, 90])[None, None, :]
    return Image.fromarray(np.clip(a + b, 0, 255).astype("uint8"))


def landscape(size):
    """Synthetic scenery (sky + hills), clearly not a person."""
    from PIL import ImageDraw
    wd, h = size
    sky = np.linspace(0, 1, h)[:, None, None] * np.array([[[250, 150, 90]]]) + (1 - np.linspace(0, 1, h)[:, None, None]) * np.array([[[40, 90, 200]]])
    im = Image.fromarray(np.repeat(sky, wd, axis=1).astype("uint8")); dr = ImageDraw.Draw(im)
    dr.ellipse((wd * .68, h * .22, wd * .68 + 120, h * .22 + 120), fill=(255, 236, 170))
    for k, (col, base) in enumerate([((70, 60, 120), .62), ((40, 80, 90), .72), ((20, 50, 60), .84)]):
        pts = [(0, h)] + [(x, h * base - 90 * abs(np.sin(x / 210 + k * 2))) for x in range(0, wd + 20, 20)] + [(wd, h)]
        dr.polygon(pts, fill=col)
    return im


pump(10, 600)
if scen != "empty":
    d = os.path.join(home, "imgs"); os.makedirs(d)
    paths = []
    for i in range(40):
        p = os.path.join(d, f"img_{i:02d}.png")
        make_image(i, (480, 360) if i % 3 else (360, 480)).save(p); paths.append(p)
    w.ref_paths, w.ref_counts, w.refs = paths[:5], [2] * 5, np.ones((10, 128), np.float32)
    w._update_refs_label()
    items = [(0.93 - i * 0.012, p) for i, p in enumerate(paths[:30])]
    w.grid_ok.set_items(items[:24]); w.grid_maybe.set_items([(0.45 - i * 0.01, p) for i, p in enumerate(paths[24:36])])
    w.grid_rej.set_items([(0.4, paths[36]), (0.52, paths[37])])
    w.verdicts = {paths[0]: "yes", paths[1]: "yes", paths[36]: "no"}
    w._set_tab_counts(24, 12, 2); w._update_steps()
    w.grid_ok.repaint_tiles()
    if scen == "scan":
        w.scan_panel.start("搜尋中…" if lang == "zh" else "Searching…")
        w.scan_panel.set_phase("掃描新相…可以隨時停止,下次會由停低嗰度繼續。" if lang == "zh" else "Scanning new photos… You can stop at any time and resume later.")
        w.scan_panel.progress(0, 5000); time.sleep(1.6); w.scan_panel.progress(1800, 5000)
        w.scan_panel.set_found(24, 12)
        w.bar.setValue(1800)
        w.set_busy(True)
    if scen in ("grid", "scan"):
        for i in (2, 3, 6): w.grid_ok.view.item(i).setSelected(True)
    if scen == "viewer":
        big = os.path.join(home, "big.png"); landscape((1600, 1000)).save(big)
        v = ui.ViewerDialog(w, [(0.91, big)] + items[1:6], {}, 0, verdicts={}, on_verdict=lambda p, v: None)
        v.path.setText(fake("Family", "Trip 2019", "IMG_0412.jpg"))
        v.resize(1920, 1080); v.show(); pump(30, 1500)
        v.grab().save(out); v.close(); w.close(); sys.exit(0)
pump(30, 1500)
w.grab().save(out)
w.close()
