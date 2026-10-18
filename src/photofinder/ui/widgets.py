"""Building blocks of the main window: step cards, a segmented control, a toast and the scan dashboard."""
import time
from collections import deque

from PySide6.QtGui import QPixmap
from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer, Signal
from PySide6.QtWidgets import (QButtonGroup, QFrame, QGraphicsOpacityEffect, QGridLayout, QHBoxLayout, QLabel,
                               QPushButton, QVBoxLayout, QWidget)

from ..i18n import tr
from . import icons
from .common import label


class StepCard(QFrame):
    """A numbered setup step. The number turns into a green tick once the step is complete."""

    def __init__(self, number, title, hint=""):
        super().__init__()
        self.setObjectName("card")
        self.number = number
        self.num = label(str(number), "stepnum")
        self.num.setAlignment(Qt.AlignCenter)
        self.title = label(title, "section")
        self.head = QHBoxLayout()
        self.head.setSpacing(10)
        self.head.addWidget(self.num)
        self.head.addWidget(self.title)
        self.head.addStretch(1)
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(14, 12, 14, 14)
        self.body.setSpacing(8)
        self.body.addLayout(self.head)
        self.hint = label(hint, "hint", wrap=True)
        if hint:
            self.body.addWidget(self.hint)

    def add_head_widget(self, w):
        self.head.addWidget(w)

    def set_done(self, done):
        if done:   # drawn tick: the ✓ glyph is missing from some fonts
            self.num.setText("")
            self.num.setPixmap(icons.pixmap("check", "#ffffff", 14))
        else:
            self.num.setPixmap(QPixmap())
            self.num.setText(str(self.number))
        self.num.setProperty("done", "true" if done else "false")
        self.num.style().unpolish(self.num)
        self.num.style().polish(self.num)


class Segmented(QFrame):
    """Row of exclusive choices (like iOS / macOS segmented controls). Emits the chosen key."""
    chosen = Signal(str)

    def __init__(self, options):
        super().__init__()
        self.setObjectName("segbar")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(3, 3, 3, 3)
        lay.setSpacing(2)
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.buttons = {}
        for key, text, tip in options:
            b = QPushButton(text)
            b.setObjectName("seg")
            b.setCheckable(True)
            b.setToolTip(tip)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, k=key: self.chosen.emit(k))
            self.group.addButton(b)
            self.buttons[key] = b
            lay.addWidget(b, 1)

    def set_current(self, key):
        """Check `key`, or nothing (custom values) when key is None."""
        self.group.setExclusive(False)
        for k, b in self.buttons.items():
            b.setChecked(k == key)
        self.group.setExclusive(True)


