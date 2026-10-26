"""
The playback screen.

Laid out for the 5" Touch Display 2 turned to landscape (1280 x 720),
and it scales down for a smaller window while developing.

It only shows what you need to see. Everything you do with your hands
is on the physical controls - play/pause, the stem buttons, tempo and
jog - so the screen has no copies of them. The only things to touch
are the waveform (drag to move through the track), its ZOOM button,
and SONGS to pick a track.

    +--------------------------------------------------------------+
    | Track name                           BPM 123.0  +0.0%  01:23 |
    +--------------------------------------------------------------+
    |                                               [ZOOM · ALL]   |
    |                     waveform  (drag me)                      |
    |                                                              |
    +--------------------------------------------------------------+
    | ▶ PLAYING        VOCALS   DRUMS   INSTRUMENTAL      [SONGS]  |
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

        self.waveform = WaveformWidget()
        self.waveform.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.waveform, 1)

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

        self.play_state = QLabel("■  STOPPED")
        self.play_state.setObjectName("playState")
        self.play_state.setMinimumWidth(170)

        layout.addWidget(self.play_state)
        layout.addStretch(1)

        for group, caption in STEM_GROUPS:
            chip = QLabel(caption)
            chip.setObjectName("stemChip")
            chip.setAlignment(Qt.AlignCenter)
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
