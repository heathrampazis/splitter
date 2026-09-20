"""
Colour palette and application stylesheet.

Qt stylesheets support only a subset of CSS. There is no letter-spacing,
no text-transform, no box-shadow and no transitions, so anything needing
those is handled on the widgets themselves: labels are uppercased in
Python, tracking is set through QFont, and depth comes from borders and
background contrast rather than shadows.
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

# One accent, used sparingly. Borrowed from the jog ring on the deck.
ACCENT = "#3fbbec"
ACCENT_DEEP = "#12323f"
ACCENT_LINE = "#1f5f7a"

AMBER = "#e0a44c"
GREEN = "#55c48f"
RED = "#ea7d70"

FONT = '"SF Pro Text", "Helvetica Neue", Arial, sans-serif'
MONO = '"SF Mono", "Menlo", monospace'


_TEMPLATE = Template("""
QWidget {
    background: $ground;
    color: $text;
    font-family: $font;
    font-size: 13px;
}

/* ---- header ---- */

QFrame#header {
    background: $panel;
    border-bottom: 1px solid $line;
}

QLabel#wordmark {
    color: $text;
    font-size: 19px;
    font-weight: 600;
    background: transparent;
}

QLabel#tagline {
    color: $textFaint;
    font-size: 12px;
    background: transparent;
}

QLabel#statusPill {
    color: $textDim;
    background: $panelRaised;
    border: 1px solid $line;
    border-radius: 11px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 600;
}

QLabel#statusPill[busy="true"] {
    color: $accent;
    background: $accentDeep;
    border: 1px solid $accentLine;
}

/* ---- drop zone ---- */

QFrame#dropZone {
    background: $panel;
    border: 2px dashed $lineBright;
    border-radius: 10px;
}

QFrame#dropZone[hover="true"] {
    background: $accentDeep;
    border: 2px dashed $accent;
}

QLabel#dropTitle {
    color: $text;
    font-size: 17px;
    font-weight: 500;
    background: transparent;
}

QLabel#dropHint {
    color: $textFaint;
    font-size: 12px;
    background: transparent;
}

QFrame#dropZone[hover="true"] QLabel#dropTitle { color: $accent; }
QFrame#dropZone[hover="true"] QLabel#dropHint { color: $accent; }

/* ---- destination strip ---- */

QFrame#destStrip {
    background: $panel;
    border: 1px solid $line;
    border-radius: 8px;
}

QLabel#destLabel {
    color: $textFaint;
    font-size: 11px;
    font-weight: 600;
    background: transparent;
}

QLabel#destPath {
    color: $text;
    font-family: $mono;
    font-size: 12px;
    background: transparent;
}

QLabel#destPath[unset="true"] {
    color: $amber;
    font-family: $font;
}

/* ---- section headings ---- */

QLabel#sectionLabel {
    color: $textFaint;
    font-size: 11px;
    font-weight: 600;
    background: transparent;
}

QLabel#sectionCount {
    color: $textFaint;
    font-family: $mono;
    font-size: 11px;
    background: transparent;
}

QLabel#emptyState {
    color: $textFaint;
    font-size: 13px;
    background: transparent;
}

/* ---- buttons ---- */

QPushButton {
    background: $panelRaised;
    color: $text;
    border: 1px solid $lineBright;
    border-radius: 6px;
    padding: 7px 16px;
    font-size: 12px;
    font-weight: 500;
}

QPushButton:hover {
    background: $panelHover;
    border: 1px solid $textFaint;
}

QPushButton:pressed {
    background: $ground;
}

QPushButton#accentButton {
    background: $accentDeep;
    color: $accent;
    border: 1px solid $accentLine;
}

QPushButton#accentButton:hover {
    background: $accentLine;
    color: $text;
}

/* ---- queue rows ---- */

QFrame#jobRow {
    background: $panel;
    border: 1px solid $line;
    border-radius: 8px;
}

QFrame#jobRow[active="true"] {
    background: $panelRaised;
    border: 1px solid $accentLine;
}

QLabel#jobName {
    color: $text;
    font-size: 13px;
    background: transparent;
}

QLabel#jobStatus {
    color: $textDim;
    font-size: 11px;
    font-weight: 600;
    background: transparent;
}

QLabel#jobDot {
    border-radius: 4px;
    background: $textFaint;
}

QProgressBar {
    background: $ground;
    border: none;
    border-radius: 2px;
    height: 4px;
}

QProgressBar::chunk {
    background: $accent;
    border-radius: 2px;
}

/* ---- scroll area ---- */

QScrollArea {
    background: transparent;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background: transparent;
}

QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: $lineBright;
    border-radius: 5px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background: $textFaint;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: transparent;
}

/* ---- dialogs ---- */

QMessageBox {
    background: $panel;
}

QMessageBox QLabel {
    color: $text;
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
    font=FONT,
    mono=MONO,
)
