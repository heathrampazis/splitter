import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (QApplication, QFrame, QGraphicsScene,
                               QGraphicsView)

from app_window import MainWindow
from styles import APP_STYLE


# True on a Raspberry Pi, where the player should fill the screen.
def on_raspberry_pi():
    try:
        with open("/proc/device-tree/model") as file:
            return "raspberry pi" in file.read().lower()
    except OSError:
        return False


# Draws the player turned on its side, for when the screen itself could
# not be rotated (run.sh normally does that with wlr-randr). Touches are
# turned back the same way, so the waveform and buttons still line up
# with your finger.
class RotatedHost(QGraphicsView):
    def __init__(self, window, degrees, screen_size):
        super().__init__()

        self.window = window

        scene = QGraphicsScene(self)
        self.setScene(scene)

        # The player is laid out landscape: the screen's long side wide.
        window.setFixedSize(screen_size.height(), screen_size.width())

        proxy = scene.addWidget(window)
        proxy.setRotation(degrees)
        scene.setSceneRect(proxy.sceneBoundingRect())

        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setStyleSheet("background: black;")

    def closeEvent(self, event):
        self.window.close()
        super().closeEvent(event)


app = QApplication(sys.argv)
app.setStyleSheet(APP_STYLE)

window = MainWindow()

# STEMDECK_WINDOWED=1 keeps it in a window on the Pi, for debugging.
if on_raspberry_pi() and not os.environ.get("STEMDECK_WINDOWED"):
    size = app.primaryScreen().size()

    if size.height() > size.width():
        # Still portrait: turn the player instead of the screen. Wayland
        # counts rotation anticlockwise and Qt clockwise, so this matches
        # what STEMDECK_ROTATION does in run.sh.
        degrees = 90 if os.environ.get("STEMDECK_ROTATION") == "270" else 270
        print(f"Screen is portrait ({size.width()} x {size.height()}) - "
              f"turning the player {degrees} degrees.")
        shown = RotatedHost(window, degrees, size)
    else:
        shown = window

    shown.showFullScreen()

    # A touchscreen has no use for a mouse pointer sitting in the middle.
    app.setOverrideCursor(Qt.BlankCursor)
else:
    window.show()

sys.exit(app.exec())
