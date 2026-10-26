"""
The main window: ties the audio engine, the screens and the controls
together.

Every physical control - GPIO or MIDI - ends up in one of two methods,
handle_button() and handle_turn(), so there is one place that decides
what each control does:

    play          play / pause
    vocals        vocals on / off
    drums         drums on / off
    instrumental  bass and other on / off together
    tempo_reset   tempo back to 0 % (the tempo encoder's push switch)

    tempo         tempo up or down, faster when turned quickly
    jog           while playing: bend the speed briefly to line up a beat
                  while paused: step through the track to find a cue

The screen's own controls are the waveform (drag to move through the
track), its zoom button, and SONGS.
"""

import json
import os
import time

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMainWindow, QStackedWidget

import controls
from audio_engine import AudioEngine
from player_ui import PlayerUI
from selection_ui import SelectionUI
from usb_manager import USBManager

# Stem groups switched by the buttons, and the stems in each.
GROUP_STEMS = {
    "vocals": ("vocals",),
    "drums": ("drums",),
    "instrumental": ("bass", "other"),
}

# Tempo: % per encoder click, and how far it can go either way. Clicks
# that arrive close together count several times over, so a quick spin
# covers the range and a slow turn is fine-grained.
TEMPO_STEP = 0.1
TEMPO_RANGE = 8.0
TEMPO_FAST_SECONDS = 0.05
TEMPO_FAST_MULTIPLIER = 5

# Jog while playing: each click bends the speed by this much (0.01 is
# 1 %), up to the limit, and the bend fades away once the wheel stops.
JOG_BEND_STEP = 0.01
JOG_BEND_MAX = 0.16
JOG_RELEASE_SECONDS = 0.08
JOG_FADE = 0.7

