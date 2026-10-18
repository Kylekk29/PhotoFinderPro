"""Draws the app icon (assets/app.png, assets/app.ico) with Pillow. Run: python packaging/make_icon.py"""
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parents[1] / "src" / "photofinder" / "assets"
S = 4096  # supersampled canvas
BLUE, VIOLET = (0x4C, 0x8D, 0xFF), (0x8B, 0x5C, 0xF6)


def gradient(size):
    """Diagonal blue -> violet gradient."""
    small = Image.new("L", (256, 256))
    small.putdata([(x + y) // 2 for y in range(256) for x in range(256)])
    mask = small.resize((size, size), Image.BICUBIC)
    return Image.composite(Image.new("RGB", (size, size), VIOLET), Image.new("RGB", (size, size), BLUE), mask)


def draw():
    base = gradient(S).convert("RGBA")
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, S - 1, S - 1), radius=int(S * 0.225), fill=255)
    base.putalpha(m)
    fg = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(fg)
    cx, cy, r, ring = int(S * 0.45), int(S * 0.45), int(S * 0.27), int(S * 0.058)
    # handle
    a = (cx + int(r * 0.74), cy + int(r * 0.74)); b = (int(S * 0.80), int(S * 0.80))
    d.line((a, b), fill=(255, 255, 255, 255), width=int(S * 0.095))
    d.ellipse((b[0] - S * 0.0475, b[1] - S * 0.0475, b[0] + S * 0.0475, b[1] + S * 0.0475), fill=(255, 255, 255, 255))
    # lens: white ring, translucent inner disc, person silhouette
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, 255))
    ri = r - ring
    d.ellipse((cx - ri, cy - ri, cx + ri, cy + ri), fill=(255, 255, 255, 0))
    inner = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    di = ImageDraw.Draw(inner)
    di.ellipse((cx - ri, cy - ri, cx + ri, cy + ri), fill=(255, 255, 255, 46))
    hr = int(ri * 0.34)
    hy = cy - int(ri * 0.20)
    person = Image.new("L", (S, S), 0)
    dp = ImageDraw.Draw(person)
    dp.ellipse((cx - hr, hy - hr, cx + hr, hy + hr), fill=255)
    sw, top = int(ri * 0.74), hy + hr + int(ri * 0.10)
    dp.ellipse((cx - sw, top, cx + sw, top + 2 * int(ri * 0.78)), fill=255)
    clip = Image.new("L", (S, S), 0)
    ImageDraw.Draw(clip).ellipse((cx - ri, cy - ri, cx + ri, cy + ri), fill=255)
    person = ImageChops.multiply(person, clip)
    inner.paste((255, 255, 255, 255), mask=person)
    fg = Image.alpha_composite(inner, fg)
    # soft shadow under the glyph
    sh = Image.new("RGBA", (S, S), (30, 20, 90, 0))
    sh.putalpha(fg.getchannel("A").point(lambda v: int(v * 0.35)).filter(ImageFilter.GaussianBlur(S * 0.012)))
    sh = ImageChops.offset(sh, 0, int(S * 0.012))
    out = Image.alpha_composite(base, sh)
    out = Image.alpha_composite(out, fg)
    out.putalpha(ImageChops.multiply(out.getchannel("A"), m))
    return out


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    big = draw()
    big.resize((512, 512), Image.LANCZOS).save(OUT / "app.png")
    big.resize((256, 256), Image.LANCZOS).save(OUT / "app.ico", sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
    print("wrote", OUT / "app.png", OUT / "app.ico")
