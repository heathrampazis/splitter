"""
Palette and stylesheet for the player.

Shares its colours with Splitter Studio on the Mac so the two halves of
the project look like one product. Everything is sized for fingers: the
smallest touch target here is 64 px.

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

# One colour per stem group, so a glance says which is which.
STEM_COLOURS = {
    "vocals": "#3fbbec",
    "drums": "#e0a44c",
    "instrumental": "#55c48f",
}

# Smallest comfortable touch target.
TOUCH = 64


_TEMPLATE = Template("""
QWidget {
    background: $ground;
    color: $text;
    font-family: sans-serif;
    font-size: 18px;
}

/* ---- playback screen: info bar ---- */

QFrame#infoBar, QFrame#statusBar {
    background: $panel;
    border: 1px solid $line;
    border-radius: 12px;
}

QLabel#songName {
    color: $text;
    font-size: 30px;
    font-weight: 600;
    background: transparent;
}

QLabel#bpm {
    color: $accent;
    font-size: 44px;
    font-weight: 700;
    background: transparent;
}

QLabel#caption {
    color: $textFaint;
    font-size: 15px;
    font-weight: 600;
    background: transparent;
}

QLabel#tempo {
    color: $text;
    font-size: 24px;
    font-weight: 600;
    background: transparent;
}

QLabel#time {
    color: $textDim;
    font-size: 24px;
    background: transparent;
}

/* ---- playback screen: status bar ---- */

QLabel#playState {
    color: $textFaint;
    font-size: 20px;
    font-weight: 700;
    background: transparent;
}

QLabel#playState[state="playing"] {
    color: $green;
}

QLabel#playState[state="paused"] {
    color: $amber;
}

QLabel#stemChip {
    color: $textFaint;
    background: $ground;
    border: 2px solid $line;
    border-radius: 10px;
    font-size: 18px;
    font-weight: 700;
    padding: 10px 18px;
}

QLabel#stemChip[on="true"][stem="vocals"] {
    color: $vocals;
    border-color: $vocals;
}

QLabel#stemChip[on="true"][stem="drums"] {
    color: $drums;
    border-color: $drums;
}

QLabel#stemChip[on="true"][stem="instrumental"] {
    color: $instrumental;
    border-color: $instrumental;
}

/* ---- buttons ---- */

QPushButton {
    background: $panelRaised;
    border: 1px solid $lineBright;
    border-radius: 10px;
    color: $text;
    font-size: 20px;
    font-weight: 700;
    min-height: ${touch}px;
    padding: 0 22px;
}

QPushButton:pressed {
    background: $accentDeep;
    border: 1px solid $accent;
    color: $accent;
}

QPushButton#songsButton {
    min-width: 150px;
}

QPushButton#zoomButton {
    background: rgba(24, 28, 33, 210);
    border: 1px solid $lineBright;
    font-size: 17px;
    padding: 0 12px;
}

/* ---- track browser page ---- */

QLabel#usbStatus {
    color: $textDim;
    font-size: 18px;
    font-weight: 600;
    background: transparent;
    padding: 6px;
}

QLabel#browserTitle {
    color: $textFaint;
    font-size: 15px;
    font-weight: 600;
    background: transparent;
}

QListWidget {
    background: $panel;
    border: 1px solid $line;
    border-radius: 12px;
    color: $text;
    font-size: 22px;
    outline: none;
}

QListWidget::item {
    padding: 18px 16px;
    border-bottom: 1px solid $line;
}

QListWidget::item:selected {
    background: $accentDeep;
    color: $accent;
}

/* ---- scrollbar ---- */

QScrollBar:vertical {
    background: transparent;
    width: 14px;
}

QScrollBar::handle:vertical {
    background: $lineBright;
    border-radius: 7px;
    min-height: 60px;
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
    green=GREEN,
    vocals=STEM_COLOURS["vocals"],
    drums=STEM_COLOURS["drums"],
    instrumental=STEM_COLOURS["instrumental"],
    touch=TOUCH,
)
