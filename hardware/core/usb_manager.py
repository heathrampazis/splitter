import os

from PySide6.QtCore import QStorageInfo


class USBManager:

    def __init__(
        self,
        on_connected,
        on_removed
    ):

        self.on_connected = on_connected
        self.on_removed = on_removed

        self.music_folder = None

    # =====================================================
    # FIND USB
    # =====================================================

    def find_music_folder(self):

        for storage in QStorageInfo.mountedVolumes():

            if not storage.isValid():
                continue

            if not storage.isReady():
                continue

            if storage.isRoot():
                continue

            root = storage.rootPath()

            music_folder = os.path.join(
                root,
                "music"
            )

            if os.path.isdir(
                music_folder
            ):

                return music_folder

        return None

    # =====================================================
    # CHECK USB
    # =====================================================

    def check(self):

        music_folder = (
            self.find_music_folder()
        )

        # -------------------------------------------------
        # USB removed
        # -------------------------------------------------

        if music_folder is None:

            if self.music_folder is not None:

                self.music_folder = None

                self.on_removed()

            return

        # -------------------------------------------------
        # New USB
        # -------------------------------------------------

        if music_folder != self.music_folder:

            self.music_folder = music_folder

            self.on_connected(
                music_folder
            )