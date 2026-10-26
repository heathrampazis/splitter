from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton,
                               QSizePolicy, QSlider, QVBoxLayout, QWidget)

import styles
from waveform_widget import WaveformWidget


# One stem's volume, as a vertical fader.
#
# These did not exist before: stem levels were only reachable from the
# physical encoders, which made them unusable on a bare touchscreen.
class StemFader(QWidget):
    changed = Signal(str, float)

    def __init__(self, stem, caption, colour):
        super().__init__()

        self.stem = stem
        self.colour = colour

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 8)
        layout.setSpacing(6)

        self.caption = QLabel(caption)
        self.caption.setObjectName("stemLabel")
        self.caption.setAlignment(Qt.AlignCenter)

        self.slider = QSlider(Qt.Vertical)
        self.slider.setRange(0, 100)
        self.slider.setValue(100)
        self.slider.valueChanged.connect(self.slider_moved)
        self.slider.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        # Each stem gets its own handle colour so the mixer can be read
        # without pausing to study the labels.
        self.slider.setStyleSheet(
            "QSlider::handle:vertical {"
            f"  background: {colour};"
            f"  border: 1px solid {colour};"
            "}"
            "QSlider::sub-page:vertical {"
            "  background: #262c33;"
            "}"
        )

        self.value = QLabel("100")
        self.value.setObjectName("stemValue")
        self.value.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.caption)
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.value)

    def slider_moved(self, position):
        self.value.setText(str(position))
        self.changed.emit(self.stem, position / 100.0)

    # Moves the fader without reporting it back, so an encoder turn does
    # not echo round and fight the hardware for control.
    def set_value(self, fraction):
        position = int(max(0.0, min(1.0, fraction)) * 100)

        self.slider.blockSignals(True)
        self.slider.setValue(position)
        self.slider.blockSignals(False)

        self.value.setText(str(position))


