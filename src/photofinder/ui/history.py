"""Past searches: each has its own results folder and reference faces. Type to filter."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from ..i18n import tr
from . import icons
from .common import button, label
from .. import theme


class HistoryPanel(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win, self.runs, self.current = win, [], None
        self.filter = QLineEdit()
        self.filter.setPlaceholderText(tr("搜尋歷史:名、日期、資料夾…"))
        self.filter.setClearButtonEnabled(True)
        self.filter.textChanged.connect(self._apply)
        self.list = QListWidget()
        self.list.setObjectName("history")
        self.list.setSpacing(2)
        self.list.itemDoubleClicked.connect(lambda _i: self.win.open_selected_run())
        self.empty = QWidget()
        el = QVBoxLayout(self.empty)
        el.addStretch(1)
        self.empty_icon = label("")
        self.empty_icon.setAlignment(Qt.AlignCenter)
        self.empty_title = label(tr("未有搜尋紀錄"), "emptytitle")
        self.empty_title.setAlignment(Qt.AlignCenter)
        self.empty_text = label(tr("完成一次搜尋之後會喺呢度出現。"), "empty", wrap=True)
        self.empty_text.setAlignment(Qt.AlignCenter)
        for w in (self.empty_icon, self.empty_title, self.empty_text):
            el.addWidget(w)
            el.addSpacing(6)
        el.addStretch(2)
        self.b_open = button(tr("開啟呢個搜尋"), "primary")
        self.b_folder = button(tr("開啟結果資料夾"), icon="open")
        self.b_forget = button(tr("移除紀錄"), "ghost", icon="trash", tip=tr("只係移除紀錄,唔會刪除結果資料夾同相片"))
        self.b_open.clicked.connect(self.win.open_selected_run)
        self.b_folder.clicked.connect(self.win.open_selected_run_folder)
        self.b_forget.clicked.connect(self.win.forget_selected_run)
        row = QHBoxLayout()
        row.addWidget(self.b_forget)
        row.addStretch(1)
        row.addWidget(self.b_folder)
        row.addWidget(self.b_open)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 6, 0, 0)
        lay.addWidget(self.filter)
        lay.addWidget(self.list, 1)
        lay.addWidget(self.empty, 1)
        lay.addLayout(row)
        self.paint_empty()

    def paint_empty(self):
        self.empty_icon.setPixmap(icons.pixmap("history", theme.C["faint"], 48))

    def reload(self, runs, current):
        self.runs, self.current = runs, current
        self._apply()

    def _apply(self, *_):
        text = self.filter.text().strip().lower()
        self.list.clear()
        for r in self.runs:
            hay = " ".join([r["name"], r["created"], " ".join(r["folders"]), r["run_dir"]]).lower()
            if text and text not in hay:
                continue
            mark = "● " if r["id"] == self.current else ""
            state = "" if r["finished"] else "   " + tr("(未完成)")
            it = QListWidgetItem(f"{mark}{r['name']}    {r['created'][:16]}    "
                                 f"{tr('{c} 確認 / {m} 待確認', c=r['confirmed'], m=r['maybe'])}{state}\n"
                                 f"{'; '.join(r['folders'])}")
            it.setData(Qt.UserRole, r["id"])
            it.setToolTip(r["run_dir"])
            self.list.addItem(it)
        none = self.list.count() == 0
        self.empty.setVisible(none)
        self.list.setVisible(not none)

    def selected_id(self):
        items = self.list.selectedItems()
        return items[0].data(Qt.UserRole) if items else None

    def set_enabled(self, enabled):
        for b in (self.b_open, self.b_folder, self.b_forget):
            b.setEnabled(enabled)
