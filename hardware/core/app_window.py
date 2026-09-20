import os
import json

from PySide6.QtWidgets import (
    QMainWindow,
    QStackedWidget
)

from PySide6.QtCore import QTimer

from audio_engine import AudioEngine
from gpio import GPIOController, StemEncoder, TempoEncoder
from player_ui import PlayerUI
from selection_ui import SelectionUI
from usb_manager import USBManager


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("StemDeck")
        self.setFixedSize(480, 320)

        # -------------------------------------------------
        # Audio
        # -------------------------------------------------

        self.engine = AudioEngine()

        # -------------------------------------------------
        # GPIO
        # -------------------------------------------------

        self.gpio = GPIOController(
            self.engine
        )

        self.tempo_encoder = TempoEncoder(
            self
        )

        self.vocal_encoder = StemEncoder(
            self,
            5,
            6,
            "vocals"
        )

        self.drums_encoder = StemEncoder(
            self,
            13,
            19,
            "drums"
        )

        self.base_encoder = StemEncoder(
            self,
            20,
            21,
            "bass_other"
        )

        # -------------------------------------------------
        # State
        # -------------------------------------------------

        self.current_folder = None

        # -------------------------------------------------
        # USB manager
        # -------------------------------------------------

        self.usb = USBManager(
            on_connected=self.usb_connected,
            on_removed=self.usb_removed
        )

        # -------------------------------------------------
        # Pages
        # -------------------------------------------------

        self.player_page = PlayerUI(
            self
        )

        self.selection_page = SelectionUI(
            self,
            self.load_track
        )

        self.pages = QStackedWidget()

        self.pages.addWidget(
            self.player_page
        )

        self.pages.addWidget(
            self.selection_page
        )

        self.pages.setCurrentWidget(
            self.player_page
        )

        self.setCentralWidget(
            self.pages
        )

        # -------------------------------------------------
        # Main update timer
        # -------------------------------------------------

        self.timer = QTimer(self)

        self.timer.timeout.connect(
            self.update_system
        )

        self.timer.start(20)

        # -------------------------------------------------
        # USB update timer
        # -------------------------------------------------

        self.usb_timer = QTimer(self)

        self.usb_timer.timeout.connect(
            self.check_usb
        )

        self.usb_timer.start(1000)

        self.check_usb()

    # =====================================================
    # PAGE CONTROL
    # =====================================================

    def show_player_page(self):

        self.pages.setCurrentWidget(
            self.player_page
        )

    def show_selection_page(self):

        self.check_usb()

        self.pages.setCurrentWidget(
            self.selection_page
        )

    # =====================================================
    # USB
    # =====================================================

    def check_usb(self):

        self.usb.check()

    def usb_connected(self, music_folder):

        print(
            "USB music folder detected:",
            music_folder
        )

        self.selection_page.set_music_folder(
            music_folder
        )

        self.selection_page.set_usb_status(
            "USB MUSIC"
        )

    def usb_removed(self):

        print(
            "USB removed"
        )

        self.selection_page.clear_tracks()

        self.selection_page.set_usb_status(
            "NO USB"
        )

        if (
            self.current_folder
            and not os.path.exists(
                self.current_folder
            )
        ):

            self.engine.stop()

            self.current_folder = None

            self.player_page.set_song_name(
                "NO SONG"
            )

            self.player_page.set_bpm(
                0
            )

    # =====================================================
    # TRACK LOADING
    # =====================================================

    def load_track(self, folder):

        print(
            "Loading:",
            folder
        )

        if not os.path.isdir(folder):

            print(
                "Track no longer exists"
            )

            return

        metadata_file = os.path.join(
            folder,
            "metadata.json"
        )

        try:

            with open(
                metadata_file,
                "r"
            ) as file:

                metadata = json.load(
                    file
                )

        except Exception as e:

            print(
                "Metadata error:",
                e
            )

            return

        self.current_folder = folder

        self.engine.stop()

        song_name = (
            metadata.get("title")
            or metadata.get("name")
            or metadata.get("song")
            or metadata.get("track")
            or os.path.basename(
                folder.rstrip("/")
            )
        )

        self.player_page.set_song_name(
            str(song_name)
        )

        self.engine.load_song(
            folder
        )

        self.player_page.load_waveforms(
            folder
        )

        bpm = metadata.get(
            "bpm",
            0
        )

        self.engine.original_bpm = bpm

        self.player_page.set_bpm(
            bpm
        )

        self.player_page.reset_tempo()

        self.show_player_page()

    # =====================================================
    # TEMPO
    # =====================================================

    def change_tempo_encoder(
        self,
        value
    ):

        value = max(
            -80,
            min(
                80,
                int(value)
            )
        )

        self.player_page.tempo_slider.setValue(
            value
        )

    def change_tempo(
        self,
        value
    ):

        tempo = value / 10

        self.engine.set_tempo(
            tempo
        )

        self.player_page.set_tempo_label(
            tempo
        )

    # =====================================================
    # STEM ENCODERS
    # =====================================================

    def update_stem_slider(
        self,
        stem,
        value
    ):

        # The physical encoders control the audio engine.
        # No on-screen stem controls are required.

        pass

    # =====================================================
    # ZOOM
    # =====================================================

    def update_search_sensitivity(self):

        zoom = self.player_page.waveform.zoom_level()

        speeds = {
            "overview": 20000,
            "medium": 5000,
            "detail": 500
        }

        self.engine.set_search_speed(
            speeds.get(
                zoom,
                5000
            )
        )

    # =====================================================
    # SYSTEM UPDATE
    # =====================================================

    def update_system(self):

        current, remaining, total = (
            self.engine.get_time_info()
        )

        self.player_page.set_time(
            current,
            remaining
        )

        self.player_page.set_bpm(
            self.engine.get_current_bpm()
        )

        if total > 0:

            self.player_page.set_progress(
                current / total
            )

    # =====================================================
    # CLEANUP
    # =====================================================

    def closeEvent(
        self,
        event
    ):

        self.engine.close()

        event.accept()