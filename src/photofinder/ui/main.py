"""Photo Finder Pro main window (PySide6). All heavy work runs in workers (workers.py).

Layout: top bar (search name, theme / language, stop / start), a sidebar of four setup cards, the result tabs
with a live scan dashboard above them, a floating selection bar, a status footer and short toast messages.
"""
import os

import numpy as np
from PySide6.QtCore import QSize, Qt, QThreadPool, QTimer
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QFileDialog, QFrame, QHBoxLayout, QLineEdit,
                               QListWidget, QListWidgetItem, QMenu, QMessageBox, QProgressBar, QScrollArea,
                               QSlider, QTabWidget, QVBoxLayout, QWidget)

from .. import copier, i18n, matcher, paths, settings, theme, workers
from ..engine import FaceEngine
from ..i18n import tr
from ..imageio import SUPPORTED_EXTS
from ..index import Index
from . import icons
from .common import APP, AVATAR, THUMB_PX, button, circle, label, retint
from .dialogs import FacePickerDialog
from .grid import ResultGrid
from .history import HistoryPanel
from .widgets import DropVeil, ScanPanel, Segmented, StepCard, Toast

PRESETS = {"loose": (45, 25), "balanced": (50, 30), "strict": (60, 40)}   # (confirmed %, maybe %)
ZOOM = (120, 320, 20)


