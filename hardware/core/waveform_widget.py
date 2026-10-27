"""
The waveform: shows where the track is, and drags to move through it.

Three zoom levels, cycled by the ZOOM button in its corner:

    8 s        the waveform scrolls past a fixed playhead in the middle
               as the track plays. This is where it starts.
    30 s       the same, further out.
    overview   the whole track fits the width; the playhead moves along
               it. Tap or drag anywhere to jump there.

When zoomed in, dragging works like the jog wheel on a CDJ: the track
plays at whatever speed and direction your finger moves - drag left to
go forward, right to go back - and a quick flick keeps it spinning fast
for a moment after you let go, then it settles back to normal.

The images come from Splitter Studio (waveform_overview.png, _medium
and _detail). Only the visible slice is drawn each frame, rather than
scaling a 25,000-pixel-wide image every time.
"""

import time

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QPushButton, QWidget

import styles

# (name, image, seconds visible or None for the whole track, button label)
ZOOMS = (
    ("detail", "detail", 8.0, "ZOOM · 8 s"),
    ("medium", "medium", 30.0, "ZOOM · 30 s"),
    ("overview", "overview", None, "ZOOM · ALL"),
)

# A press that moves less than this is a tap, not a drag.
DRAG_THRESHOLD = 8

# The flick speed is measured over the last part of a drag, this long.
FLING_WINDOW = 0.08


