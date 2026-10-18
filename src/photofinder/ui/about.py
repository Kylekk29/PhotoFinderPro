"""About box and the two web links. Clicking a link only hands the address to the user's browser;
the app itself never makes a network request."""
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout

from .. import APP_NAME, __version__, theme
from ..i18n import tr
from .common import button, label

REPO_URL = "https://github.com/Kylekk29/PhotoFinderPro"
RELEASES_URL = REPO_URL + "/releases"
NOTICES = "THIRD_PARTY_NOTICES.txt"


def open_url(url):
    QDesktopServices.openUrl(QUrl(url))


def find_notices():
    """THIRD_PARTY_NOTICES.txt next to the exe (installed / zip), inside the portable bundle, or the repo root
    when run from source. None if it is not there."""
    if getattr(sys, "frozen", False):
        dirs = [Path(sys.executable).parent, Path(getattr(sys, "_MEIPASS", sys.executable))]
    else:
        dirs = [Path(__file__).resolve().parents[3]]
    return next((d / NOTICES for d in dirs if (d / NOTICES).is_file()), None)


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        from ..app import asset_path
        self.setWindowTitle(tr("關於 Photo Finder Pro"))
        self.setFixedWidth(420)
        icon = label("")
        icon.setPixmap(QIcon(str(asset_path("app.ico"))).pixmap(72, 72))
        icon.setAlignment(Qt.AlignCenter)
        name = label(APP_NAME, "brand")
        name.setAlignment(Qt.AlignCenter)
        ver = label(tr("版本 {v}", v=__version__), "hint")
        ver.setAlignment(Qt.AlignCenter)
        offline = label(tr("100% 離線運作:程式本身唔會連線上網,冇追蹤,冇上載。"), "", wrap=True)
        offline.setAlignment(Qt.AlignCenter)
        lic = label(tr("MIT 授權 · 免費開源"), "hint")
        lic.setAlignment(Qt.AlignCenter)
        self.b_github = button("GitHub", tip=tr("喺瀏覽器開啟專案網頁"))
        self.b_github.clicked.connect(lambda: open_url(REPO_URL))
        self.b_notices = button(tr("第三方授權聲明"), tip=tr("開啟 THIRD_PARTY_NOTICES.txt"))
        self.notices = find_notices()
        self.b_notices.setVisible(self.notices is not None)
        self.b_notices.clicked.connect(self._open_notices)
        b_close = button(tr("關閉"), "primary", color="#ffffff")
        b_close.clicked.connect(self.accept)
        links = QHBoxLayout()
        links.setSpacing(8)
        links.addStretch(1)
        links.addWidget(self.b_github)
        links.addWidget(self.b_notices)
        links.addStretch(1)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 20)
        lay.setSpacing(8)
        for w in (icon, name, ver):
            lay.addWidget(w)
        lay.addSpacing(6)
        lay.addWidget(offline)
        lay.addWidget(lic)
        lay.addSpacing(10)
        lay.addLayout(links)
        lay.addSpacing(8)
        lay.addWidget(b_close)

    def _open_notices(self):
        if self.notices is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.notices)))
