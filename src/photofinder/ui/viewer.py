"""Large view of results, also used to review them fast: Y = it's the person, N = it's not, arrows move."""
import os
import subprocess

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout

from .. import theme, thumbs
from ..i18n import tr
from .common import button, label, pil_to_qimage


class ViewerDialog(QDialog):
    """`items` = [(score, path)]; `on_verdict(path, verdict)` is given when the open search can be reviewed."""

    def __init__(self, parent, items, boxes, start, verdicts=None, on_verdict=None, high=None, dates=None):
        super().__init__(parent)
        # Own copy: the grid keeps re-sorting its list while a scan adds matches; the viewer must not follow.
        self.items, self.boxes, self.i = list(items), boxes, start
        self.verdicts = dict(verdicts or {})
        self.dates = dict(dates or {})   # {path: 'YYYY-MM-DD HH:MM:SS'} known so far
        self.on_verdict, self.high = on_verdict, high
        self.show_box = True
        self.setWindowTitle(tr("檢視"))
        self.setStyleSheet(theme.viewer_qss())
        self.resize(1200, 860)

        self.count = label("", "vcount")
        self.pill = label("", "vpill")
        self.state = label("")
        self.b_box = button(tr("臉框"), icon="frame", color="#eef1f7", tip=tr("顯示 / 隱藏臉框 (F)"))
        self.b_box.setCheckable(True)
        self.b_box.setChecked(True)
        self.b_box.clicked.connect(self._toggle_box)
        b_show = button(tr("喺檔案總管顯示"), icon="open", color="#eef1f7", tip=tr("開啟相片所在資料夾(只係開啟,唔會改動)"))
        b_show.clicked.connect(self._reveal)
        top = QHBoxLayout()
        top.setContentsMargins(18, 14, 18, 6)
        top.setSpacing(10)
        for w in (self.count, self.pill, self.state):
            top.addWidget(w)
        top.addStretch(1)
        top.addWidget(self.b_box)
        top.addWidget(b_show)

        self.label = QLabel(alignment=Qt.AlignCenter)
        self.label.setMinimumSize(200, 200)
        self.path = label("", "vpath")
        self.path.setAlignment(Qt.AlignCenter)
        self.path.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.btn_prev = button(tr("上一張"), icon="chevron-left", color="#eef1f7", tip="←")
        self.btn_next = button(tr("下一張"), icon="chevron-right", color="#eef1f7", tip="→")
        self.btn_next.setLayoutDirection(Qt.RightToLeft)
        self.btn_no = button(tr("唔係佢  N"), "no", icon="x", color="#fca5a5", tip=tr("唔係要搵嘅人:由結果移走(檔案唔會刪除)"))
        self.btn_yes = button(tr("係佢  Y"), "yes", icon="check", color="#86efac", tip=tr("確認係要搵嘅人"))
        self.btn_prev.clicked.connect(lambda: self._step(-1))
        self.btn_next.clicked.connect(lambda: self._step(1))
        self.btn_yes.clicked.connect(lambda: self._judge("yes"))
        self.btn_no.clicked.connect(lambda: self._judge("no"))
        nav = QHBoxLayout()
        nav.setContentsMargins(18, 6, 18, 16)
        nav.setSpacing(10)
        nav.addWidget(self.btn_prev)
        nav.addStretch(1)
        nav.addWidget(self.btn_no)
        nav.addWidget(self.btn_yes)
        nav.addStretch(1)
        nav.addWidget(self.btn_next)
        for b in (self.btn_yes, self.btn_no):
            b.setVisible(on_verdict is not None)
            b.setMinimumWidth(150)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addLayout(top)
        lay.addWidget(self.label, 1)
        lay.addWidget(self.path)
        lay.addLayout(nav)
        self._pix = None
        self._load()

    def _step(self, d):
        n = self.i + d
        if 0 <= n < len(self.items):
            self.i = n
            self._load()

    def _judge(self, verdict):
        if self.on_verdict is None or not self.items:
            return
        path = self.items[self.i][1]
        verdict = None if self.verdicts.get(path) == verdict else verdict   # pressing it again undoes it
        self.verdicts[path] = verdict
        self.on_verdict(path, verdict)
        if verdict is not None and self.i < len(self.items) - 1:
            self._step(1)
        else:
            self._load()

    def _toggle_box(self):
        self.show_box = self.b_box.isChecked()
        self._load()

    def _reveal(self):
        path = os.path.normpath(self.items[self.i][1])
        try:
            subprocess.Popen(["explorer", "/select,", path])   # opens Explorer with the file selected; read-only
        except OSError:
            pass

    def _load(self):
        score, path = self.items[self.i]
        try:
            box = self.boxes.get(path) if self.show_box else None
            self._pix = QPixmap.fromImage(pil_to_qimage(thumbs.full_image(path, box)))
            self.label.setText("")
        except Exception as e:
            self._pix = None
            self.label.setText(tr("讀取失敗:{e}", e=e))
        self.count.setText(f"{self.i + 1} / {len(self.items)}")
        good = self.high is None or score >= self.high
        self.pill.setText(tr("相似度 {s}%", s=f"{score * 100:.0f}"))
        self.pill.setStyleSheet(f"background: {theme.GOOD if good else theme.WARN};")
        v = self.verdicts.get(path)
        self.state.setText({"yes": tr("✓ 已確認係佢"), "no": tr("✗ 已標記唔係佢")}.get(v, ""))
        self.state.setStyleSheet(f"color: {theme.GOOD if v == 'yes' else theme.DANGER}; font-weight: 700;")
        taken = self.dates.get(path)
        self.path.setText(f"{tr('拍攝日期')} {taken}  ·  {path}" if taken else path)
        self.btn_prev.setEnabled(self.i > 0)
        self.btn_next.setEnabled(self.i < len(self.items) - 1)
        self._fit()

    def _fit(self):
        if self._pix is not None:
            self.label.setPixmap(self._pix.scaled(self.label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._fit()

    def keyPressEvent(self, e):
        k = e.key()
        if k in (Qt.Key_Right, Qt.Key_Space):
            self._step(1)
        elif k == Qt.Key_Left:
            self._step(-1)
        elif k == Qt.Key_Y:
            self._judge("yes")
        elif k == Qt.Key_N:
            self._judge("no")
        elif k == Qt.Key_F:
            self.b_box.toggle()
            self._toggle_box()
        else:
            super().keyPressEvent(e)
