from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel
)

from PySide6.QtCore import Qt

from track_browser import TrackBrowser


class SelectionUI(QWidget):

    def __init__(
        self,
        app,
        load_track
    ):

        super().__init__()

        self.app = app
        self.load_track = load_track

        self.build()

    # =====================================================
    # BUILD
    # =====================================================

    def build(self):

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            4,
            4,
            4,
            4
        )

        layout.setSpacing(
            4
        )

        # -------------------------------------------------
        # USB status
        # -------------------------------------------------

        self.usb_label = QLabel(
            "Checking USB..."
        )

        self.usb_label.setAlignment(
            Qt.AlignCenter
        )

        layout.addWidget(
            self.usb_label
        )

        # -------------------------------------------------
        # Track browser
        # -------------------------------------------------

        self.browser = TrackBrowser(
            None,
            self.load_track
        )

        layout.addWidget(
            self.browser,
            1
        )

        # -------------------------------------------------
        # Back
        # -------------------------------------------------

        back_button = QPushButton(
            "BACK"
        )

        back_button.setFixedHeight(
            42
        )

        back_button.clicked.connect(
            self.app.show_player_page
        )

        layout.addWidget(
            back_button
        )

    # =====================================================
    # USB
    # =====================================================

    def set_music_folder(
        self,
        folder
    ):

        self.browser.set_music_folder(
            folder
        )

    def clear_tracks(self):

        self.browser.clear_tracks()

    def set_usb_status(
        self,
        status
    ):

        self.usb_label.setText(
            status
        )