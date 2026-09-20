APP_STYLE = """
QWidget {
    background: #101010;
    color: #f0f0f0;
    font-family: sans-serif;
    font-size: 14px;
}

QLabel {
    color: #f0f0f0;
}

QPushButton {
    background: #202020;
    border: 1px solid #555555;
    border-radius: 5px;
    color: #ffffff;
    font-size: 14px;
    font-weight: bold;
    min-height: 38px;
}

QPushButton:pressed {
    background: #404040;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #303030;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    width: 18px;
    margin: -7px 0;
    border-radius: 9px;
    background: #dddddd;
}

QListWidget {
    background: #181818;
    border: 1px solid #444444;
    border-radius: 5px;
    color: #ffffff;
    font-size: 18px;
}

QListWidget::item {
    padding: 12px;
    min-height: 35px;
}

QListWidget::item:selected {
    background: #404040;
}
"""