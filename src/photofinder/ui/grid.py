"""Paged grid of result tiles. Click selects, double-click opens the viewer (where Y / N review is possible)."""
import os

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (QAbstractItemView, QHBoxLayout, QListWidget, QListWidgetItem, QStackedLayout,
                               QVBoxLayout, QWidget)

from .. import theme
from ..i18n import tr
from . import icons
from .common import FONT, PER_PAGE, button, label
from .viewer import ViewerDialog

KINDS = ("confirmed", "maybe", "rejected")


class ResultGrid(QWidget):
    def __init__(self, win, kind="confirmed"):
        super().__init__()
        self.win, self.kind = win, kind
        self.items, self.known, self.page = [], set(), 0
        self.rows, self.scores, self.qimgs = {}, {}, {}
        bar = QHBoxLayout()
        bar.setContentsMargins(4, 0, 0, 0)
        self.prev = button("", "icon", icon="chevron-left", tip=tr("上一頁"))
        self.next = button("", "icon", icon="chevron-right", tip=tr("下一頁"))
        self.info = label("", "hint")
        self.sel_all = button(tr("選取本頁全部"), "ghost")
        self.prev.clicked.connect(lambda: self.go(-1))
        self.next.clicked.connect(lambda: self.go(1))
        self.sel_all.clicked.connect(lambda: self.view.selectAll())
        bar.addWidget(self.info)
        bar.addStretch(1)
        bar.addWidget(self.sel_all)
        bar.addWidget(self.prev)
        bar.addWidget(self.next)

        self.view = QListWidget()
        self.view.setObjectName("grid")
        self.view.setViewMode(QListWidget.IconMode)
        self.view.setResizeMode(QListWidget.Adjust)
        self.view.setMovement(QListWidget.Static)
        self.view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.view.setUniformItemSizes(True)
        self.view.setSpacing(2)
        self.view.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.view.verticalScrollBar().setSingleStep(24)
        self.view.itemDoubleClicked.connect(self._open)
        self.apply_size()

        self.empty = QWidget()
        el = QVBoxLayout(self.empty)
        el.addStretch(1)
        self.empty_icon = label("")
        self.empty_icon.setAlignment(Qt.AlignCenter)
        self.empty_title = label("", "emptytitle")
        self.empty_text = label("", "empty", wrap=True)
        self.empty_steps = label("", "empty")
        for w in (self.empty_icon, self.empty_title, self.empty_text, self.empty_steps):
            w.setAlignment(Qt.AlignCenter)
            el.addWidget(w)
            el.addSpacing(6)
        self.empty_privacy = label(tr("🔒 全部喺你部電腦度運算 · 原相只會讀取,唔會改動、搬走或者上載"), "faint")
        self.empty_privacy.setAlignment(Qt.AlignCenter)
        el.addSpacing(10)
        el.addWidget(self.empty_privacy)
        el.addStretch(2)
        holder = QWidget()
        self.stack = QStackedLayout(holder)
        self.stack.addWidget(self.empty)
        self.stack.addWidget(self.view)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 6, 0, 0)
        lay.setSpacing(4)
        lay.addLayout(bar)
        lay.addWidget(holder, 1)
        self._dirty = False

    # ---- size / paging ------------------------------------------------------------------------
    def tile(self):
        return self.win.thumb_size

    def apply_size(self):
        t = self.tile()
        self.view.setIconSize(QSize(t, t))
        self.view.setGridSize(QSize(t + 14, t + 14))

    def pages(self):
        return max(1, -(-len(self.items) // PER_PAGE))

    def set_items(self, items):
        self.items = list(items)
        self.known = {p for _, p in self.items}
        self.page = min(self.page, self.pages() - 1)
        self.render()

    def add_if_new(self, score, path):
        if path in self.known:
            return
        self.known.add(path)
        self.items.append((score, path))
        self.items.sort(key=lambda t: -t[0])
        if not self._dirty:
            self._dirty = True
            QTimer.singleShot(500, self._flush)

    def _flush(self):
        self._dirty = False
        self.render()

    def go(self, step):
        n = self.page + step
        if 0 <= n < self.pages():
            self.page = n
            self.render()
            self.view.scrollToTop()

    # ---- drawing ------------------------------------------------------------------------------
    def render(self):
        """Show the current page. Keeps the user's selection and reuses pictures already loaded, so a
        refresh during a scan neither clears the selection nor makes thumbnails flicker."""
        selected = set(self.selected_paths())
        self.view.blockSignals(True)
        self.view.clear()
        self.rows.clear()
        self.scores = {p: s for s, p in self.items}
        chunk = self.items[self.page * PER_PAGE:(self.page + 1) * PER_PAGE]
        self.qimgs = {p: q for p, q in self.qimgs.items() if p in {c[1] for c in chunk}}  # bounded memory
        self.stack.setCurrentIndex(1 if chunk else 0)
        if not chunk:
            self.refresh_empty()
        for score, path in chunk:
            it = QListWidgetItem(QIcon(self._tile(self.qimgs.get(path), score, path)), "")
            it.setData(Qt.UserRole, path)
            it.setToolTip(f"{os.path.basename(path)}\n{tr('相似度 {s}%', s=f'{score * 100:.0f}')}\n{path}")
            self.view.addItem(it)
            self.rows[path] = it
            if path in selected:
                it.setSelected(True)
            if path not in self.qimgs:
                self.win.request_thumb(path)
        self.view.blockSignals(False)
        self.view.itemSelectionChanged.emit()
        n = len(self.items)
        self.info.setText(tr("共 {n} 張 · 第 {p}/{t} 頁", n=n, p=self.page + 1, t=self.pages()) if n > PER_PAGE
                          else (tr("共 {n} 張", n=n) if n else ""))
        multi = n > PER_PAGE
        self.prev.setVisible(multi)
        self.next.setVisible(multi)
        self.sel_all.setVisible(bool(n))
        self.prev.setEnabled(self.page > 0)
        self.next.setEnabled(self.page < self.pages() - 1)

    def repaint_tiles(self):
        """Redraw tiles in place (theme, zoom or review labels changed)."""
        for path, it in self.rows.items():
            it.setIcon(QIcon(self._tile(self.qimgs.get(path), self.scores.get(path, 0.0), path)))

    def _tile(self, qimg, score, path=None):
        """Square tile: rounded, face-centred picture with a score pill and the review mark."""
        t, dpr = self.tile(), 2.0
        tile = QPixmap(int(t * dpr), int(t * dpr))
        tile.setDevicePixelRatio(dpr)
        tile.fill(Qt.transparent)
        p = QPainter(tile)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        clip = QPainterPath()
        clip.addRoundedRect(0, 0, t, t, 12, 12)
        p.setClipPath(clip)
        p.fillRect(0, 0, t, t, QColor(theme.C["thumb"]))
        if qimg is None:
            p.drawPixmap(t // 2 - 14, t // 2 - 14, icons.pixmap("image", theme.C["faint"], 28))
        else:
            pm = QPixmap.fromImage(qimg)
            pm.setDevicePixelRatio(1.0)
            p.drawPixmap(0, 0, t, t, pm.scaled(int(t * dpr), int(t * dpr), Qt.KeepAspectRatioByExpanding,
                                              Qt.SmoothTransformation))
        p.setClipping(False)
        verdict = self.win.verdicts.get(path) if path else None
        if self.kind == "rejected" or verdict == "no":
            colour = "#6b7280"
        else:
            colour = theme.GOOD if (score >= self.win.high.value() / 100 or verdict == "yes") else theme.WARN
        f = QFont(FONT, 8 if t < 170 else 9)
        f.setBold(True)
        p.setFont(f)
        w = 44 if t < 170 else 50
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 110))
        p.drawRoundedRect(7, 7, w + 2, 24, 12, 12)
        p.setBrush(QColor(colour))
        p.drawRoundedRect(8, 8, w, 22, 11, 11)
        p.setPen(QColor("white"))
        p.drawText(8, 8, w, 22, Qt.AlignCenter, f"{score * 100:.0f}%")
        if verdict in ("yes", "no"):
            c = QColor(theme.GOOD if verdict == "yes" else theme.DANGER)
            p.setPen(QPen(QColor("white"), 2))
            p.setBrush(c)
            p.drawEllipse(t - 34, 8, 26, 26)
            p.drawPixmap(t - 29, 13, icons.pixmap("check" if verdict == "yes" else "x", "#ffffff", 16))
        p.end()
        return tile

    def set_thumb(self, path, qimg):
        it = self.rows.get(path)
        if it is not None:
            self.qimgs[path] = qimg
            it.setIcon(QIcon(self._tile(qimg, self.scores.get(path, 0.0), path)))

    def refresh_empty(self):
        c = theme.C
        if self.kind == "confirmed":
            folders, refs, scanned = self.win.setup_state()
            self.empty_icon.setPixmap(icons.pixmap("search", c["accent"], 56))
            self.empty_title.setText(tr("搵返一個人嘅所有相") if not scanned else tr("未有確認嘅相"))
            self.empty_text.setText(tr("俾幾張參考相,Photo Finder Pro 會喺你嘅相片資料夾入面搵晒佢出嚟,"
                                       "再複製一份去結果資料夾。") if not scanned else
                                    tr("試吓加多幾張唔同年份嘅參考相,或者喺「待你確認」度確認啲相。"))
            mark = lambda ok, n: "✓" if ok else n
            self.empty_steps.setText(f"{mark(folders, '①')} {tr('加入相片資料夾')}　　"
                                     f"{mark(refs, '②')} {tr('加入參考相')}　　③ {tr('撳「開始搜尋」')}"
                                     if not scanned else "")
            self.empty_steps.setVisible(not scanned)
        elif self.kind == "maybe":
            self.empty_icon.setPixmap(icons.pixmap("check", theme.GOOD, 48))
            self.empty_title.setText(tr("冇需要你確認嘅相"))
            self.empty_text.setText(tr("分數喺兩個門檻之間嘅相會喺呢度出現。雙擊一張相,用 Y / N 鍵快速確認。"))
            self.empty_steps.setVisible(False)
        else:
            self.empty_icon.setPixmap(icons.pixmap("x", c["faint"], 48))
            self.empty_title.setText(tr("未有排除嘅相"))
            self.empty_text.setText(tr("標記做「唔係佢」嘅相會放喺呢度,唔會出現喺最終結果。檔案本身唔會被刪除。"))
            self.empty_steps.setVisible(False)

    def selected_paths(self):
        return [i.data(Qt.UserRole) for i in self.view.selectedItems()]

    def _open(self, item):
        path = item.data(Qt.UserRole)
        idx = next(i for i, (_, p) in enumerate(self.items) if p == path)
        can_review = self.win.run is not None
        ViewerDialog(self, self.items, self.win.boxes, idx, verdicts=self.win.verdicts,
                     on_verdict=self.win.set_verdict if can_review else None,
                     high=self.win.high.value() / 100).exec()
        self.win.refresh_results()
