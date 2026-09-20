from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import (QApplication, QFileDialog, QFrame, QHBoxLayout,
                               QLabel, QMainWindow, QMessageBox, QPushButton,
                               QScrollArea, QVBoxLayout, QWidget)

from core.queue_manager import QueueManager
from core.transfer import TransferManager
from gui import theme
from gui.job_widget import JobWidget

AUDIO_EXTENSIONS = [".mp3", ".wav", ".aif", ".aiff"]

# Statuses that mean a track still has work left to do.
UNFINISHED = ("Waiting", "In Progress")


# Sets letter spacing, which Qt stylesheets cannot express.
def tighten(widget, spacing):
    font = widget.font()
    font.setLetterSpacing(QFont.AbsoluteSpacing, spacing)
    widget.setFont(font)


# Handles drag-and-drop of supported audio files, and click to browse.
class DropZone(QFrame):
    def __init__(self, parent):
        super().__init__()
        self.parent_window = parent

        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(180)
        self.setCursor(Qt.PointingHandCursor)
        self.set_hover(False)

        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        self.title = QLabel("Drop audio files here")
        self.title.setObjectName("dropTitle")
        self.title.setAlignment(Qt.AlignCenter)

        self.hint = QLabel("MP3 · WAV · AIFF     or click to browse")
        self.hint.setObjectName("dropHint")
        self.hint.setAlignment(Qt.AlignCenter)
        tighten(self.hint, 0.4)

        layout.addStretch()
        layout.addWidget(self.title)
        layout.addWidget(self.hint)
        layout.addStretch()

    # Repaints the zone when a drag moves in or out.
    #
    # Qt only re-evaluates property-based selectors when the style is
    # explicitly refreshed, hence the unpolish/polish pair.
    def set_hover(self, hovering):
        self.setProperty("hover", "true" if hovering else "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self.set_hover(True)
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.set_hover(False)

    # Collect supported audio files and add them to the queue.
    def dropEvent(self, event):
        self.set_hover(False)

        files = []

        for url in event.mimeData().urls():
            filepath = url.toLocalFile()

            if Path(filepath).suffix.lower() in AUDIO_EXTENSIONS:
                files.append(filepath)

        self.parent_window.add_files(files)

    # Dragging a file in is not always convenient, so the zone doubles as
    # a browse button.
    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return

        patterns = " ".join(f"*{e}" for e in AUDIO_EXTENSIONS)

        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Choose audio files",
            "",
            f"Audio files ({patterns})"
        )

        if files:
            self.parent_window.add_files(files)


