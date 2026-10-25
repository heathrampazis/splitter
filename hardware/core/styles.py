"""
Palette and stylesheet for the player.

Shares its colours with Splitter Studio on the Mac so the two halves of
the project look like one product. Everything is sized for fingers: the
smallest touch target here is 56 px.

Qt stylesheets are not CSS. There is no letter-spacing, no shadow and no
transition, so anything needing those is handled on the widgets.
"""

from string import Template

# Surfaces, darkest to lightest.
GROUND = "#101316"
PANEL = "#181c21"
PANEL_RAISED = "#1f242a"
PANEL_HOVER = "#262c33"

LINE = "#262c33"
LINE_BRIGHT = "#333b44"

TEXT = "#e6eaee"
TEXT_DIM = "#8b959f"
TEXT_FAINT = "#5f6a75"

ACCENT = "#3fbbec"
ACCENT_DEEP = "#12323f"
ACCENT_LINE = "#1f5f7a"

AMBER = "#e0a44c"
GREEN = "#55c48f"
RED = "#ea7d70"

# One colour per stem, so a glance at the faders says which is which.
STEM_COLOURS = {
    "vocals": "#3fbbec",
    "drums": "#e0a44c",
    "bass": "#55c48f",
    "other": "#a98bd8",
}

# Smallest comfortable touch target.
TOUCH = 56


_TEMPLATE = Template("""
QWidget {
    background: $ground;
    color: $text;
    font-family: sans-serif;
    font-size: 14px;
}

/* ---- text ---- */

QLabel#songName {
    color: $text;
    font-size: 20px;
    font-weight: 600;
    background: transparent;
}

QLabel#bpm {
    color: $accent;
    font-size: 17px;
    font-weight: 600;
    background: transparent;
}

QLabel#time {
    color: $textDim;
    font-size: 16px;
    background: transparent;
}

QLabel#stemLabel {
    color: $textFaint;
    font-size: 11px;
    font-weight: 600;
    background: transparent;
}

QLabel#stemValue {
    color: $textDim;
    font-size: 12px;
    background: transparent;
}

QLabel#tempoValue {
    color: $text;
    font-size: 13px;
    font-weight: 600;
    background: transparent;
}

QLabel#usbStatus {
    color: $textDim;
    font-size: 14px;
    font-weight: 600;
    background: transparent;
    padding: 6px;
}

QLabel#browserTitle {
    color: $textFaint;
    font-size: 12px;
    font-weight: 600;
    background: transparent;
}

/* ---- panels ---- */

QFrame#topBar {
    background: $panel;
    border-bottom: 1px solid $line;
}

QFrame#mixer {
    background: $panel;
    border: 1px solid $line;
    border-radius: 10px;
}

/* ---- buttons ---- */

QPushButton {
    background: $panelRaised;
    border: 1px solid $lineBright;
    border-radius: 8px;
    color: $text;
    font-size: 14px;
    font-weight: 600;
    min-height: ${touch}px;
    padding: 0 14px;
}

QPushButton:pressed {
    background: $accentDeep;
    border: 1px solid $accent;
    color: $accent;
}

QPushButton#playButton {
    background: $accentDeep;
    border: 1px solid $accentLine;
    color: $accent;
    font-size: 19px;
}

QPushButton#playButton:pressed {
    background: $accent;
    color: $ground;
}

QPushButton#playButton[playing="true"] {
    background: $accent;
    border: 1px solid $accent;
    color: $ground;
}

/* ---- faders ---- */

QSlider::groove:vertical {
    width: 6px;
    background: $ground;
    border-radius: 3px;
}

QSlider::handle:vertical {
    height: 30px;
    margin: 0 -15px;
    border-radius: 7px;
    background: $textDim;
    border: 1px solid $lineBright;
}

QSlider::groove:horizontal {
    height: 6px;
    background: $ground;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    width: 34px;
    margin: -14px 0;
    border-radius: 7px;
    background: $textDim;
    border: 1px solid $lineBright;
}

QSlider::sub-page:vertical {
    background: $lineBright;
    border-radius: 3px;
}

/* ---- track list ---- */

QListWidget {
    background: $panel;
    border: 1px solid $line;
    border-radius: 10px;
    color: $text;
    font-size: 17px;
    outline: none;
}

QListWidget::item {
    padding: 16px 14px;
    border-bottom: 1px solid $line;
}

QListWidget::item:selected {
    background: $accentDeep;
    color: $accent;
}

/* ---- scrollbar ---- */

QScrollBar:vertical {
    background: transparent;
    width: 12px;
}

QScrollBar::handle:vertical {
    background: $lineBright;
    border-radius: 6px;
    min-height: 50px;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: transparent;
}
""")


APP_STYLE = _TEMPLATE.substitute(
    ground=GROUND,
    panel=PANEL,
    panelRaised=PANEL_RAISED,
    panelHover=PANEL_HOVER,
    line=LINE,
    lineBright=LINE_BRIGHT,
    text=TEXT,
    textDim=TEXT_DIM,
    textFaint=TEXT_FAINT,
    accent=ACCENT,
    accentDeep=ACCENT_DEEP,
    accentLine=ACCENT_LINE,
    amber=AMBER,
    touch=TOUCH,
)