class _Area(QWidget):
    """Main area; keeps the toast centred when it is resized."""
    toast = None

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self.toast is not None and self.toast.isVisible():
            self.toast.reposition()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.cfg = settings.load()
        theme.set_mode(self.cfg["theme"])   # before any widget is built: icons and tiles read the tokens
        i18n.set_lang(self.cfg["lang"])
        self.setWindowTitle(APP)
        self.setStyleSheet(theme.qss())
        self.setAcceptDrops(True)
        self.setMinimumSize(1100, 700)
        self.resize(1360, 860)
        self.index = Index()
        self._engine = None
        # A new (not yet started) search starts from these references; once a search is started its own
        # copy is kept under runs\<id>. This also carries over references saved by earlier versions.
        self.ref_paths, self.ref_counts, self.refs = matcher.load_refs()
        self.run = None   # the open search (a row of the runs table), or None for a new search
        self.boxes, self.verdicts, self._results = {}, {}, []
        self.thumb_size = self.cfg["thumb"]
        self.worker = None
        self._busy = False
        self._closed = False   # set in closeEvent: signals still queued from workers must then be ignored
        self.avatar_items, self.avatar_q = {}, {}
        self.pool = QThreadPool.globalInstance()
        self.thumb_signals = workers.make_thumb_signals()
        self.thumb_signals.ready.connect(self._thumb_ready)
        self.avatar_signals = workers.make_thumb_signals()
        self.avatar_signals.ready.connect(self._avatar_ready)
        self._thr_timer = QTimer(self, singleShot=True, interval=250)
        self._thr_timer.timeout.connect(self._thr_changed)
        self._build()
        for f in self.cfg["folders"]:
            self._add_folder_item(f)
        self.out_edit.setText(self.cfg["output"] or str(paths.default_output_dir()))
        self.high.setValue(int(round(self.cfg["high"] * 100)))
        self.low.setValue(int(round(self.cfg["low"] * 100)))
        last = self.cfg.get("last_run")
        if last is not None and self.index.get_run(last):
            self.load_run(last)
        else:
            self._update_refs_label()
            self._update_run_label()
            self.refresh_results()
            self._refresh_history()

    # ---- layout -------------------------------------------------------------------------------
    def _build(self):
        # top bar
        top = QFrame()
        top.setObjectName("topbar")
        tl = QHBoxLayout(top)
        tl.setContentsMargins(20, 10, 20, 10)
        tl.setSpacing(10)
        self.logo = label("")
        self.logo.setPixmap(icons.pixmap("logo", theme.C["accent"], 22))
        brand = QVBoxLayout()
        brand.setSpacing(0)
        brand.addWidget(label("Photo Finder Pro", "brand"))
        brand.addWidget(label(tr("100% 本機運算 · 私隱安全"), "brandsub"))
        tl.addWidget(self.logo)
        tl.addLayout(brand)
        tl.addSpacing(18)
        namebox = QFrame()
        namebox.setObjectName("namebox")
        namebox.setFixedWidth(360)
        nl = QHBoxLayout(namebox)
        nl.setContentsMargins(6, 2, 4, 2)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(tr("搵邊個?例如:公公"))
        self.name_edit.editingFinished.connect(self._name_changed)
        self.b_new = button(tr("新搜尋"), "ghost", icon="plus", tip=tr("開一個全新嘅搜尋(清空參考相同名)"))
        self.b_new.clicked.connect(self.new_search)
        nl.addWidget(self.name_edit, 1)
        nl.addWidget(self.b_new)
        tl.addWidget(namebox)
        tl.addStretch(1)
        self.b_theme = button("", "icon", tip=tr("切換深色 / 淺色"))
        self.b_theme.clicked.connect(self.toggle_theme)
        self.b_lang = button("", "icon", icon="globe", tip=tr("切換語言 / Language"))
        self.b_lang.clicked.connect(self.toggle_lang)
        self._paint_toggles()
        self.bar = QProgressBar()
        self.bar.setTextVisible(False)
        self.b_stop = button(tr("停止"), "danger", icon="stop", color=theme.DANGER, tip=tr("停止(下次會由停低嗰度繼續)"))
        self.b_start = button(tr("開始搜尋"), "primary", icon="play", color="#ffffff")
        self.b_stop.setEnabled(False)
        self.b_start.clicked.connect(self.start_scan)
        self.b_stop.clicked.connect(self.stop_task)
        for w in (self.b_theme, self.b_lang):
            tl.addWidget(w)
        tl.addSpacing(6)
        tl.addWidget(self.b_stop)
        tl.addWidget(self.b_start)

        # sidebar: four setup cards
        self.card_folders = StepCard(1, tr("相片資料夾"), tr("可以直接拖資料夾入嚟,包括子資料夾"))
        self.folder_list = QListWidget()
        self.folder_list.setFixedHeight(72)
        self.folder_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.folder_list.setTextElideMode(Qt.ElideMiddle)
        self.folder_list.itemChanged.connect(self._folders_changed)
        self.b_add = button(tr("加入資料夾"), icon="folder-plus")
        self.b_rm = button(tr("移除"), "ghost")
        self.b_add.clicked.connect(self.add_folder)
        self.b_rm.clicked.connect(self.remove_folder)
        self.card_folders.body.addWidget(self.folder_list)
        self.card_folders.body.addLayout(self._row(self.b_add, 1, self.b_rm))

        self.card_refs = StepCard(2, tr("要搵嘅人"))
        self.avatars = QListWidget()
        self.avatars.setObjectName("avatars")
        self.avatars.setViewMode(QListWidget.IconMode)
        self.avatars.setIconSize(QSize(AVATAR, AVATAR))
        self.avatars.setGridSize(QSize(AVATAR + 8, AVATAR + 8))
        self.avatars.setMovement(QListWidget.Static)
        self.avatars.setSelectionMode(QAbstractItemView.SingleSelection)
        self.avatars.setFixedHeight(2 * (AVATAR + 8) + 6)
        self.avatars.setContextMenuPolicy(Qt.ActionsContextMenu)
        act = QAction(tr("從參考相移除"), self.avatars)
        act.triggered.connect(self.remove_selected_ref)
        self.avatars.addAction(act)
        self.refs_label = label("", "hint", wrap=True)
        self.b_ref = button(tr("加入參考相"), icon="user-plus")
        self.b_ref_rm = button(tr("移除所選"), "ghost")
        self.b_clear = button(tr("全部清除"), "ghost")
        self.b_ref.clicked.connect(self.add_refs)
        self.b_clear.clicked.connect(self.clear_refs)
        self.b_ref_rm.clicked.connect(self.remove_selected_ref)
        self.card_refs.body.addWidget(self.avatars)
        self.card_refs.body.addWidget(self.refs_label)
        self.card_refs.body.addLayout(self._row(self.b_ref, 1, self.b_ref_rm, self.b_clear))

        self.card_acc = StepCard(3, tr("準確度"), tr("越低越寬鬆,搵到更多但可能有錯。"))
        self.presets = Segmented([("loose", tr("寬鬆"), tr("搵到更多,但可能有錯")),
                                  ("balanced", tr("平衡"), tr("建議")),
                                  ("strict", tr("嚴格"), tr("更準確,但可能漏咗啲"))])
        self.presets.chosen.connect(self._preset_chosen)
        self.card_acc.body.addWidget(self.presets)
        self.high, self.low = QSlider(Qt.Horizontal), QSlider(Qt.Horizontal)
        for name, sl_, tip in ((tr("確認"), self.high, tr("分數去到呢個百分比就自動當係佢")),
                               (tr("待確認"), self.low, tr("分數喺呢度同「確認」之間嘅相,留俾你睇"))):
            sl_.setRange(1, 99)
            sl_.setToolTip(tip)
            row = QHBoxLayout()
            nm = label(name)
            nm.setMinimumWidth(48)
            row.addWidget(nm)
            row.addWidget(sl_, 1)
            val = label("", "value")
            val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            sl_.valueChanged.connect(lambda v, lab=val: lab.setText(f"{v}%"))
            sl_.valueChanged.connect(lambda _v: self._thr_timer.start())
            sl_.valueChanged.connect(lambda _v: self._sync_preset())
            row.addWidget(val)
            self.card_acc.body.addLayout(row)

        self.card_out = StepCard(4, tr("結果放邊"), tr("每次搜尋喺入面開新資料夾"))
        self.out_edit = QLineEdit()
        self.out_edit.textChanged.connect(self._update_steps)
        self.b_out = button(tr("選擇…"))
        self.b_open_out = button(tr("開啟"), icon="open")
        self.b_out.clicked.connect(self.pick_output)
        self.b_open_out.clicked.connect(self.open_output)
        self.card_out.body.addWidget(self.out_edit)
        self.card_out.body.addLayout(self._row(self.b_out, 1, self.b_open_out))

        self.run_label = label("", "hint", wrap=True)
        inner = QWidget()
        inner.setObjectName("sideinner")
        il = QVBoxLayout(inner)
        il.setContentsMargins(16, 16, 16, 16)
        il.setSpacing(12)
        for c in (self.card_folders, self.card_refs, self.card_acc, self.card_out):
            il.addWidget(c)
        il.addWidget(self.run_label)
        il.addStretch(1)
        scroll = QScrollArea()
        scroll.setObjectName("sidescroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(inner)
        side = QFrame()
        side.setObjectName("sidebar")
        side.setFixedWidth(372)
        sl = QVBoxLayout(side)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.addWidget(scroll)

        # main: scan dashboard + result tabs
        self.scan_panel = ScanPanel(self.bar)
        self.tabs = QTabWidget()
        self.grid_ok = ResultGrid(self, "confirmed")
        self.grid_maybe = ResultGrid(self, "maybe")
        self.grid_rej = ResultGrid(self, "rejected")
        self.grids = (self.grid_ok, self.grid_maybe, self.grid_rej)
        self.history = HistoryPanel(self)
        for w in (self.grid_ok, self.grid_maybe, self.grid_rej):
            self.tabs.addTab(w, "")
        self.tabs.addTab(self.history, tr("搜尋歷史"))
        corner = QWidget()
        cl = QHBoxLayout(corner)
        cl.setContentsMargins(0, 0, 0, 4)
        cl.setSpacing(8)
        self.zoom = QSlider(Qt.Horizontal)
        self.zoom.setRange(ZOOM[0], ZOOM[1])
        self.zoom.setSingleStep(ZOOM[2])
        self.zoom.setPageStep(ZOOM[2])
        self.zoom.setFixedWidth(100)
        self.zoom.setToolTip(tr("縮圖大小"))
        self.zoom.setValue(self.thumb_size)
        self.zoom.valueChanged.connect(self._zoom_changed)
        self.b_export_final = button(tr("匯出最終結果"), "primary", icon="export", color="#ffffff",
                                     tip=tr("將確認嘅相複製到結果資料夾嘅 final 入面"))
        self.b_export_final.setStyleSheet("padding: 5px 16px;")   # fits the tab bar height
        self.b_export_final.clicked.connect(self.export_final)
        self.b_more = button("", "icon", icon="more", tip=tr("更多"))
        self.b_more.clicked.connect(self._more_menu)
        self.act_refresh = QAction(tr("重新整理"), self)
        self.act_copy = QAction(tr("複製結果"), self)
        self.act_unchecked = QAction(tr("匯出無法檢查清單"), self)
        self.act_refresh.triggered.connect(self.refresh_results)
        self.act_copy.triggered.connect(self.copy_results)
        self.act_unchecked.triggered.connect(self.export_unchecked)
        for w in (self.zoom, self.b_export_final, self.b_more):
            cl.addWidget(w)
        self.tabs.setCornerWidget(corner, Qt.TopRightCorner)

        # floating selection bar
        self.selbar = QFrame()
        self.selbar.setObjectName("selbar")
        sb = QHBoxLayout(self.selbar)
        sb.setContentsMargins(16, 8, 12, 8)
        sb.setSpacing(8)
        self.sel_label = label("")
        self.b_yes = button(tr("係佢"), "yes", icon="check", color="#22c55e")
        self.b_no = button(tr("唔係佢"), "no", icon="x", color="#ef4444")
        self.b_unmark = button(tr("清除標記"), "ghost")
        self.b_addref = button(tr("加入參考相"), "primary", icon="user-plus", color="#ffffff")
        b_clear_sel = button(tr("取消選取"), "ghost")
        self.b_yes.clicked.connect(lambda: self._mark_selected("yes"))
        self.b_no.clicked.connect(lambda: self._mark_selected("no"))
        self.b_unmark.clicked.connect(lambda: self._mark_selected(None))
        self.b_addref.clicked.connect(self.add_selected_as_refs)
        b_clear_sel.clicked.connect(self._clear_selection)
        sb.addWidget(self.sel_label)
        sb.addStretch(1)
        for w in (self.b_yes, self.b_no, self.b_unmark, self.b_addref, b_clear_sel):
            sb.addWidget(w)
        self.selbar.hide()
        for g in self.grids:
            g.view.itemSelectionChanged.connect(self._sel_changed)

        self.area = _Area()
        main = QVBoxLayout(self.area)
        main.setContentsMargins(20, 14, 20, 12)
        main.setSpacing(10)
        main.addWidget(self.scan_panel)
        main.addWidget(self.tabs, 1)
        main.addWidget(self.selbar)
        self.toast = Toast(self.area)
        self.area.toast = self.toast

        # footer
        foot = QFrame()
        foot.setObjectName("footer")
        fl = QHBoxLayout(foot)
        fl.setContentsMargins(20, 6, 20, 6)
        self.status = label(tr("只讀取原相,只複製到輸出資料夾。"), "status")
        fl.addWidget(self.status)

        body = QHBoxLayout()
        body.setSpacing(0)
        body.addWidget(side)
        body.addWidget(self.area, 1)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(top)
        root.addLayout(body, 1)
        root.addWidget(foot)
        self.veil = DropVeil(self)
        for e in (self.name_edit, self.out_edit, self.history.filter):
            e.setAcceptDrops(False)   # a dropped folder must reach the window, not be pasted as text
        self.busy_widgets = [self.b_new, self.name_edit, self.b_add, self.b_rm, self.b_ref, self.b_ref_rm,
                             self.b_clear, self.b_start, self.b_addref, self.b_yes, self.b_no, self.b_unmark,
                             self.b_export_final, self.b_more, self.b_out, self.high, self.low, self.presets]
        self._set_tab_counts(0, 0, 0)

    @staticmethod
    def _row(*items):
        """Button row; an int after a widget is its stretch."""
        r = QHBoxLayout()
        r.setSpacing(6)
        last = None
        for it in items:
            if isinstance(it, int):
                r.setStretchFactor(last, it)
            else:
                r.addWidget(it)
                last = it
        return r

    # ---- helpers ------------------------------------------------------------------------------
    def engine(self):
        if self._engine is None:
            self._engine = FaceEngine()
        return self._engine

    def set_busy(self, busy, stoppable=True):
        self._busy = busy
        for w in self.busy_widgets:
            w.setEnabled(not busy)
        self.history.set_enabled(not busy)
        self.b_stop.setEnabled(busy and stoppable)
        self._update_review_state()

    def say(self, text):
        self.status.setText(text)

    def notify(self, text, ms=3800):
        self.toast.show_text(text, ms)

    def folders(self):
        return [self.folder_list.item(i).data(Qt.UserRole) for i in range(self.folder_list.count())
                if self.folder_list.item(i).checkState() == Qt.Checked]

    def _add_folder_item(self, path):
        for i in range(self.folder_list.count()):
            if self.folder_list.item(i).data(Qt.UserRole) == path:
                return
        it = QListWidgetItem(path)
        it.setData(Qt.UserRole, path)
        it.setToolTip(path)
        it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
        it.setCheckState(Qt.Checked)
        self.folder_list.addItem(it)

    def _folders_changed(self, *_):
        """Ticking or adding/removing a folder changes which results are shown."""
        self._update_steps()
        self._thr_timer.start()

    def setup_state(self):
        """(has ticked folders, has references, anything scanned yet) for the empty-state hints."""
        return bool(self.folders()), bool(len(self.refs)), self.run is not None or bool(self.index.stats())

    def _update_steps(self, *_):
        self.card_folders.set_done(bool(self.folders()))
        self.card_refs.set_done(len(self.refs) > 0)
        self.card_acc.set_done(True)
        self.card_out.set_done(bool(self.out_edit.text().strip()))

    def _update_refs_label(self):
        n = len(self.ref_paths)
        self.refs_label.setText(tr("{n} 張參考相,{m} 個參考臉(連鏡像)。越多張、越多年份越準。", n=n, m=len(self.refs))
                                if n else tr("未有參考相。加入幾張清楚嘅正面相。"))
        self.avatars.clear()
        self.avatar_items.clear()
        for path in self.ref_paths:
            it = QListWidgetItem(QIcon(circle(self.avatar_q.get(path))), "")
            it.setData(Qt.UserRole, path)
            it.setToolTip(path + "\n" + tr("(撳選,再按「移除所選」或者右鍵移除)"))
            self.avatars.addItem(it)
            self.avatar_items[path] = it
            if path not in self.avatar_q:
                self.request_thumb(path, framed=False)
        self._update_steps()

    def save_settings(self):
        self.cfg.update(folders=[self.folder_list.item(i).data(Qt.UserRole) for i in range(self.folder_list.count())],
                        output=self.out_edit.text().strip(), low=self.low.value() / 100, high=self.high.value() / 100,
                        last_run=self.run["id"] if self.run else None, thumb=self.thumb_size)
        settings.save(self.cfg)

    # ---- look & language ----------------------------------------------------------------------
    def _paint_toggles(self):
        self.b_theme.setProperty("icon_name", "sun" if theme.mode == "dark" else "moon")
        self.b_theme.setIcon(icons.icon("sun" if theme.mode == "dark" else "moon", theme.C["text"], 18))
        self.b_theme.setIconSize(QSize(18, 18))
        self.b_lang.setText("EN" if i18n.lang() == "zh" else "中")

    def toggle_theme(self):
        theme.set_mode("light" if theme.mode == "dark" else "dark")
        self.cfg["theme"] = theme.mode
        self.setStyleSheet(theme.qss())
        retint(self)
        self._paint_toggles()
        self.logo.setPixmap(icons.pixmap("logo", theme.C["accent"], 22))
        self.history.paint_empty()
        for g in self.grids:
            g.refresh_empty()
            g.repaint_tiles()
        for path, it in self.avatar_items.items():
            it.setIcon(QIcon(circle(self.avatar_q.get(path))))
        self.save_settings()

    def toggle_lang(self):
        new = "en" if i18n.lang() == "zh" else "zh"
        self.cfg["lang"] = new
        self.save_settings()
        key = "重新開啟程式後生效"
        self.notify(f"{key} · {i18n.EN.get(key, key)}", 5000)   # shown in both languages; no auto restart
        i18n.set_lang(new)
        self._paint_toggles()

    def _zoom_changed(self, v):
        snapped = round(v / ZOOM[2]) * ZOOM[2]
        if snapped != v:
            self.zoom.setValue(snapped)
            return
        self.thumb_size = v
        for g in self.grids:
            g.apply_size()
            g.repaint_tiles()
        self.save_settings()

    def _more_menu(self):
        m = QMenu(self)
        for a in (self.act_refresh, self.act_copy, self.act_unchecked):
            m.addAction(a)
        m.exec(self.b_more.mapToGlobal(self.b_more.rect().bottomLeft()))

    # ---- accuracy presets ---------------------------------------------------------------------
    def _preset_chosen(self, key):
        high, low = PRESETS[key]
        self.high.setValue(high)
        self.low.setValue(low)
        self._sync_preset()

    def _sync_preset(self):
        cur = (self.high.value(), self.low.value())
        self.presets.set_current(next((k for k, v in PRESETS.items() if v == cur), None))

    # ---- searches (runs) ----------------------------------------------------------------------
    def _persist_refs(self):
        """Save the reference faces: into the open search's own snapshot, or the new-search draft."""
        home = paths.run_dir(self.run["id"]) if self.run else None
        matcher.save_refs(self.ref_paths, self.ref_counts, self.refs, home=home)

    def _run_name(self):
        return self.name_edit.text().strip() or tr("未命名")

    def _update_run_label(self):
        if self.run:
            self.run_label.setText(tr("結果資料夾:{d}\n再撳「開始搜尋」會繼續放入呢個資料夾;想開新資料夾請撳「新搜尋」。",
                                      d=os.path.basename(self.run["run_dir"])))
        else:
            self.run_label.setText(tr("未開始。撳「開始搜尋」會喺輸出資料夾入面開一個新資料夾。"
                                      "注意:每次搜尋都會重新複製符合嘅相,會用多啲磁碟空間。"))

    def _write_run_json(self):
        if not self.run:
            return
        r = self.index.get_run(self.run["id"])
        self.run = r
        try:
            copier.write_run_json(r["run_dir"], {
                "name": r["name"], "created": r["created"], "folders": r["folders"], "low": r["low"],
                "high": r["high"], "confirmed": r["confirmed"], "maybe": r["maybe"],
                "finished": bool(r["finished"]), "reference_images": list(self.ref_paths)})
        except OSError:
            pass  # the results folder may have been moved by the user; the history record still works

    def _ensure_run(self, folders):
        """Create the search (results folder, history record, reference snapshot) the first time it is
        needed; later calls just save the current folders/thresholds/name."""
        low, high = self.low.value() / 100, self.high.value() / 100
        if self.run is None:
            copier.validate_output_root(self.output_root(), folders)   # BEFORE a folder is created
            run_dir = copier.new_run_dir(self.output_root(), self.name_edit.text())
            rid = self.index.create_run(self._run_name(), folders, run_dir, low, high)
            self.run = self.index.get_run(rid)
            self._persist_refs()
        else:
            copier.validate_output_root(self.run["run_dir"], folders)
            self.index.update_run(self.run["id"], name=self._run_name(), folders=folders, low=low, high=high)
            self._persist_refs()
        self._write_run_json()
        self._update_run_label()
        self._refresh_history()
        return self.run

    def _name_changed(self):
        if self.run:
            self.index.update_run(self.run["id"], name=self._run_name())
            self.run = self.index.get_run(self.run["id"])
            self._refresh_history()

    def _refresh_history(self):
        self.history.reload(self.index.list_runs(), self.run["id"] if self.run else None)

    def new_search(self):
        """Blank search: no references, no name. The next scan gets its own new results folder."""
        self.run = None
        self.name_edit.clear()
        self.ref_paths, self.ref_counts, self.refs = [], [], np.zeros((0, 128), np.float32)
        self._persist_refs()
        self.boxes = {}
        self.scan_panel.hide()
        self._update_refs_label()
        self._update_run_label()
        self.refresh_results()
        self._refresh_history()
        self.tabs.setCurrentIndex(0)
        self.say(tr("新搜尋:加入參考相同相片資料夾,再撳「開始搜尋」。"))
        self.save_settings()

    def load_run(self, run_id):
        """Reopen a past search with its own references, folders and thresholds."""
        row = self.index.get_run(run_id)
        if row is None:
            return
        self.run = row
        self.name_edit.setText(row["name"])
        self.ref_paths, self.ref_counts, self.refs = matcher.load_refs(home=paths.run_dir(run_id))
        self.folder_list.clear()
        for f in row["folders"]:
            self._add_folder_item(f)
        self.low.setValue(int(round(row["low"] * 100)))
        self.high.setValue(int(round(row["high"] * 100)))
        self.scan_panel.hide()
        self._update_refs_label()
        self._update_run_label()
        self.refresh_results()
        self._refresh_history()
        self.tabs.setCurrentIndex(0)
        self.save_settings()

    def open_selected_run(self):
        rid = self.history.selected_id()
        if rid is None:
            QMessageBox.information(self, APP, tr("請先揀一個搜尋。"))
            return
        self.load_run(rid)

    def open_selected_run_folder(self):
        rid = self.history.selected_id()
        row = self.index.get_run(rid) if rid is not None else None
        if row is None:
            QMessageBox.information(self, APP, tr("請先揀一個搜尋。"))
        elif os.path.isdir(row["run_dir"]):
            os.startfile(row["run_dir"])
        else:
            QMessageBox.information(self, APP, tr("搵唔到結果資料夾(可能已被搬走):\n{d}", d=row["run_dir"]))

    def forget_selected_run(self):
        rid = self.history.selected_id()
        if rid is None:
            QMessageBox.information(self, APP, tr("請先揀一個搜尋。"))
            return
        ask = QMessageBox.question(self, APP, tr("移除呢個搜尋紀錄?\n\n只係移除紀錄,唔會刪除結果資料夾同任何相片。"))
        if ask != QMessageBox.Yes:
            return
        self.index.delete_run(rid)
        if self.run and self.run["id"] == rid:
            self.run, self.verdicts = None, {}
            self._update_run_label()
            self._redistribute()
        self._refresh_history()
        self.save_settings()

    # ---- folders, refs, output ----------------------------------------------------------------
    def add_folder(self):
        d = QFileDialog.getExistingDirectory(self, tr("揀相片資料夾(會包括子資料夾)"))
        if d:
            self._add_folder_item(os.path.normpath(d))
            self.save_settings()

    def remove_folder(self):
        for it in self.folder_list.selectedItems():
            self.folder_list.takeItem(self.folder_list.row(it))
        self.save_settings()
        self._folders_changed()

    def pick_output(self):
        d = QFileDialog.getExistingDirectory(self, tr("揀輸出資料夾(唔可以喺相片資料夾入面)"))
        if d:
            self.out_edit.setText(os.path.normpath(d))
            self.save_settings()

    def output_root(self):
        return self.out_edit.text().strip() or str(paths.default_output_dir())

    def open_output(self):
        p = self.output_root()
        os.makedirs(p, exist_ok=True)
        os.startfile(p)

    def add_refs(self):
        exts = " ".join(f"*{e}" for e in sorted(SUPPORTED_EXTS))
        files, _ = QFileDialog.getOpenFileNames(self, tr("揀參考相"), "", f"{tr('相片')} ({exts})")
        if files:
            self._build_refs([os.path.normpath(f) for f in files])

    def add_selected_as_refs(self):
        sel = self.grid_ok.selected_paths() + self.grid_maybe.selected_paths()
        if not sel:
            QMessageBox.information(self, APP, tr("請先喺結果入面揀相。"))
            return
        self._build_refs(sel)

    def _build_refs(self, image_paths):
        try:
            eng = self.engine()
        except Exception as e:
            QMessageBox.critical(self, APP, tr("載入人臉模型失敗:{e}", e=e))
            return
        self.set_busy(True, stoppable=False)
        self.say(tr("正在分析參考相…"))
        self.worker = workers.RefWorker(eng, image_paths)
        self.worker.done.connect(self._refs_analysed)
        self.worker.failed.connect(self._task_failed)
        self.worker.start()

    def _ask_face(self, item):
        """Show the photo with numbered faces; return the chosen index or None (skipped)."""
        dlg = FacePickerDialog(self, item["path"], [f[0] for f in item["faces"]])
        dlg.exec()
        return dlg.choice

    def _refs_analysed(self, items, notes):
        """Decide which face in each image is the person (automatically when clear, else ask), add the
        face and its mirror image to the references."""
        if self._closed:
            return
        known = self.refs if len(self.refs) else None
        vectors, used, used_counts, skipped = [], [], [], []
        for item in items:
            if item["path"] in self.ref_paths or item["path"] in used:
                continue  # already a reference: adding it again would double its weight
            idx = matcher.auto_pick(item["faces"], known)
            if idx is None:
                idx = self._ask_face(item)
            if idx is None:
                skipped.append(os.path.basename(item["path"]))
                continue
            rows = [item["faces"][idx][2]]
            mirror = matcher.mirror_embedding(item["faces"][idx][0], item["flipped"], item["width"])
            if mirror is not None:
                rows.append(mirror)
            vectors.extend(rows)
            used.append(item["path"])
            used_counts.append(len(rows))
            mat = np.vstack(vectors).astype(np.float32)
            known = np.vstack([self.refs, mat]) if len(self.refs) else mat  # helps the next images
        if vectors:
            mat = np.vstack(vectors).astype(np.float32)
            self.refs = np.vstack([self.refs, mat]) if len(self.refs) else mat
            self.ref_paths = self.ref_paths + used
            self.ref_counts = self.ref_counts + used_counts
            self._persist_refs()
        self._update_refs_label()
        self.set_busy(False)
        self._clear_selection()
        extra = []
        if notes:
            extra.append(tr("{n} 張冇揾到人臉", n=len(notes)))
        if skipped:
            extra.append(tr("略過 {n} 張", n=len(skipped)))
        msg = tr("參考相已更新。") + ("(" + ";".join(extra) + ")" if extra else "")
        self.say(msg)
        self.notify(msg)
        self.refresh_results()

    def clear_refs(self):
        if QMessageBox.question(self, APP, tr("清除所有參考相?(已掃描嘅資料唔受影響)")) == QMessageBox.Yes:
            self.ref_paths, self.ref_counts, self.refs = [], [], np.zeros((0, 128), np.float32)
            self._persist_refs()
            self._update_refs_label()
            self.refresh_results()

    def remove_selected_ref(self):
        """Remove ONE reference photo from the reference list (the photo file itself is never touched)."""
        items = self.avatars.selectedItems()
        if not items:
            QMessageBox.information(self, APP, tr("請先撳一個頭像,揀要移除嘅參考相。"))
            return
        path = items[0].data(Qt.UserRole)
        if path not in self.ref_paths:
            return
        ask = QMessageBox.question(self, APP, tr("從參考相移除呢張?\n{p}\n\n只係由參考相清單移除,唔會刪除相片檔案。", p=path))
        if ask != QMessageBox.Yes:
            return
        i = self.ref_paths.index(path)
        self.ref_paths, self.ref_counts, self.refs = matcher.remove_reference(
            self.ref_paths, self.ref_counts, self.refs, i)
        self._persist_refs()
        self._update_refs_label()
        self.say(tr("已移除一張參考相。"))
        self.refresh_results()

    # ---- drag & drop --------------------------------------------------------------------------
    @staticmethod
    def _dropped(e):
        return [u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]

    def _droppable(self, e):
        if self._busy or not e.mimeData().hasUrls():
            return False
        return any(os.path.isdir(p) or os.path.splitext(p)[1].lower() in SUPPORTED_EXTS for p in self._dropped(e))

    def dragEnterEvent(self, e):
        if self._droppable(e):
            e.acceptProposedAction()
            self.veil.cover()
        else:
            e.ignore()

    def dragLeaveEvent(self, e):
        self.veil.hide()

    def dropEvent(self, e):
        self.veil.hide()
        if not self._droppable(e):
            e.ignore()
            return
        e.acceptProposedAction()
        dirs = [os.path.normpath(p) for p in self._dropped(e) if os.path.isdir(p)]
        imgs = [os.path.normpath(p) for p in self._dropped(e)
                if os.path.isfile(p) and os.path.splitext(p)[1].lower() in SUPPORTED_EXTS]
        for d in dirs:
            self._add_folder_item(d)
        if dirs:
            self.save_settings()
            self.notify(tr("已加入 {n} 個資料夾", n=len(dirs)))
        if imgs:
            self._build_refs(imgs)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self.veil.isVisible():
            self.veil.cover()

    # ---- results ------------------------------------------------------------------------------
    def request_thumb(self, path, framed=True):
        """Build a thumbnail in the background: face-centred squares for the grids, plain ones for avatars."""
        if framed:
            self.pool.start(workers.ThumbTask(path, THUMB_PX, self.boxes.get(path), self.thumb_signals, square=True))
        else:
            self.pool.start(workers.ThumbTask(path, 160, None, self.avatar_signals, square=False))

    def _thumb_ready(self, path, qimg):
        for g in self.grids:
            g.set_thumb(path, qimg)

    def _avatar_ready(self, path, qimg):
        self.avatar_q[path] = qimg
        it = self.avatar_items.get(path)
        if it is not None:
            it.setIcon(QIcon(circle(qimg)))

    def _thr_changed(self):
        if self.low.value() > self.high.value():
            self.low.setValue(self.high.value())
        if self.worker is None or not self.worker.isRunning():
            self.refresh_results()

    def _selected(self):
        return [p for g in self.grids for p in g.selected_paths()]

    def _sel_changed(self):
        n = len(self._selected())
        self.selbar.setVisible(n > 0)
        self.sel_label.setText(tr("已選 {n} 張", n=n))
        self._update_review_state()

    def _clear_selection(self):
        for g in self.grids:
            g.view.clearSelection()

    def _update_review_state(self):
        ok = self.run is not None and not self._busy
        tip = "" if ok else tr("完成一次搜尋之後先可以標記")
        for b in (self.b_yes, self.b_no, self.b_unmark):
            b.setEnabled(ok)
            b.setToolTip(tip)

    def _set_tab_counts(self, a, b, c):
        for i, (key, n) in enumerate(((tr("確認 {n}"), a), (tr("待你確認 {n}"), b), (tr("已排除 {n}"), c))):
            self.tabs.setTabText(i, key.format(n=n))

    def refresh_results(self):
        """Re-score everything from the index, then sort it into the three tabs using the review labels."""
        if self._closed:
            return
        self._results, self.boxes = matcher.score_photos(self.index, self.refs, self.folders())
        self.verdicts = self.index.verdicts(self.run["id"]) if self.run else {}
        self._redistribute()

    def _redistribute(self):
        confirmed, maybe, rejected = matcher.apply_verdicts(self._results, self.verdicts, self.low.value() / 100,
                                                            self.high.value() / 100)
        self.grid_ok.set_items(confirmed)
        self.grid_maybe.set_items(maybe)
        self.grid_rej.set_items(rejected)
        self._set_tab_counts(len(confirmed), len(maybe), len(rejected))
        self._update_steps()
        self._update_review_state()

    # ---- review (labels only; photo files are never touched) -----------------------------------
    def set_verdict(self, path, verdict):
        self.set_verdicts([path], verdict)

    def set_verdicts(self, paths_, verdict):
        """Label photos "yes" / "no" (None clears). Needs an open search; only the database changes."""
        paths_ = list(paths_)
        if self.run is None or not paths_:
            return
        self.index.set_verdicts(self.run["id"], paths_, verdict)
        for p in paths_:
            if verdict is None:
                self.verdicts.pop(p, None)
            else:
                self.verdicts[p] = verdict
        if self.worker is None or not self.worker.isRunning():   # during a scan the end-of-scan refresh does it
            self._redistribute()
        n = len(paths_)
        self.notify({"yes": tr("已確認 {n} 張係佢", n=n), "no": tr("已排除 {n} 張,可以喺「已排除」睇返", n=n),
                     None: tr("已清除 {n} 張嘅標記", n=n)}[verdict], 2600)

    def _mark_selected(self, verdict):
        sel = self._selected()
        if not sel:
            return
        self.set_verdicts(sel, verdict)
        self._clear_selection()

    # ---- scan ---------------------------------------------------------------------------------
    def start_scan(self):
        folders = self.folders()
        if not len(self.refs):
            QMessageBox.information(self, APP, tr("掃描前請先加入參考相。"))
            return
        if not folders:
            QMessageBox.information(self, APP, tr("請先加入並剔選至少一個相片資料夾。"))
            return
        try:
            eng = self.engine()
            run = self._ensure_run(folders)
        except Exception as e:
            QMessageBox.critical(self, APP, str(e))
            return
        self.save_settings()
        self.set_busy(True)
        self.scan_panel.start(tr("搜尋中…"))
        self.scan_panel.set_found(len(self.grid_ok.items), len(self.grid_maybe.items))
        self.say(tr("掃描中…結果放入:{d}", d=os.path.basename(run["run_dir"])))
        self.worker = workers.ScanWorker(folders, self.index, eng, self.refs, self.low.value() / 100,
                                         self.high.value() / 100, run["run_dir"])
        self.worker.phase.connect(self._scan_phase)
        self.worker.progress.connect(self._scan_progress)
        self.worker.matched.connect(self._scan_matched)
        self.worker.done.connect(self._scan_done)
        self.worker.failed.connect(self._task_failed)
        self.worker.start()

    def _scan_phase(self, text):
        if not self._closed:
            self.scan_panel.set_phase(text)
            self.say(text)

    def _scan_progress(self, i, total, path):
        if self._closed:
            return
        self.scan_panel.progress(i, total)
        self.say(tr("正在列出相片…") if total == 0 else f"{i}/{total}  {os.path.basename(path)}")

    def _scan_matched(self, tier, score, path, box):
        if self._closed:
            return
        self.boxes[path] = box
        v = self.verdicts.get(path)
        grid = (self.grid_rej if v == "no" else self.grid_ok if v == "yes" or tier == matcher.TIER_CONFIRMED
                else self.grid_maybe)
        grid.add_if_new(score, path)
        self.scan_panel.set_found(len(self.grid_ok.items), len(self.grid_maybe.items))

    def _scan_done(self, res):
        if self._closed:
            return
        self.set_busy(False)
        msg = tr("完成:共 {total} 張,新掃描 {scanned},跳過 {skipped},失敗 {failed};已複製 {copied}。",
                 total=res["total"], scanned=res["scanned"], skipped=res["skipped"], failed=res["failed"],
                 copied=res.get("copied", {}))
        title = tr("搜尋完成")
        if res["disk_low"]:
            msg = tr("輸出磁碟剩餘空間不足,已停止。") + msg
            title = tr("磁碟空間不足,已停止")
        if res["stopped"]:
            msg = tr("已停止。") + msg
            title = tr("已停止")
        self.say(msg)
        self.refresh_results()
        a, b = len(self.grid_ok.items), len(self.grid_maybe.items)
        self.scan_panel.set_found(a, b)
        self.scan_panel.finish(title, msg)
        if self.run:
            self.index.update_run(self.run["id"], finished=0 if res["stopped"] or res["disk_low"] else 1,
                                  confirmed=a, maybe=b)
            self._write_run_json()
            self._refresh_history()
        self.notify(f"{title}:" + tr("{a} 張確認 + {b} 張待你確認", a=a, b=b), 5000)
        QApplication.alert(self)

    def _task_failed(self, err):
        if self._closed:
            return
        self.set_busy(False)
        self.scan_panel.hide()
        self.say(tr("出錯:") + err)
        QMessageBox.critical(self, APP, err)

    def stop_task(self):
        if self.worker is not None and hasattr(self.worker, "stop"):
            self.worker.stop()
            self.say(tr("正在停止…"))

    # ---- copy / export ------------------------------------------------------------------------
    def copy_results(self):
        confirmed, maybe = self.grid_ok.items, self.grid_maybe.items
        if not (confirmed or maybe):
            QMessageBox.information(self, APP, tr("冇結果可以複製。"))
            return
        try:
            run = self._ensure_run(self.folders())
        except Exception as e:
            QMessageBox.critical(self, APP, str(e))
            return
        self.set_busy(True)
        self.scan_panel.start(tr("複製結果"))
        self.worker = workers.CopyWorker(confirmed, maybe, run["run_dir"], self.folders())
        self.worker.progress.connect(self._scan_progress)
        self.worker.done.connect(self._copy_done)
        self.worker.failed.connect(self._task_failed)
        self.worker.start()

    def _copy_done(self, counts, log):
        if self._closed:
            return
        self.set_busy(False)
        msg = tr("複製完成 {c};記錄:{log}", c=counts, log=log)
        self.scan_panel.finish(tr("複製完成"), msg)
        self.say(msg)
        self.notify(tr("複製完成"))

    def export_final(self):
        """Copy the reviewed confirmed set into <search>\\final\\ (copy only; nothing else is touched)."""
        if self.run is None:
            QMessageBox.information(self, APP, tr("請先完成一次搜尋,再匯出最終結果。"))
            return
        items = list(self.grid_ok.items)
        if not items:
            QMessageBox.information(self, APP, tr("冇確認嘅相可以匯出。"))
            return
        final_dir = os.path.join(self.run["run_dir"], copier.FINAL_DIR)
        ask = QMessageBox.question(self, APP, tr("會將 {n} 張確認相複製到\n{d}\\。待確認嘅 {m} 張同已排除嘅唔會包括。原相唔會改動。",
                                                 n=len(items), d=final_dir, m=len(self.grid_maybe.items)))
        if ask != QMessageBox.Yes:
            return
        try:
            copier.validate_output_root(self.run["run_dir"], self.folders())
        except Exception as e:
            QMessageBox.critical(self, APP, str(e))
            return
        self.set_busy(True)
        self.scan_panel.start(tr("匯出最終結果"))
        self.worker = workers.ExportWorker(items, self.run["run_dir"], self.folders())
        self.worker.progress.connect(self._scan_progress)
        self.worker.done.connect(self._export_done)
        self.worker.failed.connect(self._task_failed)
        self.worker.start()

    def _export_done(self, counts, log):
        if self._closed:
            return
        self.set_busy(False)
        n = counts.get("copied", 0) + counts.get("already_there", 0)
        msg = tr("匯出完成 {c};記錄:{log}", c=counts, log=log)
        self.scan_panel.finish(tr("匯出完成"), msg)
        self.say(msg)
        self.notify(tr("已匯出 {n} 張到 final 資料夾", n=n), 5000)
        QApplication.alert(self)
        final_dir = os.path.join(self.run["run_dir"], copier.FINAL_DIR) if self.run else ""
        if final_dir and os.path.isdir(final_dir) and QMessageBox.question(
                self, APP, tr("匯出完成。要開啟 final 資料夾嗎?")) == QMessageBox.Yes:
            os.startfile(final_dir)

    def export_unchecked(self):
        rows = self.index.paths_with_status("noface", "error", "unsupported")
        if not rows:
            QMessageBox.information(self, APP, tr("冇無法檢查嘅相。"))
            return
        try:
            root = self.run["run_dir"] if self.run else self.output_root()
            copier.validate_output_root(root, self.folders())
            log = copier.write_csv(copier.unique_path(root, "unchecked_photos", ".csv"), ["path", "status"], rows, root)
            self.say(tr("已匯出 {n} 張:{log}", n=len(rows), log=log))
            self.notify(tr("已匯出無法檢查清單"))
        except Exception as e:
            QMessageBox.critical(self, APP, str(e))

    # ---- close --------------------------------------------------------------------------------
    def closeEvent(self, e):
        self.save_settings()
        if self.worker is not None and self.worker.isRunning():
            self.stop_task()
            if not self.worker.wait(15000):
                e.ignore()  # still busy (e.g. a very large photo): keep the window, never cut the worker off
                self.say(tr("仍然喺度停止中,請稍後再關閉。"))
                return
        self.pool.waitForDone(5000)  # let thumbnail tasks finish before the window goes away
        self._closed = True
        self.index.close()
        super().closeEvent(e)
