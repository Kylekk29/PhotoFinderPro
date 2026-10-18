"""Small helpers shared by the UI modules."""
import numpy as np
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import QLabel, QPushButton

from .. import theme
from . import icons

FONT = "Microsoft YaHei UI"
THUMB_PX = 400   # thumbnails are built at this size once, tiles of any zoom level scale them down
PER_PAGE = 120
AVATAR = 54
APP = "Photo Finder Pro"


def pil_to_qimage(im):
    im = im.convert("RGBA")
    return QImage(np.asarray(im).tobytes(), im.width, im.height, im.width * 4, QImage.Format_RGBA8888).copy()


def label(text, name=None, wrap=False):
    lab = QLabel(text)
    if name:
        lab.setObjectName(name)
    lab.setWordWrap(wrap)
    return lab


def button(text="", name=None, icon=None, color=None, tip=None, size=16):
    """QPushButton with an optional object name (style) and a line icon tinted for the current theme."""
    b = QPushButton(text)
    if name:
        b.setObjectName(name)
    if icon:
        b.setProperty("icon_name", icon)
        b.setProperty("icon_color", color)
        b.setIcon(icons.icon(icon, color or theme.C["text"], size))
        b.setIconSize(QSize(size, size))
    if tip:
        b.setToolTip(tip)
    b.setCursor(Qt.PointingHandCursor)
    return b


def retint(widget):
    """Re-tint every themed button icon under `widget` after a theme change."""
    for b in widget.findChildren(QPushButton):
        name = b.property("icon_name")
        if name:
            b.setIcon(icons.icon(name, b.property("icon_color") or theme.C["text"], b.iconSize().width() or 16))


def circle(qimg, size=AVATAR):
    """Round avatar cropped from the centre of an image (a plain disc when there is no image yet)."""
    out = QPixmap(size * 2, size * 2)
    out.fill(Qt.transparent)
    p = QPainter(out)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    path = QPainterPath()
    path.addEllipse(2, 2, size * 2 - 4, size * 2 - 4)
    p.setClipPath(path)
    p.fillRect(0, 0, size * 2, size * 2, QColor(theme.C["thumb"]))
    if qimg is not None:
        pm = QPixmap.fromImage(qimg).scaled(size * 2, size * 2, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        p.drawPixmap((size * 2 - pm.width()) // 2, (size * 2 - pm.height()) // 2, pm)
    p.end()
    out.setDevicePixelRatio(2.0)
    return out
