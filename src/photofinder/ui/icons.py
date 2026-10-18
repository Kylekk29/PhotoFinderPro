"""Small line icons (own drawings, 24x24 SVG, stroke = colour). Rendered once per (name, colour, size)."""
from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

_PATHS = {
    "folder": '<path d="M3 7.5A2.5 2.5 0 0 1 5.5 5H9l2 2.5h7.5A2.5 2.5 0 0 1 21 10v7.5a2.5 2.5 0 0 1-2.5 2.5h-13'
              'A2.5 2.5 0 0 1 3 17.5z"/>',
    "folder-plus": '<path d="M3 7.5A2.5 2.5 0 0 1 5.5 5H9l2 2.5h7.5A2.5 2.5 0 0 1 21 10v7.5a2.5 2.5 0 0 1-2.5 2.5h-13'
                   'A2.5 2.5 0 0 1 3 17.5z"/><path d="M12 11v6M9 14h6"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 20.5c1.2-4 4.3-6 8-6s6.8 2 8 6"/>',
    "user-plus": '<circle cx="10" cy="8" r="4"/><path d="M2.5 20.5c1.1-3.8 4-5.8 7.5-5.8 1.6 0 3 .4 4.3 1.2"/>'
                 '<path d="M19 13v6M16 16h6"/>',
    "play": '<path d="M7 4.8v14.4a1 1 0 0 0 1.5.86l12-7.2a1 1 0 0 0 0-1.72l-12-7.2A1 1 0 0 0 7 4.8z" fill="{c}"/>',
    "stop": '<rect x="6" y="6" width="12" height="12" rx="2" fill="{c}"/>',
    "check": '<path d="M4.5 12.5l5 5L19.5 7"/>',
    "x": '<path d="M6 6l12 12M18 6L6 18"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M4.6 4.6l1.4 1.4M18 18l1.4 1.4M2.5 12h2'
           'M19.5 12h2M4.6 19.4L6 18M18 6l1.4-1.4"/>',
    "moon": '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/>',
    "image": '<rect x="3" y="4" width="18" height="16" rx="2.5"/><circle cx="9" cy="10" r="1.8"/>'
             '<path d="M21 16l-5-5-9 9"/>',
    "export": '<path d="M12 15V3M7.5 7.5L12 3l4.5 4.5"/><path d="M5 13v5.5A2.5 2.5 0 0 0 7.5 21h9a2.5 2.5 0 0 0 2.5-2.5V13"/>',
    "history": '<path d="M3.5 12a8.5 8.5 0 1 0 2.6-6.1L3.5 8.5"/><path d="M3.5 3.5v5h5"/><path d="M12 7.5V12l3 2"/>',
    "refresh": '<path d="M20 11a8 8 0 0 0-14.5-4.5L3.5 9"/><path d="M3.5 4v5h5"/><path d="M4 13a8 8 0 0 0 14.5 4.5'
               'L20.5 15"/><path d="M20.5 20v-5h-5"/>',
    "more": '<circle cx="5.5" cy="12" r="1.3" fill="{c}"/><circle cx="12" cy="12" r="1.3" fill="{c}"/>'
            '<circle cx="18.5" cy="12" r="1.3" fill="{c}"/>',
    "trash": '<path d="M4 7h16M10 11v6M14 11v6M5.5 7l1 12a2 2 0 0 0 2 2h7a2 2 0 0 0 2-2l1-12M9 7V4.5h6V7"/>',
    "open": '<path d="M14 4h6v6M20 4l-9 9"/><path d="M18 14v4.5a2 2 0 0 1-2 2H5.5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2H10"/>',
    "search": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5L21 21"/>',
    "shield": '<path d="M12 3l7.5 3v5.5c0 4.6-3.2 8.3-7.5 9.5-4.3-1.2-7.5-4.9-7.5-9.5V6z"/><path d="M8.5 12l2.5 2.5 4.5-5"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.6 3.7 5.6 3.7 9s-1.2 6.4-3.7 9'
             'c-2.5-2.6-3.7-5.6-3.7-9S9.5 5.6 12 3z"/>',
    "chevron-left": '<path d="M15 5l-7 7 7 7"/>',
    "chevron-right": '<path d="M9 5l7 7-7 7"/>',
    "frame": '<path d="M4 9V5.5A1.5 1.5 0 0 1 5.5 4H9M15 4h3.5A1.5 1.5 0 0 1 20 5.5V9M20 15v3.5a1.5 1.5 0 0 1-1.5 1.5'
             'H15M9 20H5.5A1.5 1.5 0 0 1 4 18.5V15"/><circle cx="12" cy="11" r="2.5"/><path d="M8 17c.8-1.8 2.2-2.7 4-2.7'
             's3.2.9 4 2.7"/>',
    "sparkle": '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/><path d="M19 16l.7 2 2 .7-2 .7'
               '-.7 2-.7-2-2-.7 2-.7z"/>',
    "logo": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5L21 21"/><circle cx="10.5" cy="9" r="2"/>'
            '<path d="M7 14c.7-1.5 2-2.3 3.5-2.3s2.8.8 3.5 2.3"/>',
}

_cache = {}


def pixmap(name, color, size=18, dpr=2.0):
    key = (name, color, size, dpr)
    if key not in _cache:
        body = _PATHS[name].replace("{c}", color)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" '
               f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{body}</svg>')
        px = int(size * dpr)
        pm = QPixmap(px, px)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        QSvgRenderer(QByteArray(svg.encode())).render(p, QRectF(0, 0, px, px))
        p.end()
        pm.setDevicePixelRatio(dpr)
        _cache[key] = pm
    return _cache[key]


def icon(name, color, size=18):
    return QIcon(pixmap(name, color, size))
