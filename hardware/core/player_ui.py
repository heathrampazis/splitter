from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QSlider,
    QSizePolicy
)

from PySide6.QtCore import Qt

from waveform_widget import WaveformWidget


class PlayerUI(QWidget):

    def __init__(
        self,
        app
    ):

        super().__init__()

        self.app = app

        self.build()

    # =====================================================
    # BUILD
    # =====================================================

    def build(self):

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            8,
            6,
            8,
            6
        )

        layout.setSpacing(
            4
        )

        # -------------------------------------------------
        # Song
        # -------------------------------------------------

        self.song_label = QLabel(
            "NO SONG"
        )

        self.song_label.setAlignment(
            Qt.AlignCenter
        )

        self.song_label.setWordWrap(
            True
        )

        self.song_label.setMinimumHeight(
            28
        )

        layout.addWidget(
            self.song_label
        )

        # -------------------------------------------------
        # Waveform
        # -------------------------------------------------

        self.waveform = WaveformWidget()

        self.waveform.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        self.waveform.setMinimumHeight(
            150
        )

        layout.addWidget(
            self.waveform,
            1
        )

        # -------------------------------------------------
        # BPM / Time
        # -------------------------------------------------

        info = QHBoxLayout()

        info.setContentsMargins(
            4,
            0,
            4,
            0
        )

        info.setSpacing(
            10
        )

        self.bpm_label = QLabel(
            "BPM ---"
        )

        self.bpm_label.setAlignment(
            Qt.AlignLeft |
            Qt.AlignVCenter
        )

        self.time_label = QLabel(
            "00:00 / -00:00"
        )

        self.time_label.setAlignment(
            Qt.AlignRight |
            Qt.AlignVCenter
        )

        info.addWidget(
            self.bpm_label
        )

        info.addStretch()

        info.addWidget(
            self.time_label
        )

        layout.addLayout(
            info
        )

        # -------------------------------------------------
        # Search / Zoom
        # -------------------------------------------------

        controls = QHBoxLayout()

        controls.setSpacing(
            5
        )

        rewind_button = QPushButton(
            "REWIND"
        )

        rewind_button.setFixedHeight(
            38
        )

        rewind_button.pressed.connect(
            lambda:
            self.app.engine.start_search(-1)
        )

        rewind_button.released.connect(
            self.app.engine.stop_search
        )

        forward_button = QPushButton(
            "FAST FORWARD"
        )

        forward_button.setFixedHeight(
            38
        )

        forward_button.pressed.connect(
            lambda:
            self.app.engine.start_search(1)
        )

        forward_button.released.connect(
            self.app.engine.stop_search
        )

        zoom_button = QPushButton(
            "ZOOM"
        )

        zoom_button.setFixedHeight(
            38
        )

        zoom_button.clicked.connect(
            self.toggle_zoom
        )

        controls.addWidget(
            rewind_button
        )

        controls.addWidget(
            forward_button
        )

        controls.addWidget(
            zoom_button
        )

        layout.addLayout(
            controls
        )

        # -------------------------------------------------
        # Tempo
        # -------------------------------------------------

        self.tempo_slider = QSlider(
            Qt.Horizontal
        )

        self.tempo_slider.setRange(
            -80,
            80
        )

        self.tempo_slider.setValue(
            0
        )

        self.tempo_slider.valueChanged.connect(
            self.app.change_tempo
        )

        layout.addWidget(
            self.tempo_slider
        )

        self.tempo_label = QLabel(
            "Tempo: 0.0%"
        )

        self.tempo_label.setAlignment(
            Qt.AlignCenter
        )

        layout.addWidget(
            self.tempo_label
        )

        # -------------------------------------------------
        # Songs
        # -------------------------------------------------

        songs_button = QPushButton(
            "SONGS"
        )

        songs_button.setFixedHeight(
            42
        )

        songs_button.clicked.connect(
            self.app.show_selection_page
        )

        layout.addWidget(
            songs_button
        )

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

    def set_song_name(
        self,
        name
    ):

        self.song_label.setText(
            name
        )

    def set_bpm(
        self,
        bpm
    ):

        self.bpm_label.setText(
            f"BPM {float(bpm):.1f}"
        )

    def set_time(
        self,
        current,
        remaining
    ):

        self.time_label.setText(
            f"{self.format_time(current)} / "
            f"-{self.format_time(remaining)}"
        )

    def set_progress(
        self,
        progress
    ):

        self.waveform.set_progress(
            progress
        )

    def set_tempo_label(
        self,
        tempo
    ):

        self.tempo_label.setText(
            f"Tempo: {tempo:+.1f}%"
        )

    def reset_tempo(self):

        self.tempo_slider.blockSignals(
            True
        )

        self.tempo_slider.setValue(
            0
        )

        self.tempo_slider.blockSignals(
            False
        )

        self.app.engine.set_tempo(
            0
        )

        self.tempo_label.setText(
            "Tempo: 0.0%"
        )

    def load_waveforms(
        self,
        folder
    ):

        self.waveform.load_waveforms(
            folder
        )

    # =====================================================
    # TIME
    # =====================================================

    @staticmethod
    def format_time(
        seconds
    ):

        minutes = int(
            seconds // 60
        )

        seconds = int(
            seconds % 60
        )

        return (
            f"{minutes:02}:{seconds:02}"
        )