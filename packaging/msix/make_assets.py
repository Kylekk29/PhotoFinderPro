"""Generate the MSIX visual assets from src/photofinder/assets/app.png (Pillow, no other deps).
Usage: venv/Scripts/python.exe packaging/msix/make_assets.py [out_dir]   (default: packaging/msix/Assets)
Outputs are committed so the build does not depend on running this."""
import sys
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
SRC = HERE.parents[1] / "src" / "photofinder" / "assets" / "app.png"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "Assets"


def icon(size, fill=1.0):
    """The app icon scaled (aspect kept) to fill*size, centred on a transparent square."""
    base = Image.open(SRC).convert("RGBA")
    s = max(1, round(size * fill))
    im = base.resize((s, s), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(im, ((size - s) // 2, (size - s) // 2), im)
    return canvas


def on_canvas(w, h, fill):
    """Icon (square, height = fill*h) centred on a transparent w x h canvas."""
    ic = icon(round(h * fill))
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    canvas.paste(ic, ((w - ic.width) // 2, (h - ic.height) // 2), ic)
    return canvas


def save(im, name):
    OUT.mkdir(parents=True, exist_ok=True)
    im.save(OUT / name, optimize=True)


def main():
    # App list / taskbar icons: edge-to-edge (the system plates them).
    for sz in (16, 24, 32, 48, 256):
        save(icon(sz), f"Square44x44Logo.targetsize-{sz}.png")
        save(icon(sz), f"Square44x44Logo.targetsize-{sz}_altform-unplated.png")
    save(icon(44), "Square44x44Logo.scale-100.png")
    save(icon(88), "Square44x44Logo.scale-200.png")
    # Medium tile 150x150: icon at ~70% so it breathes inside the tile.
    save(on_canvas(150, 150, 0.7), "Square150x150Logo.scale-100.png")
    save(on_canvas(300, 300, 0.7), "Square150x150Logo.scale-200.png")
    # Wide tile 310x150.
    save(on_canvas(310, 150, 0.7), "Wide310x150Logo.scale-100.png")
    save(on_canvas(620, 300, 0.7), "Wide310x150Logo.scale-200.png")
    # Store logo 50x50 (+ scales).
    save(icon(50), "StoreLogo.scale-100.png")
    save(icon(100), "StoreLogo.scale-200.png")
    # Splash 620x300 (+ 200 scale), transparent background (BackgroundColor from manifest).
    save(on_canvas(620, 300, 0.6), "SplashScreen.scale-100.png")
    save(on_canvas(1240, 600, 0.6), "SplashScreen.scale-200.png")
    # Unqualified base files: the manifest references these names and makeappx requires them to exist.
    save(icon(44), "Square44x44Logo.png")
    save(on_canvas(150, 150, 0.7), "Square150x150Logo.png")
    save(on_canvas(310, 150, 0.7), "Wide310x150Logo.png")
    save(icon(50), "StoreLogo.png")
    save(on_canvas(620, 300, 0.6), "SplashScreen.png")
    print("assets ->", OUT, len(list(OUT.glob('*.png'))), "files")


main()
