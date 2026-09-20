from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPixmap, QPen
from PySide6.QtCore import Qt, QTimer


class WaveformWidget(QWidget):

    def __init__(self):
        super().__init__()

        self.waveforms = {
            "overview": None,
            "medium": None,
            "detail": None
        }

        self.current_zoom = "overview"
        self.progress = 0.0
        self.target_progress = 0.0

        self.setMinimumHeight(120)
        self.setMaximumHeight(150)

        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate)
        self.animation_timer.start(16)

    def load_waveforms(self, folder):
        self.waveforms["overview"] = QPixmap(f"{folder}/waveform_overview.png")
        self.waveforms["medium"] = QPixmap(f"{folder}/waveform_medium.png")
        self.waveforms["detail"] = QPixmap(f"{folder}/waveform_detail.png")
        self.update()

    def zoom_in(self):
        if self.current_zoom == "overview":
            self.current_zoom = "medium"
        elif self.current_zoom == "medium":
            self.current_zoom = "detail"
        self.update()

    def zoom_out(self):
        if self.current_zoom == "detail":
            self.current_zoom = "medium"
        elif self.current_zoom == "medium":
            self.current_zoom = "overview"
        self.update()

    def zoom_level(self):
        return self.current_zoom

    def set_progress(self, value):
        self.target_progress = max(0.0, min(value, 1.0))

    def animate(self):
        difference = self.target_progress - self.progress
        self.progress += difference * 0.15
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.black)

        waveform = self.waveforms.get(self.current_zoom)

        if waveform is None:
            return

        image_width = waveform.width()
        image_height = waveform.height()
        screen_width = self.width()
        scaled_height = self.height()

        scaled_width = int(image_width * (scaled_height / image_height))

        scaled_waveform = waveform.scaled(
            scaled_width,
            scaled_height,
            Qt.IgnoreAspectRatio,
            Qt.SmoothTransformation
        )

        play_position = int(self.progress * scaled_width)
        offset = screen_width // 2 - play_position

        painter.drawPixmap(offset, 0, scaled_waveform)

        painter.setPen(QPen(Qt.red, 3))
        painter.drawLine(
            screen_width // 2,
            0,
            screen_width // 2,
            self.height()
        )