class PlayerUI(QWidget):

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.faders = {}
        self.playing = False
        self.build()

    # =====================================================
    # BUILD
    # =====================================================

    def build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 10)
        layout.setSpacing(8)

        layout.addWidget(self.build_top_bar())
        layout.addWidget(self.build_waveform(), 1)
        layout.addWidget(self.build_mixer())
        layout.addLayout(self.build_transport())

    # -----------------------------------------------------
    # Track name, BPM and time
    # -----------------------------------------------------

    def build_top_bar(self):
        bar = QFrame()
        bar.setObjectName("topBar")
        bar.setFixedHeight(54)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(6, 0, 6, 0)
        layout.setSpacing(16)

        self.song_label = QLabel("NO SONG")
        self.song_label.setObjectName("songName")

        self.bpm_label = QLabel("BPM ---")
        self.bpm_label.setObjectName("bpm")

        self.time_label = QLabel("00:00 / -00:00")
        self.time_label.setObjectName("time")

        layout.addWidget(self.song_label, 1)
        layout.addWidget(self.bpm_label)
        layout.addWidget(self.time_label)

        return bar

    def build_waveform(self):
        self.waveform = WaveformWidget()
        self.waveform.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.waveform.setMinimumHeight(100)

        return self.waveform

    # -----------------------------------------------------
    # Stem faders and tempo
    # -----------------------------------------------------

    def build_mixer(self):
        mixer = QFrame()
        mixer.setObjectName("mixer")
        mixer.setMinimumHeight(168)

        layout = QHBoxLayout(mixer)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(4)

        stems = [
            ("vocals", "VOCALS"),
            ("drums", "DRUMS"),
            ("bass", "BASS"),
            ("other", "OTHER"),
        ]

        for stem, caption in stems:
            fader = StemFader(stem, caption, styles.STEM_COLOURS[stem])
            fader.changed.connect(self.stem_changed)

            self.faders[stem] = fader
            layout.addWidget(fader, 1)

        divider = QFrame()
        divider.setFrameShape(QFrame.VLine)
        divider.setStyleSheet(f"color:{styles.LINE};")
        layout.addWidget(divider)

        layout.addWidget(self.build_tempo(), 1)

        return mixer

    def build_tempo(self):
        column = QWidget()

        layout = QVBoxLayout(column)
        layout.setContentsMargins(4, 8, 4, 8)
        layout.setSpacing(6)

        caption = QLabel("TEMPO")
        caption.setObjectName("stemLabel")
        caption.setAlignment(Qt.AlignCenter)

        self.tempo_slider = QSlider(Qt.Vertical)
        self.tempo_slider.setRange(-80, 80)
        self.tempo_slider.setValue(0)

        # Plus at the bottom, minus at the top. That is how every CDJ and
        # turntable is laid out, and the screen should not disagree with
        # a physical fader wired in later.
        self.tempo_slider.setInvertedAppearance(True)
        self.tempo_slider.valueChanged.connect(self.app.change_tempo)
        self.tempo_slider.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        self.tempo_label = QLabel("0.0%")
        self.tempo_label.setObjectName("tempoValue")
        self.tempo_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(caption)
        layout.addWidget(self.tempo_slider, 1)
        layout.addWidget(self.tempo_label)

        return column

    # -----------------------------------------------------
    # Transport
    # -----------------------------------------------------

    def build_transport(self):
        layout = QHBoxLayout()
        layout.setSpacing(8)

        rewind = QPushButton("◀◀")
        rewind.pressed.connect(lambda: self.app.engine.start_search(-1))
        rewind.released.connect(self.app.engine.stop_search)

        # Playback used to be reachable only from a physical button.
        self.play_button = QPushButton("▶  PLAY")
        self.play_button.setObjectName("playButton")
        self.play_button.clicked.connect(self.app.engine.toggle_play)

        forward = QPushButton("▶▶")
        forward.pressed.connect(lambda: self.app.engine.start_search(1))
        forward.released.connect(self.app.engine.stop_search)

        zoom = QPushButton("ZOOM")
        zoom.clicked.connect(self.toggle_zoom)

        songs = QPushButton("SONGS")
        songs.clicked.connect(self.app.show_selection_page)

        layout.addWidget(rewind, 2)
        layout.addWidget(self.play_button, 3)
        layout.addWidget(forward, 2)
        layout.addWidget(zoom, 2)
        layout.addWidget(songs, 2)

        return layout

    # =====================================================
    # CONTROL HANDLERS
    # =====================================================

    def stem_changed(self, stem, value):
        self.app.engine.set_volume(stem, value)

    # Called by the encoders so the on-screen fader follows the knob.
    def set_stem_value(self, stem, value):
        fader = self.faders.get(stem)

        if fader:
            fader.set_value(value)

    # Keeps the play button honest whichever control started playback.
    def set_playing(self, playing):
        if playing == self.playing:
            return

        self.playing = playing

        self.play_button.setText("❚❚  PAUSE" if playing else "▶  PLAY")
        self.play_button.setProperty("playing", "true" if playing else "false")
        self.play_button.style().unpolish(self.play_button)
        self.play_button.style().polish(self.play_button)

    # =====================================================
    # ZOOM
    # =====================================================

    def toggle_zoom(self):
        current = self.waveform.zoom_level()

        if current == "overview":
            self.waveform.zoom_in()
        elif current == "medium":
            self.waveform.zoom_in()
        else:
            self.waveform.zoom_out()
            self.waveform.zoom_out()

        self.app.update_search_sensitivity()

    # =====================================================
    # DISPLAY HELPERS
    # =====================================================

    def set_song_name(self, name):
        self.song_label.setText(name)

    def set_bpm(self, bpm):
        self.bpm_label.setText(f"BPM {float(bpm):.1f}")

    def set_time(self, current, remaining):
        self.time_label.setText(
            f"{self.format_time(current)} / -{self.format_time(remaining)}"
        )

    def set_progress(self, progress):
        self.waveform.set_progress(progress)

    def set_tempo_label(self, tempo):
        self.tempo_label.setText(f"{tempo:+.1f}%")

    def reset_tempo(self):
        self.tempo_slider.blockSignals(True)
        self.tempo_slider.setValue(0)
        self.tempo_slider.blockSignals(False)

        self.app.engine.set_tempo(0)
        self.tempo_label.setText("0.0%")

    # Returns every fader to full, which is the state a new track starts in.
    #
    # The engine is reset too. The faders are moved with their signals
    # blocked, so without this the screen would show 100 while the engine
    # kept the last track's levels, and the next encoder turn would jump.
    def reset_stems(self):
        for stem, fader in self.faders.items():
            fader.set_value(1.0)
            self.app.engine.set_volume(stem, 1.0)

    def load_waveforms(self, folder):
        self.waveform.load_waveforms(folder)

    # =====================================================
    # TIME
    # =====================================================

    @staticmethod
    def format_time(seconds):
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)

        return f"{minutes:02}:{seconds:02}"
