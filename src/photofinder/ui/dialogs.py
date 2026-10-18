"""Face picker: a reference photo with several people shows numbered faces; the user clicks the person."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from .. import theme, thumbs
from ..i18n import tr
from .common import FONT, pil_to_qimage


class _ClickLabel(QLabel):
    def __init__(self, on_click):
        super().__init__()
        self._on_click = on_click

    def mousePressEvent(self, e):
        self._on_click(e.position().x(), e.position().y())


class FacePickerDialog(QDialog):
    def __init__(self, parent, path, boxes):
        super().__init__(parent)
        self.choice = None
        self.boxes = boxes
        self.setWindowTitle(tr("邊個係你要搵嘅人?"))
        self.setStyleSheet(theme.viewer_qss())
        im = thumbs.full_image(path)
        self.scale = min(1000 / im.width, 620 / im.height, 1.0)
        im = im.resize((max(1, int(im.width * self.scale)), max(1, int(im.height * self.scale))))
        pm = QPixmap.fromImage(pil_to_qimage(im))
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        f = QFont(FONT, 12)
        f.setBold(True)
        p.setFont(f)
        for n, (x, y, w, h) in enumerate(boxes, 1):
            x, y, w, h = (v * self.scale for v in (x, y, w, h))
            pen_col = QColor(theme.GOOD)
            p.setPen(pen_col)
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(int(x), int(y), int(w), int(h), 6, 6)
            p.setBrush(pen_col)
            p.setPen(Qt.NoPen)
            p.drawEllipse(int(x + w / 2 - 14), max(0, int(y) - 32), 28, 28)
            p.setPen(QColor("white"))
            p.drawText(int(x + w / 2 - 14), max(0, int(y) - 32), 28, 28, Qt.AlignCenter, str(n))
        p.end()
        self.label = _ClickLabel(self._clicked)
        self.label.setPixmap(pm)
        self.label.setFixedSize(pm.size())
        self.label.setCursor(Qt.PointingHandCursor)
        row = QHBoxLayout()
        row.addStretch(1)
        for n in range(1, len(boxes) + 1):
            b = QPushButton(tr("揀第 {n} 個", n=n))
            b.clicked.connect(lambda _=False, i=n - 1: self._pick(i))
            row.addWidget(b)
        skip = QPushButton(tr("略過呢張"))
        skip.clicked.connect(self.reject)
        row.addWidget(skip)
        row.addStretch(1)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(14)
        lay.addWidget(QLabel(tr("呢張相入面有幾個人。撳相上面嘅面,或者撳下面嘅掣,揀你要搵嗰個。"), alignment=Qt.AlignCenter))
        lay.addWidget(self.label, 0, Qt.AlignCenter)
        lay.addLayout(row)

    def _pick(self, i):
        self.choice = i
        self.accept()

    def _clicked(self, px, py):
        hits = [(w * h, i) for i, (x, y, w, h) in enumerate(self.boxes)
                if x * self.scale <= px <= (x + w) * self.scale and y * self.scale <= py <= (y + h) * self.scale]
        if hits:
            self._pick(min(hits)[1])  # the smallest box under the click
