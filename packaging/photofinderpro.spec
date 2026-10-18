# PyInstaller spec: onedir, windowed. Build with packaging\build.bat
import shutil
from pathlib import Path

from PyInstaller.utils.hooks import collect_dynamic_libs

ROOT = Path(SPECPATH).parent
SRC = ROOT / "src"
datas = [(str(ROOT / "models" / n), "models") for n in ("yunet.onnx", "sface.onnx")]
datas += [(str(f), "photofinder/assets") for f in (SRC / "photofinder" / "assets").glob("*") if f.is_file()]
binaries = collect_dynamic_libs("pi_heif")
EXCLUDES = ["tkinter", "pytest", "matplotlib", "scipy", "pandas", "IPython", "unittest", "PyInstaller",
            "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.Qt3DCore", "PySide6.QtQuick",
            "PySide6.QtQml", "PySide6.QtMultimedia", "PySide6.QtNetwork", "PySide6.QtSql", "PySide6.QtPdf",
            "PySide6.QtDesigner", "PySide6.QtCharts", "PySide6.QtDataVisualization"]

a = Analysis([str(ROOT / "packaging" / "launch.py")], pathex=[str(SRC)], binaries=binaries, datas=datas,
             hiddenimports=["pi_heif"], excludes=EXCLUDES, noarchive=False)
a.binaries = [b for b in a.binaries if "opengl32sw" not in b[0]]  # software-GL fallback (20 MB), unused by widgets
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="PhotoFinderPro", console=False,
          icon=str(SRC / "photofinder" / "assets" / "app.ico"),
          version=str(ROOT / "packaging" / "version_info.txt"), upx=False)
coll = COLLECT(exe, a.binaries, a.datas, name="PhotoFinderPro", upx=False)
for f in (ROOT / "THIRD_PARTY_NOTICES.txt", ROOT / "packaging" / "README_FOR_FRIENDS.txt"):  # next to the exe
    shutil.copy2(f, Path(DISTPATH) / "PhotoFinderPro" / f.name)
