from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QMainWindow, QWidget, QLabel, QVBoxLayout, QFrame, QScrollArea, QPushButton, QFileDialog)
from core.queue_manager import QueueManager
from core.transfer import TransferManager
from gui.job_widget import JobWidget


# Handles drag-and-drop of supported audio files.
class DropArea(QFrame):
    def __init__(self, parent):
        super().__init__()
        self.parent_window = parent
        self.setAcceptDrops(True)
        self.setMinimumHeight(200)

        label = QLabel("Drag MP3 / WAV / AIFF Files Here")
        label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout(self)
        layout.addWidget(label)

        self.setStyleSheet("""
            QFrame {
                border:3px dashed gray;
                border-radius:15px;
            }
            QLabel {
                font-size:24px;
            }
        """)

    # Accept drag events when they contain files.
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    # Collect supported audio files and add them to the queue.
    def dropEvent(self, event):
        files = []

        for url in event.mimeData().urls():
            filepath = url.toLocalFile()
            extension = Path(filepath).suffix.lower()

            if extension in [".mp3", ".wav", ".aif", ".aiff"]:
                files.append(filepath)

        self.parent_window.add_files(files)


# Builds and controls the main application window.
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Splitter Studio")
        self.resize(900, 700)

        self.jobs = {}
        self.destination_folder = None
        self.queue = QueueManager()
        self.transfer = TransferManager()

        self.build_ui()
        self.connect_queue()

    # Builds the main application layout.
    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        title = QLabel("Splitter Studio")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.destination_button = QPushButton("Select Destination Folder")
        self.destination_button.clicked.connect(self.select_destination)
        layout.addWidget(self.destination_button)

        self.drop_area = DropArea(self)
        layout.addWidget(self.drop_area)

        queue_label = QLabel("Queue")
        layout.addWidget(queue_label)

        # Scrollable area containing the list of jobs.
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.queue_container = QWidget()
        self.queue_layout = QVBoxLayout(self.queue_container)
        self.queue_layout.addStretch()
        self.scroll.setWidget(self.queue_container)
        layout.addWidget(self.scroll)

    # Connect queue signals to the appropriate UI updates.
    def connect_queue(self):
        self.queue.job_started.connect(self.job_started)
        self.queue.job_finished.connect(self.job_finished)
        self.queue.job_failed.connect(self.job_failed)

    # Opens a folder picker for the export destination.
    def select_destination(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")

        if folder:
            self.destination_folder = folder
            print("Destination:", folder)

    # Creates a UI widget for each file and adds it to the queue.
    def add_files(self, files):
        for filepath in files:
            widget = JobWidget(filepath)
            self.jobs[filepath] = widget

            self.queue_layout.insertWidget(self.queue_layout.count()-1, widget)

            widget.transfer_button.clicked.connect(
                lambda checked=False, f=filepath: self.transfer_track(f)
            )

            self.queue.add_job(filepath)

    # Update the job's UI when processing starts.
    def job_started(self, filepath):
        widget = self.jobs.get(filepath)

        if widget:
            widget.set_status("In Progress")

    # Update the job's UI when processing finishes successfully.
    def job_finished(self, filepath):
        widget = self.jobs.get(filepath)

        if widget:
            widget.set_status("Complete")
            widget.show_transfer_button()

    # Update the job's UI when processing fails.
    def job_failed(self, filepath, message):
        widget = self.jobs.get(filepath)

        if widget:
            widget.set_status("Failed")

        print(message)

    # Copy the completed track to the selected destination.
    def transfer_track(self, filepath):
        if not self.destination_folder:
            print("No destination selected")
            return

        source_folder = Path("output") / Path(filepath).stem
        destination = self.transfer.copy_track(source_folder, self.destination_folder)
        print("Transferred to:", destination)