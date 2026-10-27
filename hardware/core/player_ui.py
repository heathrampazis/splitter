"""
The playback screen.

Laid out for the 5" Touch Display 2 turned to landscape (1280 x 720),
and it scales down for a smaller window while developing.

It only shows what you need to see. Play/pause and the three stem
buttons can be tapped on the screen as well as pressed on the hardware;
both do exactly the same thing. Tempo and jog are only on the knobs.
The waveform can be dragged to move through the track, ZOOM changes how
much of it shows, and SONGS picks a track.

    +--------------------------------------------------------------+
    | Track name                           BPM 123.0  +0.0%  01:23 |
    +--------------------------------------------------------------+
    |                                               [ZOOM · 8 s]   |
    |                     waveform  (drag me)                      |
    |                                                              |
    +--------------------------------------------------------------+
    | [▶ PLAYING]   [VOCALS] [DRUMS] [INSTRUMENTAL]       [SONGS]  |
    +--------------------------------------------------------------+
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton,
                               QSizePolicy, QVBoxLayout, QWidget)

import styles
from waveform_widget import WaveformWidget

# The three stem groups the buttons switch, in screen order.
STEM_GROUPS = (
    ("vocals", "VOCALS"),
    ("drums", "DRUMS"),
    ("instrumental", "INSTRUMENTAL"),
)


# Tallest the waveform gets, in pixels, on the 720-pixel-high screen.
WAVEFORM_MAX_HEIGHT = 300


# A label that shortens long text with "…" instead of pushing the layout.
class ElidingLabel(QLabel):
    def __init__(self, text=""):
        super().__init__()
        self.full_text = text
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.setText(text)

    def setText(self, text):
        self.full_text = text
        self.apply_elide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.apply_elide()

    def apply_elide(self):
        metrics = QFontMetrics(self.font())
        super().setText(metrics.elidedText(self.full_text, Qt.ElideRight,
                                           max(0, self.width())))


def refresh_style(widget):
    # Qt only re-reads property-based styles when told to.
    widget.style().unpolish(widget)
    widget.style().polish(widget)


class PlayerUI(QWidget):

    def __init__(self, app):
        super().__init__()

        self.app = app
        self.playing = None
        self.stem_chips = {}

        self.build()

    # =====================================================
    # BUILD
    # =====================================================

    def build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        layout.addWidget(self.build_info_bar())

        # The spare height goes evenly above and below the waveform.
        layout.addStretch(1)

        self.waveform = WaveformWidget()
        self.waveform.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Kept a little short of the full height, so the touch buttons
        # below get room for a finger.
        self.waveform.setMaximumHeight(WAVEFORM_MAX_HEIGHT)
        layout.addWidget(self.waveform, 3)

        layout.addStretch(1)
        layout.addWidget(self.build_status_bar())

    def build_info_bar(self):
        bar = QFrame()
        bar.setObjectName("infoBar")

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(18, 10, 18, 10)
        layout.setSpacing(28)

        self.song_label = ElidingLabel("NO TRACK")
        self.song_label.setObjectName("songName")

        self.bpm_label = QLabel("---.-")
        self.bpm_label.setObjectName("bpm")
        self.bpm_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        bpm_caption = QLabel("BPM")
        bpm_caption.setObjectName("caption")

        self.tempo_label = QLabel("+0.0%")
        self.tempo_label.setObjectName("tempo")
        self.tempo_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.time_label = QLabel("00:00  -00:00")
        self.time_label.setObjectName("time")
        self.time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addWidget(self.song_label, 1)
        layout.addWidget(self.bpm_label)
        layout.addWidget(bpm_caption)
        layout.addWidget(self.tempo_label)
        layout.addWidget(self.time_label)

        return bar

    def build_status_bar(self):
        bar = QFrame()
        bar.setObjectName("statusBar")

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 8, 8, 8)
        layout.setSpacing(12)

        # Buttons act the moment a finger goes down, like the hardware
        # ones, rather than on release.
        self.play_state = self.touch_button("■  STOPPED", "playState", "play")
        self.play_state.setMinimumWidth(200)

        layout.addWidget(self.play_state)
        layout.addStretch(1)

        for group, caption in STEM_GROUPS:
            chip = self.touch_button(caption, "stemChip", group)
            chip.setProperty("stem", group)
            chip.setProperty("on", "true")

            self.stem_chips[group] = chip
            layout.addWidget(chip)

        layout.addStretch(1)

        songs = QPushButton("SONGS")
        songs.setObjectName("songsButton")
        songs.setFocusPolicy(Qt.NoFocus)
        songs.clicked.connect(self.app.show_selection_page)
        layout.addWidget(songs)

        return bar

    def touch_button(self, text, object_name, control):
        button = QPushButton(text)
        button.setObjectName(object_name)
        button.setFocusPolicy(Qt.NoFocus)
        button.pressed.connect(lambda: self.app.handle_button(control, True))
        button.released.connect(lambda: self.app.handle_button(control, False))
        return button

    # =====================================================
    # DISPLAY
    # =====================================================

    def set_song_name(self, name):
        self.song_label.setText(name)

    def set_bpm(self, bpm):
        bpm = float(bpm or 0)
        self.bpm_label.setText(f"{bpm:.1f}" if bpm > 0 else "---.-")

    def set_tempo(self, percent):
        self.tempo_label.setText(f"{percent:+.1f}%")

    def set_time(self, current, remaining):
        self.time_label.setText(
            f"{self.format_time(current)}  -{self.format_time(remaining)}")

    def set_progress(self, progress):
        self.waveform.set_progress(progress)

    def set_playing(self, playing, loaded=True):
        state = "playing" if playing else ("paused" if loaded else "stopped")

        if state == self.playing:
            return

        self.playing = state

        text = {"playing": "▶  PLAYING", "paused": "❚❚  PAUSED",
                "stopped": "■  STOPPED"}[state]

        self.play_state.setText(text)
        self.play_state.setProperty("state", state)
        refresh_style(self.play_state)

    def set_stem(self, group, on):
        chip = self.stem_chips.get(group)

        if chip is None:
            return

        chip.setProperty("on", "true" if on else "false")
        refresh_style(chip)

    def load_waveforms(self, folder, duration):
        self.waveform.load_waveforms(folder, duration)

    def clear(self):
        self.set_song_name("NO TRACK")
        self.set_bpm(0)
        self.set_tempo(0)
        self.set_time(0, 0)
        self.set_playing(False, loaded=False)
        self.waveform.clear()

        for group, _ in STEM_GROUPS:
            self.set_stem(group, True)

    @staticmethod
    def format_time(seconds):
        seconds = max(0, int(seconds))
        return f"{seconds // 60:02}:{seconds % 60:02}"
