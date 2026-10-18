"""Look of the app: one set of colour tokens per mode (dark / light) and one stylesheet built from them."""
GOOD = "#22c55e"
WARN = "#f59e0b"
DANGER = "#ef4444"
ACCENT = "#5b8cff"
ACCENT2 = "#8b5cf6"   # end of the brand gradient

PALETTES = {
    "dark": {
        "bg": "#0b0d12", "panel": "#11141b", "card": "#171b24", "raised": "#1e2330", "hover": "#252b3a",
        "border": "#232937", "border_hi": "#343c50", "text": "#eef1f7", "muted": "#8b94a8", "faint": "#596178",
        "accent": ACCENT, "accent_hover": "#7aa2ff", "accent_soft": "rgba(91,140,255,0.16)",
        "thumb": "#1f2430", "viewer": "#05070b", "scroll": "#353d52", "tooltip": "#000000",
    },
    "light": {
        "bg": "#f5f6fa", "panel": "#ffffff", "card": "#ffffff", "raised": "#f0f2f7", "hover": "#e8ebf3",
        "border": "#e2e6ee", "border_hi": "#c9cfdc", "text": "#141824", "muted": "#626b7f", "faint": "#a2a9b8",
        "accent": "#3b6cf6", "accent_hover": "#2f5be0", "accent_soft": "rgba(59,108,246,0.12)",
        "thumb": "#e9ecf3", "viewer": "#0b0d12", "scroll": "#c3c9d6", "tooltip": "#141824",
    },
}

mode = "dark"
C = dict(PALETTES["dark"])


def set_mode(m):
    """Switch the colour tokens in place (C stays the same dict, so modules holding it see the change)."""
    global mode
    mode = m if m in PALETTES else "dark"
    C.clear()
    C.update(PALETTES[mode])