# Jog while paused: seconds moved per click.
JOG_CUE_SECONDS = 0.025


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("StemDeck")

        # The 5" Touch Display 2 turned to landscape. On the Pi the
        # window is made full screen by main.py.
        self.resize(1280, 720)
        self.setMinimumSize(800, 450)

        self.engine = AudioEngine()

        self.current_folder = None
        self.tempo = 0.0
        self.last_tempo_click = 0.0
        self.jog_bend = 0.0
        self.last_jog_click = 0.0
        self.scrub_was_playing = False
        self.stems_on = {group: True for group in GROUP_STEMS}

        # ---- USB stick ----

        self.usb = USBManager(on_connected=self.usb_connected,
                              on_removed=self.usb_removed)

        # ---- screens ----

        self.player_page = PlayerUI(self)
        self.selection_page = SelectionUI(self, self.load_track)

        self.pages = QStackedWidget()
        self.pages.addWidget(self.player_page)
        self.pages.addWidget(self.selection_page)
        self.pages.setCurrentWidget(self.player_page)
        self.setCentralWidget(self.pages)

        waveform = self.player_page.waveform
        waveform.scrub_started.connect(self.scrub_started)
        waveform.scrub_moved.connect(self.scrub_moved)
        waveform.scrub_ended.connect(self.scrub_ended)

        self.player_page.clear()

        # ---- physical controls ----

        # Attached last, because they call into the screens as soon as
        # anything is pressed.
        self.controls = controls.attach(self)

        # ---- timers ----

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_system)
        self.timer.start(20)

        self.usb_timer = QTimer(self)
        self.usb_timer.timeout.connect(self.check_usb)
        self.usb_timer.start(1000)

        self.check_usb()

    # =====================================================
    # PAGES
    # =====================================================

    def show_player_page(self):
        self.pages.setCurrentWidget(self.player_page)

    def show_selection_page(self):
        self.check_usb()
        self.pages.setCurrentWidget(self.selection_page)

    # =====================================================
    # USB
    # =====================================================

    def check_usb(self):
        self.usb.check()

    def usb_connected(self, music_folder):
        print("USB music folder detected:", music_folder)
        self.selection_page.set_music_folder(music_folder)
        self.selection_page.set_usb_status("USB MUSIC")

    def usb_removed(self):
        print("USB removed")
        self.selection_page.clear_tracks()
        self.selection_page.set_usb_status("NO USB")

        if self.current_folder and not os.path.exists(self.current_folder):
            self.engine.stop()
            self.current_folder = None
            self.player_page.clear()

    # =====================================================
    # TRACK LOADING
    # =====================================================

    def load_track(self, folder):
        print("Loading:", folder)

        if not os.path.isdir(folder):
            print("Track no longer exists")
            return

        try:
            with open(os.path.join(folder, "metadata.json")) as file:
                metadata = json.load(file)
        except Exception as e:
            print("Metadata error:", e)
            return

        self.current_folder = folder
        self.engine.stop()

        song_name = (metadata.get("title") or metadata.get("name")
                     or os.path.basename(folder.rstrip("/")))

        self.player_page.set_song_name(str(song_name))

        self.engine.load_song(folder)
        self.engine.original_bpm = metadata.get("bpm", 0) or 0

        _, _, total = self.engine.get_time_info()
        self.player_page.load_waveforms(folder, total)

        # A new track starts flat: tempo 0 %, no jog, every stem on.
        self.set_tempo(0.0)
        self.jog_bend = 0.0
        self.engine.set_jog(0.0)

        for group in GROUP_STEMS:
            self.set_stem(group, True)

        self.show_player_page()

    # =====================================================
    # CONTROLS
    # =====================================================

    def handle_button(self, name, pressed):
        # Every button acts the moment it goes down.
        if not pressed:
            return

        if name == "play":
            self.engine.toggle_play()

        elif name in GROUP_STEMS:
            self.set_stem(name, not self.stems_on[name])

        elif name == "tempo_reset":
            self.set_tempo(0.0)

            # The next click starts afresh rather than counting as part
            # of a fast spin.
            self.last_tempo_click = 0.0

    def handle_turn(self, name, steps):
        if name == "tempo":
            self.turn_tempo(steps)

        elif name == "jog":
            self.turn_jog(steps)

    # Called when a controller disappears mid-press.
    def release_all(self):
        self.jog_bend = 0.0
        self.engine.set_jog(0.0)

    # ---- stems ----

    def set_stem(self, group, on):
        self.stems_on[group] = on

        for stem in GROUP_STEMS[group]:
            self.engine.set_volume(stem, 1.0 if on else 0.0)

        self.player_page.set_stem(group, on)

    # ---- tempo ----

    def turn_tempo(self, steps):
        now = time.monotonic()
        fast = now - self.last_tempo_click < TEMPO_FAST_SECONDS
        self.last_tempo_click = now

        step = TEMPO_STEP * (TEMPO_FAST_MULTIPLIER if fast else 1)
        self.set_tempo(self.tempo + steps * step)

    def set_tempo(self, percent):
        percent = max(-TEMPO_RANGE, min(TEMPO_RANGE, percent))

        # Keep it on the 0.1 % grid so it reads cleanly and returns to
        # exactly 0.
        self.tempo = round(percent, 1)

        self.engine.set_tempo(self.tempo)
        self.player_page.set_tempo(self.tempo)

    # ---- jog ----

    def turn_jog(self, steps):
        if self.engine.playing:
            self.jog_bend = max(-JOG_BEND_MAX, min(JOG_BEND_MAX,
                                self.jog_bend + steps * JOG_BEND_STEP))
            self.last_jog_click = time.monotonic()
            self.engine.set_jog(self.jog_bend)
        else:
            self.engine.nudge_position(steps * JOG_CUE_SECONDS)

    def fade_jog(self):
        if self.jog_bend == 0.0:
            return

        if time.monotonic() - self.last_jog_click < JOG_RELEASE_SECONDS:
            return

        self.jog_bend *= JOG_FADE

        if abs(self.jog_bend) < 0.001:
            self.jog_bend = 0.0

        self.engine.set_jog(self.jog_bend)

    # ---- dragging the waveform ----

    def scrub_started(self):
        # Hold playback while a finger is on the waveform, then carry on
        # from wherever it lets go.
        self.scrub_was_playing = self.engine.playing
        self.engine.pause()

    def scrub_moved(self, progress):
        _, _, total = self.engine.get_time_info()
        self.engine.set_position(progress * total)

    def scrub_ended(self):
        if self.scrub_was_playing:
            self.engine.play()

    # =====================================================
    # SCREEN UPDATE
    # =====================================================

    def update_system(self):
        self.fade_jog()

        current, remaining, total = self.engine.get_time_info()
        loaded = total > 0

        self.player_page.set_time(current, remaining)
        self.player_page.set_playing(self.engine.playing, loaded=loaded)

        if loaded:
            self.player_page.set_bpm(self.engine.get_current_bpm())
            self.player_page.set_progress(current / total)

    # =====================================================
    # CLEANUP
    # =====================================================

    def closeEvent(self, event):
        if self.controls:
            self.controls.close()

        self.engine.close()
        event.accept()
