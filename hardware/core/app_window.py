import os
import json

from PySide6.QtWidgets import (
    QMainWindow,
    QStackedWidget
)

from PySide6.QtCore import QTimer

from audio_engine import AudioEngine
import controls
from player_ui import PlayerUI
from selection_ui import SelectionUI
from usb_manager import USBManager


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("StemDeck")

        # Sized for a 5" 800x480 panel, but nothing is pinned to that:
        # the layout adapts so the same code runs on a 3.5" screen or in
        # a desktop window while developing.
        self.resize(800, 480)
        self.setMinimumSize(480, 320)

        # -------------------------------------------------
        # Audio
        # -------------------------------------------------

        self.engine = AudioEngine()

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
        # Physical controls (optional)
        # -------------------------------------------------

        # Attached last, because the encoders call back into the pages as
        # soon as they are turned. Returns None when controls are
        # disabled or the MIDI library is missing, which is fine for a
        # touch-only build. The Pico itself can be plugged in any time.
        self.controls = controls.attach(self)

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
        self.player_page.reset_stems()

        self.show_player_page()

    # =====================================================
    # TEMPO
    # =====================================================

    # Moves the tempo by a number of slider units (0.1 % each), starting
    # from wherever the on-screen slider is now. The slider stays the one
    # record of the tempo, so the encoder and the touchscreen can be used
    # in turn without either jumping.
    def nudge_tempo(
        self,
        steps
    ):

        slider = self.player_page.tempo_slider

        value = max(
            slider.minimum(),
            min(
                slider.maximum(),
                slider.value() + int(steps)
            )
        )

        # Setting the slider calls change_tempo, which updates the
        # engine and the label.
        slider.setValue(
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

    # Moves a stem's volume up or down by a fraction of full scale,
    # starting from the engine's current level. Reading the engine, not
    # a value remembered by the knob, means a fader moved on screen is
    # picked up the next time the encoder turns.
    def nudge_stem(
        self,
        stem,
        delta
    ):

        # One encoder drives bass and other together, while the screen
        # gives them a fader each. Each moves by the same amount from
        # wherever it is, so a balance set on screen is kept.
        if stem == "bass_other":
            targets = ["bass", "other"]
        else:
            targets = [stem]

        for target in targets:
            value = max(
                0.0,
                min(
                    1.0,
                    self.engine.get_volume(target) + delta
                )
            )

            self.engine.set_volume(
                target,
                value
            )

            self.player_page.set_stem_value(
                target,
                value
            )

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

        # Playback can be started from the screen or from a button, so
        # the engine is the single source of truth for the label.
        self.player_page.set_playing(
            self.engine.playing
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

        if self.controls:
            self.controls.close()

        self.engine.close()

        event.accept()