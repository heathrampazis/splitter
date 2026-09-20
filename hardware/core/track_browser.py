import os

from PySide6.QtWidgets import (
    QWidget,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QLabel
)

from PySide6.QtCore import Qt


class TrackBrowser(QWidget):

    def __init__(
        self,
        music_folder,
        callback
    ):
        super().__init__()

        self.music_folder = music_folder
        self.callback = callback

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            4,
            4,
            4,
            4
        )

        layout.setSpacing(4)

        label = QLabel(
            "TRACKS"
        )

        label.setAlignment(
            Qt.AlignCenter
        )

        layout.addWidget(
            label
        )

        self.list = QListWidget()

        self.list.setMinimumHeight(
            200
        )

        self.list.itemClicked.connect(
            self.track_selected
        )

        layout.addWidget(
            self.list
        )

        self.refresh()

    def refresh(self):

        folders = []

        if (
            self.music_folder
            and os.path.exists(
                self.music_folder
            )
        ):

            try:

                for folder in os.listdir(
                    self.music_folder
                ):

                    path = os.path.join(
                        self.music_folder,
                        folder
                    )

                    if os.path.isdir(path):

                        folders.append(
                            folder
                        )

            except OSError:
                pass

        folders.sort(
            key=str.lower
        )

        current = [

            self.list.item(
                index
            ).text()

            for index in range(
                self.list.count()
            )

        ]

        if current == folders:
            return

        self.list.clear()

        for folder in folders:

            self.list.addItem(
                QListWidgetItem(folder)
            )

    def set_music_folder(
        self,
        folder
    ):

        self.music_folder = folder

        self.refresh()

    def clear_tracks(self):

        self.music_folder = None

        self.list.clear()

    def track_selected(
        self,
        item
    ):

        if not self.music_folder:
            return

        folder = os.path.join(
            self.music_folder,
            item.text()
        )

        if not os.path.isdir(folder):
            return

        self.callback(
            folder
        )