# Builds and controls the main application window.
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Splitter Studio")
        self.resize(980, 760)
        self.setMinimumSize(760, 600)

        self.jobs = {}
        self.job_status = {}
        self.destination_folder = None
        self.queue = QueueManager()
        self.transfer = TransferManager()

        self.apply_theme()
        self.build_ui()
        self.connect_queue()
        self.refresh_summary()

    # Fusion renders consistently and takes stylesheets predictably, which
    # the native macOS style does not.
    def apply_theme(self):
        app = QApplication.instance()

        if app is None:
            return

        app.setStyle("Fusion")

        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(theme.GROUND))
        palette.setColor(QPalette.WindowText, QColor(theme.TEXT))
        palette.setColor(QPalette.Base, QColor(theme.PANEL))
        palette.setColor(QPalette.AlternateBase, QColor(theme.PANEL_RAISED))
        palette.setColor(QPalette.Text, QColor(theme.TEXT))
        palette.setColor(QPalette.Button, QColor(theme.PANEL_RAISED))
        palette.setColor(QPalette.ButtonText, QColor(theme.TEXT))
        palette.setColor(QPalette.Highlight, QColor(theme.ACCENT))
        palette.setColor(QPalette.HighlightedText, QColor(theme.GROUND))
        palette.setColor(QPalette.ToolTipBase, QColor(theme.PANEL))
        palette.setColor(QPalette.ToolTipText, QColor(theme.TEXT))

        app.setPalette(palette)
        app.setStyleSheet(theme.APP_STYLE)

    # Builds the main application layout.
    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self.build_header())

        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(18)

        self.drop_zone = DropZone(self)
        layout.addWidget(self.drop_zone)

        layout.addWidget(self.build_destination_strip())
        layout.addLayout(self.build_queue_header())
        layout.addWidget(self.build_queue(), 1)

        outer.addWidget(body, 1)

    # Wordmark on the left, overall state on the right.
    def build_header(self):
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(72)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 0, 24, 0)

        titles = QVBoxLayout()
        titles.setSpacing(1)

        wordmark = QLabel("Splitter Studio")
        wordmark.setObjectName("wordmark")

        tagline = QLabel("Stem separation for the deck")
        tagline.setObjectName("tagline")

        titles.addWidget(wordmark)
        titles.addWidget(tagline)

        self.status_pill = QLabel("READY")
        self.status_pill.setObjectName("statusPill")
        tighten(self.status_pill, 0.8)

        layout.addLayout(titles)
        layout.addStretch()
        layout.addWidget(self.status_pill)

        return header

    # Shows where finished tracks will go, rather than hiding it behind a
    # button that gives no feedback once pressed.
    def build_destination_strip(self):
        strip = QFrame()
        strip.setObjectName("destStrip")

        layout = QHBoxLayout(strip)
        layout.setContentsMargins(16, 12, 12, 12)
        layout.setSpacing(14)

        label = QLabel("EXPORT TO")
        label.setObjectName("destLabel")
        tighten(label, 0.9)

        self.destination_label = QLabel("No destination selected")
        self.destination_label.setObjectName("destPath")
        self.destination_label.setProperty("unset", "true")

        self.destination_button = QPushButton("Choose…")
        self.destination_button.setCursor(Qt.PointingHandCursor)
        self.destination_button.clicked.connect(self.select_destination)

        layout.addWidget(label)
        layout.addWidget(self.destination_label, 1)
        layout.addWidget(self.destination_button)

        return strip

    def build_queue_header(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 0, 2, 0)

        label = QLabel("QUEUE")
        label.setObjectName("sectionLabel")
        tighten(label, 0.9)

        self.queue_count = QLabel("")
        self.queue_count.setObjectName("sectionCount")
        self.queue_count.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(self.queue_count)

        return layout

    def build_queue(self):
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.queue_container = QWidget()

        self.queue_layout = QVBoxLayout(self.queue_container)
        self.queue_layout.setContentsMargins(0, 0, 6, 0)
        self.queue_layout.setSpacing(8)

        self.empty_state = QLabel("Nothing queued yet")
        self.empty_state.setObjectName("emptyState")
        self.empty_state.setAlignment(Qt.AlignCenter)

        self.queue_layout.addWidget(self.empty_state)
        self.queue_layout.addStretch()

        self.scroll.setWidget(self.queue_container)

        return self.scroll

    # Connect queue signals to the appropriate UI updates.
    def connect_queue(self):
        self.queue.job_started.connect(self.job_started)
        self.queue.job_finished.connect(self.job_finished)
        self.queue.job_failed.connect(self.job_failed)

    # Opens a folder picker for the export destination.
    def select_destination(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Destination Folder"
        )

        if not folder:
            return

        self.destination_folder = folder

        # Home-relative paths are shorter and easier to recognise.
        display = folder

        try:
            display = "~/" + str(Path(folder).relative_to(Path.home()))
        except ValueError:
            pass

        self.destination_label.setText(display)
        self.destination_label.setToolTip(folder)
        self.destination_label.setProperty("unset", "false")
        self.destination_label.style().unpolish(self.destination_label)
        self.destination_label.style().polish(self.destination_label)

    # Creates a UI widget for each file and adds it to the queue.
    def add_files(self, files):
        for filepath in files:
            if filepath in self.jobs:
                continue

            widget = JobWidget(filepath)
            self.jobs[filepath] = widget
            self.job_status[filepath] = "Waiting"

            # Sits above the trailing stretch, below everything already there.
            self.queue_layout.insertWidget(
                self.queue_layout.count() - 1,
                widget
            )

            widget.transfer_button.clicked.connect(
                lambda checked=False, f=filepath: self.transfer_track(f)
            )

            self.queue.add_job(filepath)

        self.refresh_summary()

    # Applies a status to both the widget and the tally behind the header.
    def set_job_status(self, filepath, status):
        self.job_status[filepath] = status

        widget = self.jobs.get(filepath)

        if widget:
            widget.set_status(status)

        self.refresh_summary()

    # Keeps the header pill, the queue count and the empty state in step.
    def refresh_summary(self):
        total = len(self.jobs)
        pending = sum(
            1 for status in self.job_status.values() if status in UNFINISHED
        )

        self.empty_state.setVisible(total == 0)

        if total:
            self.queue_count.setText(
                f"{total} track{'s' if total != 1 else ''}"
            )
        else:
            self.queue_count.setText("")

        if pending:
            self.status_pill.setText(f"{pending} IN QUEUE")
            self.status_pill.setProperty("busy", "true")
        else:
            self.status_pill.setText("READY")
            self.status_pill.setProperty("busy", "false")

        self.status_pill.style().unpolish(self.status_pill)
        self.status_pill.style().polish(self.status_pill)

    # Update the job's UI when processing starts.
    def job_started(self, filepath):
        self.set_job_status(filepath, "In Progress")

    # Update the job's UI when processing finishes successfully.
    def job_finished(self, filepath):
        self.set_job_status(filepath, "Complete")

        widget = self.jobs.get(filepath)

        if widget:
            widget.show_transfer_button()

    # Update the job's UI when processing fails.
    def job_failed(self, filepath, message):
        self.set_job_status(filepath, "Failed")

        print(message)

        QMessageBox.warning(
            self,
            "Processing failed",
            f"{Path(filepath).name}\n\n{message}"
        )

    # Copy the completed track to the selected destination.
    def transfer_track(self, filepath):
        if not self.destination_folder:
            QMessageBox.information(
                self,
                "No destination",
                "Choose a destination folder before transferring."
            )
            return

        source_folder = Path("output") / Path(filepath).stem

        try:
            destination = self.transfer.copy_track(
                source_folder,
                self.destination_folder
            )

        except Exception as e:
            QMessageBox.warning(self, "Transfer failed", str(e))
            return

        print("Transferred to:", destination)

        widget = self.jobs.get(filepath)

        if widget:
            widget.transfer_button.setText("Transferred")
            widget.transfer_button.setEnabled(False)