def qss():
    c = C
    return f"""
QWidget {{ background: {c['bg']}; color: {c['text']}; }}
QLabel {{ background: transparent; }}
QToolTip {{ background: {c['tooltip']}; color: #ffffff; border: none; padding: 5px 9px; border-radius: 6px; }}

QFrame#topbar {{ background: {c['panel']}; border-bottom: 1px solid {c['border']}; }}
QFrame#sidebar {{ background: {c['panel']}; border-right: 1px solid {c['border']}; }}
QFrame#footer {{ background: {c['panel']}; border-top: 1px solid {c['border']}; }}
QScrollArea#sidescroll, QWidget#sideinner {{ background: {c['panel']}; border: none; }}
QFrame#topbar QLabel, QFrame#footer QWidget {{ background: transparent; }}

QLabel#brand {{ font-size: 16px; font-weight: 700; }}
QLabel#brandsub {{ color: {c['muted']}; font-size: 11px; }}
QLabel#section {{ font-size: 13px; font-weight: 700; }}
QLabel#hint {{ color: {c['muted']}; font-size: 12px; }}
QLabel#faint {{ color: {c['faint']}; font-size: 11px; }}
QLabel#value {{ color: {c['text']}; font-weight: 700; min-width: 36px; }}
QLabel#empty {{ color: {c['muted']}; font-size: 14px; }}
QLabel#emptytitle {{ color: {c['text']}; font-size: 20px; font-weight: 700; }}
QLabel#status {{ color: {c['muted']}; font-size: 12px; }}
QLabel#stepnum {{ background: {c['raised']}; color: {c['muted']}; border-radius: 11px; font-weight: 700;
                  font-size: 11px; min-width: 22px; max-width: 22px; min-height: 22px; max-height: 22px; }}
QLabel#stepnum[done="true"] {{ background: {GOOD}; color: #ffffff; }}
QLabel#bignum {{ font-size: 22px; font-weight: 700; }}
QLabel#statlabel {{ color: {c['muted']}; font-size: 11px; }}

QFrame#card {{ background: {c['card']}; border: 1px solid {c['border']}; border-radius: 14px; }}
QFrame#card QWidget {{ background: transparent; }}
QFrame#card QListWidget, QFrame#card QLineEdit {{ background: {c['raised']}; }}
QFrame#scanpanel {{ background: {c['card']}; border: 1px solid {c['border']}; border-radius: 14px; }}
QFrame#scanpanel QWidget {{ background: transparent; }}
QFrame#selbar {{ background: {c['raised']}; border: 1px solid {c['accent']}; border-radius: 14px; }}
QFrame#selbar QWidget {{ background: transparent; }}
QFrame#selbar QLabel {{ font-weight: 700; }}
QFrame#namebox {{ background: {c['raised']}; border: 1px solid {c['border']}; border-radius: 10px; }}
QFrame#namebox QLineEdit {{ background: transparent; border: none; font-size: 14px; font-weight: 600; padding: 4px; }}
QFrame#namebox QWidget {{ background: transparent; }}
QLabel#toast {{ background: {c['tooltip'] if mode == 'dark' else '#141824'}; color: #ffffff; border-radius: 12px;
                padding: 11px 18px; font-weight: 600; border: 1px solid {c['border_hi'] if mode == 'dark' else '#141824'}; }}
QLabel#dropveil {{ background: rgba(91,140,255,0.18); border: 3px dashed {c['accent']}; border-radius: 18px;
                   color: {c['text']}; font-size: 20px; font-weight: 700; }}

QPushButton {{ background: {c['raised']}; border: 1px solid {c['border']}; border-radius: 9px; padding: 7px 14px;
               font-weight: 600; }}
QPushButton:hover {{ background: {c['hover']}; border-color: {c['border_hi']}; }}
QPushButton:pressed {{ background: {c['border']}; }}
QPushButton:disabled {{ color: {c['faint']}; background: {c['panel']}; border-color: {c['border']}; }}
QPushButton#primary {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {c['accent']}, stop:1 {ACCENT2});
                       color: #ffffff; border: none; font-weight: 700; padding: 9px 22px; }}
QPushButton#primary:hover {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {c['accent_hover']}, stop:1 #9d74fa); }}
QPushButton#primary:disabled {{ background: {c['raised']}; color: {c['faint']}; }}
QPushButton#danger {{ color: {DANGER}; background: transparent; border: 1px solid rgba(239,68,68,0.45); }}
QPushButton#danger:hover {{ background: rgba(239,68,68,0.12); }}
QPushButton#danger:disabled {{ color: {c['faint']}; border-color: {c['border']}; }}
QPushButton#ghost {{ background: transparent; border: none; color: {c['muted']}; padding: 7px 10px; }}
QPushButton#ghost:hover {{ color: {c['text']}; background: {c['hover']}; }}
QPushButton#ghost:disabled {{ color: {c['faint']}; }}
QPushButton#icon {{ background: transparent; border: 1px solid transparent; border-radius: 9px; padding: 6px; }}
QPushButton#icon:hover {{ background: {c['hover']}; }}
QPushButton#yes {{ background: rgba(34,197,94,0.14); color: {GOOD}; border: 1px solid rgba(34,197,94,0.45); }}
QPushButton#yes:hover {{ background: rgba(34,197,94,0.24); }}
QPushButton#yes:disabled, QPushButton#no:disabled {{ background: transparent; color: {c['faint']}; border-color: {c['border']}; }}
QPushButton#no {{ background: rgba(239,68,68,0.12); color: {DANGER}; border: 1px solid rgba(239,68,68,0.40); }}
QPushButton#no:hover {{ background: rgba(239,68,68,0.22); }}
QPushButton#seg {{ background: transparent; border: none; border-radius: 7px; padding: 6px 4px; color: {c['muted']}; }}
QPushButton#seg:hover {{ color: {c['text']}; }}
QPushButton#seg:checked {{ background: {c['card']}; color: {c['text']}; border: 1px solid {c['border_hi']}; }}
QFrame#segbar {{ background: {c['raised']}; border-radius: 9px; }}
QFrame#segbar QWidget {{ background: transparent; }}

QLineEdit {{ background: {c['raised']}; border: 1px solid {c['border']}; border-radius: 9px; padding: 7px 9px;
             selection-background-color: {c['accent']}; }}
QLineEdit:focus {{ border-color: {c['accent']}; }}
QListWidget {{ background: {c['raised']}; border: 1px solid {c['border']}; border-radius: 10px; padding: 4px; outline: 0; }}
QListWidget#grid, QListWidget#avatars, QListWidget#history {{ background: transparent; border: none; }}
QListWidget::item {{ border-radius: 8px; padding: 3px; color: {c['text']}; }}
QListWidget::item:selected {{ background: {c['accent_soft']}; color: {c['text']}; }}
QListWidget::item:hover:!selected {{ background: {c['hover']}; }}
QListWidget#grid::item {{ padding: 4px; border-radius: 14px; border: 2px solid transparent; }}
QListWidget#grid::item:selected {{ background: {c['accent_soft']}; border: 2px solid {c['accent']}; }}
QListWidget#grid::item:hover:!selected {{ background: {c['hover']}; }}
QListWidget#history::item {{ background: {c['card']}; border: 1px solid {c['border']}; border-radius: 12px;
                             margin: 3px 0; padding: 8px 12px; }}
QListWidget#history::item:selected {{ border: 1px solid {c['accent']}; background: {c['accent_soft']}; }}
QListWidget#history::item:hover:!selected {{ border-color: {c['border_hi']}; }}
QListWidget#history QWidget {{ background: transparent; }}

QTabWidget::pane {{ border: none; background: transparent; }}
QTabBar {{ background: transparent; }}
QTabBar::tab {{ background: transparent; padding: 7px 16px; margin-right: 4px; border-radius: 9px;
               color: {c['muted']}; font-weight: 700; }}
QTabBar::tab:selected {{ background: {c['raised']}; color: {c['text']}; }}
QTabBar::tab:hover:!selected {{ color: {c['text']}; }}

QProgressBar {{ border: none; background: {c['raised']}; border-radius: 4px; max-height: 8px; min-height: 8px;
                color: transparent; }}
QProgressBar::chunk {{ border-radius: 4px;
                       background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c['accent']}, stop:1 {ACCENT2}); }}
QSlider::groove:horizontal {{ height: 4px; background: {c['border']}; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {c['accent']}; border-radius: 2px; }}
QSlider::handle:horizontal {{ background: #ffffff; border: 1px solid {c['border_hi']}; width: 14px; height: 14px;
                              margin: -6px 0; border-radius: 8px; }}
QSlider::handle:horizontal:disabled {{ background: {c['faint']}; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {c['scroll']}; border-radius: 4px; min-height: 30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
QScrollBar:horizontal {{ height: 0; }}
QMenu {{ background: {c['card']}; border: 1px solid {c['border_hi']}; border-radius: 10px; padding: 5px; }}
QMenu::item {{ padding: 7px 18px 7px 12px; border-radius: 6px; }}
QMenu::item:selected {{ background: {c['hover']}; }}
QMenu::item:disabled {{ color: {c['faint']}; }}
QMenu::separator {{ height: 1px; background: {c['border']}; margin: 4px 6px; }}
QMessageBox {{ background: {c['card']}; }}
"""


