from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontMetrics
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QProgressBar,
                               QPushButton)

from gui import theme

# Dot colour per state. Waiting stays deliberately quiet so a queue of
# twenty tracks does not look like twenty things demanding attention.
DOT_COLOURS = {
    "Waiting": theme.TEXT_FAINT,
    "In Progress": theme.ACCENT,
    "Complete": theme.GREEN,
    "Failed": theme.RED,
}


# A label that shortens its text from the middle when space runs out.
#
# Track names are long and the interesting part is usually at both ends,
# so trimming the middle beats letting the layout clip the end.
class ElidingLabel(QLabel):
    def __init__(self, text=""):
        super().__init__()
        self.full_text = text
        self.setText(text)

    def setText(self, text):
        self.full_text = text
        super().setText(text)
        self.apply_elide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.apply_elide()

    def apply_elide(self):
        metrics = QFontMetrics(self.font())
        width = max(0, self.width())

        super().setText(
            metrics.elidedText(self.full_text, Qt.ElideMiddle, width)
        )


# Represents one audio job in the UI.
class JobWidget(QFrame):
    def __init__(self, filepath):
        super().__init__()
        self.filepath = filepath
        self.setObjectName("jobRow")
        self.build_ui()
        self.set_status("Waiting")

    # Builds the layout and widgets for the job.
    def build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 11, 12, 11)
        layout.setSpacing(12)

        # State shows as a coloured dot as well as words, so the queue can
        # be read at a glance without parsing text.
        self.dot = QLabel()
        self.dot.setObjectName("jobDot")
        self.dot.setFixedSize(8, 8)

        self.filename = ElidingLabel(Path(self.filepath).name)
        self.filename.setObjectName("jobName")
        self.filename.setToolTip(self.filepath)
        self.filename.setMinimumWidth(120)

        # Demucs runs in a subprocess and reports nothing back, so there is
        # no percentage to show. A range of 0-0 makes Qt draw a moving
        # indicator instead, which says "working" without inventing a number.
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.setFixedSize(120, 4)
        self.progress.hide()

        self.status = QLabel()
        self.status.setObjectName("jobStatus")
        self.status.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.status.setMinimumWidth(90)
        self.tighten(self.status, 0.8)

        # Hidden until the job finishes successfully.
        self.transfer_button = QPushButton("Transfer")
        self.transfer_button.setObjectName("accentButton")
        self.transfer_button.setCursor(Qt.PointingHandCursor)
        self.transfer_button.hide()

        layout.addWidget(self.dot)
        layout.addWidget(self.filename, 1)
        layout.addWidget(self.progress)
        layout.addWidget(self.status)
        layout.addWidget(self.transfer_button)

    # Qt stylesheets cannot set letter spacing, so it goes on the font.
    def tighten(self, widget, spacing):
        font = widget.font()
        font.setLetterSpacing(QFont.AbsoluteSpacing, spacing)
        widget.setFont(font)

    # Updates the status text, the dot and the busy indicator.
    def set_status(self, status):
        self.status.setText(status.upper())

        colour = DOT_COLOURS.get(status, theme.TEXT_FAINT)
        self.dot.setStyleSheet(f"border-radius:4px; background:{colour};")

        if status == "Complete":
            self.status.setStyleSheet(f"color:{theme.GREEN};")
        elif status == "Failed":
            self.status.setStyleSheet(f"color:{theme.RED};")
        elif status == "In Progress":
            self.status.setStyleSheet(f"color:{theme.ACCENT};")
        else:
            self.status.setStyleSheet(f"color:{theme.TEXT_FAINT};")

        running = status == "In Progress"

        self.progress.setVisible(running)
        self.set_active(running)

    # Lifts the running row out of the queue visually.
    def set_active(self, active):
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)

    # Shows the transfer button after successful processing.
    def show_transfer_button(self):
        self.transfer_button.show()
