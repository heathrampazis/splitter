import sys

from PySide6.QtWidgets import QApplication

from app_window import MainWindow
from styles import APP_STYLE


app = QApplication(sys.argv)

app.setStyleSheet(APP_STYLE)

window = MainWindow()
window.show()

sys.exit(app.exec())