def viewer_qss():
    c = C
    return f"""
QDialog {{ background: {c['viewer']}; color: #eef1f7; }}
QDialog QWidget {{ background: transparent; color: #eef1f7; }}
QLabel {{ background: transparent; color: #eef1f7; }}
QLabel#vpath {{ color: #8b94a8; font-size: 11px; }}
QLabel#vpill {{ border-radius: 10px; padding: 3px 10px; font-weight: 700; color: #ffffff; }}
QLabel#vcount {{ color: #8b94a8; font-weight: 600; }}
QPushButton {{ background: rgba(255,255,255,0.08); color: #eef1f7; border: 1px solid rgba(255,255,255,0.12);
               border-radius: 10px; padding: 9px 18px; font-weight: 600; }}
QPushButton:hover {{ background: rgba(255,255,255,0.16); }}
QPushButton:disabled {{ color: #4b5266; background: rgba(255,255,255,0.03); }}
QPushButton#yes {{ background: rgba(34,197,94,0.20); color: #86efac; border: 1px solid rgba(34,197,94,0.55); }}
QPushButton#yes:hover {{ background: rgba(34,197,94,0.32); }}
QPushButton#no {{ background: rgba(239,68,68,0.18); color: #fca5a5; border: 1px solid rgba(239,68,68,0.5); }}
QPushButton#no:hover {{ background: rgba(239,68,68,0.30); }}
QPushButton#primary {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {ACCENT}, stop:1 {ACCENT2});
                       color: #ffffff; border: none; font-weight: 700; padding: 9px 22px; }}
QToolTip {{ background: #000000; color: #ffffff; border: none; padding: 5px 9px; }}
"""


# Backwards-compatible names (dark mode values).
QSS = qss()
VIEWER_QSS = viewer_qss()