class Toast(QLabel):
    """Short message that floats over the bottom of its parent and fades away."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("toast")
        self.setAlignment(Qt.AlignCenter)
        self.setWordWrap(True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        self.anim = QPropertyAnimation(self.effect, b"opacity", self)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.finished.connect(lambda: self.hide() if self.effect.opacity() < 0.05 else None)
        self.timer = QTimer(self, singleShot=True)
        self.timer.timeout.connect(self._fade_out)
        self.hide()

    def show_text(self, text, ms=3800):
        self.setText(text)
        w = min(620, self.parent().width() - 40, self.fontMetrics().horizontalAdvance(text) + 60)
        self.setFixedWidth(max(120, w))
        self.setFixedHeight(self.heightForWidth(self.width()) + 8 if self.hasHeightForWidth() else self.sizeHint().height())
        self.reposition()
        self.show()
        self.raise_()
        self.anim.stop()
        self.anim.setDuration(180)
        self.anim.setStartValue(self.effect.opacity() if self.isVisible() else 0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()
        self.timer.start(ms)

    def reposition(self):
        p = self.parent()
        self.move((p.width() - self.width()) // 2, p.height() - self.height() - 84)   # above the selection bar

    def _fade_out(self):
        self.anim.stop()
        self.anim.setDuration(420)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.start()


def _fmt_duration(sec):
    if sec < 60:
        return tr("少過 1 分鐘")
    m = int(sec // 60)
    if m < 60:
        return tr("約 {m} 分鐘", m=m)
    return tr("約 {h} 小時 {m} 分", h=m // 60, m=m % 60)


class ScanPanel(QFrame):
    """Live dashboard while a search runs: progress, speed, time left and what was found so far."""

    def __init__(self, bar):
        super().__init__()
        self.setObjectName("scanpanel")
        self.bar = bar
        self.title = label("", "section")
        self.phase = label("", "hint", wrap=True)
        self.samples = deque()
        grid = QGridLayout()
        grid.setHorizontalSpacing(28)
        grid.setVerticalSpacing(0)
        self.stats = {}
        for col, (key, text) in enumerate((("done", tr("已處理")), ("speed", tr("速度")), ("eta", tr("尚餘時間")),
                                           ("found", tr("搵到")))):
            val = label("–", "bignum")
            grid.addWidget(val, 0, col)
            grid.addWidget(label(text, "statlabel"), 1, col)
            self.stats[key] = val
        grid.setColumnStretch(4, 1)
        top = QHBoxLayout()
        top.addWidget(self.title)
        top.addStretch(1)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 14, 18, 16)
        lay.setSpacing(8)
        lay.addLayout(top)
        lay.addWidget(self.phase)
        lay.addWidget(bar)
        lay.addSpacing(4)
        lay.addLayout(grid)
        self.hide()

    def start(self, title):
        self.samples.clear()
        self.title.setText(title)
        self.phase.setText("")
        for v in self.stats.values():
            v.setText("–")
        self.bar.setMaximum(0)
        self.show()

    def set_phase(self, text):
        self.samples.clear()   # copying known matches and scanning new photos run at very different speeds
        self.phase.setText(text)

    def progress(self, i, total):
        if total == 0:
            self.bar.setMaximum(0)
            self.stats["done"].setText(tr("列出相片中…"))
            return
        self.bar.setMaximum(total)
        self.bar.setValue(i)
        self.stats["done"].setText(f"{i:,} / {total:,}")
        now = time.monotonic()
        self.samples.append((now, i))
        while len(self.samples) > 2 and now - self.samples[0][0] > 20:   # speed over the last ~20 s
            self.samples.popleft()
        t0, i0 = self.samples[0]
        if now - t0 >= 1.5 and i > i0:
            rate = (i - i0) / (now - t0)
            self.stats["speed"].setText(tr("{r} 張/秒", r=f"{rate:.1f}"))
            self.stats["eta"].setText(_fmt_duration((total - i) / rate))

    def set_found(self, confirmed, maybe):
        self.stats["found"].setText(f"{confirmed} + {maybe}")
        self.stats["found"].setToolTip(tr("{a} 張確認 + {b} 張待你確認", a=confirmed, b=maybe))

    def finish(self, title, phase):
        self.title.setText(title)
        self.phase.setText(phase)
        self.stats["speed"].setText("–")
        self.stats["eta"].setText("–")
        if self.bar.maximum() == 0:
            self.bar.setMaximum(1)
        self.bar.setValue(self.bar.maximum())


class DropVeil(QLabel):
    """Shown over the window while files are dragged onto it."""

    def __init__(self, parent):
        super().__init__(tr("放開以加入\n資料夾 → 相片資料夾 · 相片 → 參考相"), parent)
        self.setObjectName("dropveil")
        self.setAlignment(Qt.AlignCenter)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.hide()

    def cover(self):
        p = self.parent()
        self.setGeometry(16, 16, p.width() - 32, p.height() - 32)
        self.show()
        self.raise_()


class Spacer(QWidget):
    def __init__(self, h=0, w=0):
        super().__init__()
        self.setFixedSize(w or 1, h or 1)
