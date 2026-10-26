import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app_window import MainWindow
from styles import APP_STYLE


# True on a Raspberry Pi, where the player should fill the screen.
def on_raspberry_pi():
    try:
        with open("/proc/device-tree/model") as file:
            return "raspberry pi" in file.read().lower()
    except OSError:
        return False


app = QApplication(sys.argv)
app.setStyleSheet(APP_STYLE)

window = MainWindow()

# STEMDECK_WINDOWED=1 keeps it in a window on the Pi, for debugging.
if on_raspberry_pi() and not os.environ.get("STEMDECK_WINDOWED"):
    window.showFullScreen()

    # A touchscreen has no use for a mouse pointer sitting in the middle.
    app.setOverrideCursor(Qt.BlankCursor)
else:
    window.show()

sys.exit(app.exec())