class WaveformWidget(QWidget):
    # Dragging when zoomed in.
    scrub_started = Signal()
    scrub_moved = Signal(float)     # where the finger has the track, 0.0 to 1.0
    scrub_ended = Signal(float)     # flick speed, x normal; minus is backwards

    # A tap or drag on the overview: jump straight there, 0.0 to 1.0.
    seek = Signal(float)

    def __init__(self):
        super().__init__()

        self.images = {}
        self.duration = 0.0
        self.progress = 0.0
        self.zoom_index = 0

        self.press_x = None
        self.press_progress = 0.0
        self.dragging = False
        self.recent = []    # (time, progress) for the last moments of a drag

        self.setMinimumHeight(120)
        self.setAttribute(Qt.WA_OpaquePaintEvent)

        self.zoom_button = QPushButton(ZOOMS[0][3], self)
        self.zoom_button.setObjectName("zoomButton")
        self.zoom_button.setFocusPolicy(Qt.NoFocus)
        self.zoom_button.clicked.connect(self.cycle_zoom)

    # =====================================================
    # DATA
    # =====================================================

    def load_waveforms(self, folder, duration):
        self.images = {}

        for name in ("overview", "medium", "detail"):
            pixmap = QPixmap(f"{folder}/waveform_{name}.png")

            if not pixmap.isNull():
                self.images[name] = pixmap

        self.duration = max(0.0, float(duration))
        self.progress = 0.0
        self.update()

    def clear(self):
        self.images = {}
        self.duration = 0.0
        self.progress = 0.0
        self.update()

    def set_progress(self, value):
        # While a finger is on the waveform, it decides the position.
        if self.dragging:
            return

        value = max(0.0, min(float(value), 1.0))

        if abs(value - self.progress) > 1e-6:
            self.progress = value
            self.update()

    # =====================================================
    # ZOOM
    # =====================================================

    def cycle_zoom(self):
        self.zoom_index = (self.zoom_index + 1) % len(ZOOMS)
        self.zoom_button.setText(ZOOMS[self.zoom_index][3])
        self.update()

    def zoom_level(self):
        return ZOOMS[self.zoom_index][0]

    def visible_fraction(self):
        seconds = ZOOMS[self.zoom_index][2]

        if seconds is None or self.duration <= 0:
            return 1.0

        return min(1.0, seconds / self.duration)

    def is_overview(self):
        return ZOOMS[self.zoom_index][2] is None

    def resizeEvent(self, event):
        super().resizeEvent(event)

        w, h = 180, 56
        self.zoom_button.setGeometry(self.width() - w - 12, 12, w, h)

    # =====================================================
    # TOUCH
    # =====================================================

    def position_at(self, x):
        width = max(1, self.width())

        if self.is_overview():
            # The waveform stands still: the finger is the position.
            return x / width

        # The waveform moves with the finger, so a drag of one screen
        # width moves by one screen's worth of track.
        dx = x - self.press_x
        return self.press_progress - dx * self.visible_fraction() / width

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton or self.duration <= 0:
            return

        self.press_x = event.position().x()
        self.press_progress = self.progress
        self.dragging = False
        self.recent = []

    def mouseMoveEvent(self, event):
        if self.press_x is None:
            return

        x = event.position().x()

        if not self.dragging:
            if abs(x - self.press_x) < DRAG_THRESHOLD:
                return

            self.dragging = True

            if not self.is_overview():
                self.scrub_started.emit()

        value = max(0.0, min(self.position_at(x), 1.0))
        self.progress = value
        self.update()

        if self.is_overview():
            self.seek.emit(value)
            return

        now = time.monotonic()
        self.recent.append((now, value))
        self.recent = [(t, p) for t, p in self.recent if now - t <= FLING_WINDOW]

        self.scrub_moved.emit(value)

    def mouseReleaseEvent(self, event):
        if self.press_x is None:
            return

        if self.dragging:
            self.dragging = False

            if not self.is_overview():
                self.scrub_ended.emit(self.fling_speed())

        elif self.is_overview():
            # A tap on the overview jumps straight there.
            value = max(0.0, min(event.position().x() / max(1, self.width()), 1.0))
            self.progress = value
            self.seek.emit(value)
            self.update()

        self.press_x = None

    # How fast the finger was moving the track as it let go, as a
    # multiple of normal speed. A finger that stopped before lifting
    # gives 0, so the track stays where it was put.
    def fling_speed(self):
        now = time.monotonic()
        recent = [(t, p) for t, p in self.recent if now - t <= FLING_WINDOW]

        if len(recent) < 2:
            return 0.0

        (t0, p0), (t1, p1) = recent[0], recent[-1]

        if t1 - t0 <= 0:
            return 0.0

        return (p1 - p0) * self.duration / (t1 - t0)

    # =====================================================
    # DRAWING
    # =====================================================

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        width, height = self.width(), self.height()
        painter.fillRect(self.rect(), QColor(styles.GROUND))

        name, image_name, _, _ = ZOOMS[self.zoom_index]
        image = self.images.get(image_name) or self.images.get("overview")

        if image is None:
            painter.setPen(QColor(styles.TEXT_FAINT))
            painter.drawText(self.rect(), Qt.AlignCenter, "Load a track from SONGS")
            return

        image_w, image_h = image.width(), image.height()

        if self.is_overview():
            painter.drawPixmap(QRectF(0, 0, width, height), image,
                               QRectF(0, 0, image_w, image_h))

            # Dim what has already played.
            playhead = self.progress * width
            painter.fillRect(QRectF(0, 0, playhead, height),
                             QColor(0, 0, 0, 110))
        else:
            # The slice of the image that should fill the widget, centred
            # on the play position.
            slice_w = image_w * self.visible_fraction()
            left = self.progress * image_w - slice_w / 2
            right = left + slice_w

            # Clip to the image; past either end is left empty.
            src_left = max(0.0, left)
            src_right = min(float(image_w), right)

            if src_right > src_left:
                dst_left = (src_left - left) / slice_w * width
                dst_right = (src_right - left) / slice_w * width

                painter.drawPixmap(
                    QRectF(dst_left, 0, dst_right - dst_left, height), image,
                    QRectF(src_left, 0, src_right - src_left, image_h))

            playhead = width / 2

            # Dim the half that has already played.
            painter.fillRect(QRectF(0, 0, playhead, height),
                             QColor(0, 0, 0, 90))

        pen = QPen(QColor(styles.RED), 3)
        painter.setPen(pen)
        painter.drawLine(int(playhead), 0, int(playhead), height)
