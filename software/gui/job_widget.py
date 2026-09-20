from PySide6.QtWidgets import (QWidget, QLabel, QHBoxLayout, QPushButton)
from PySide6.QtCore import Qt

# Represents one audio job in the UI.
class JobWidget(QWidget):
    def __init__(self, filepath):
        super().__init__()
        self.filepath = filepath
        self.build_ui()

    # Builds the layout and widgets for the job.
    def build_ui(self):
        layout = QHBoxLayout(self)

        self.filename = QLabel(self.filepath.split("/")[-1])
        self.filename.setAlignment(Qt.AlignLeft)

        self.status = QLabel("Waiting")
        self.status.setAlignment(Qt.AlignRight)

        # Hidden until the job finishes successfully.
        self.transfer_button = QPushButton("Transfer")
        self.transfer_button.hide()

        layout.addWidget(self.filename)
        layout.addWidget(self.status)
        layout.addWidget(self.transfer_button)

        # Basic styling for the job row.
        self.setStyleSheet("""
            QWidget {
                border-bottom:1px solid #333;
                padding:8px;
            }
            QLabel {
                font-size:16px;
            }
        """)

    # Updates the status text and its colour.
    def set_status(self, status):
        self.status.setText(status)

        if status == "Complete":
            self.status.setStyleSheet("color:green;")
        elif status == "In Progress":
            self.status.setStyleSheet("color:orange;")
        elif status == "Failed":
            self.status.setStyleSheet("color:red;")
        else:
            self.status.setStyleSheet("color:gray;")

    # Shows the transfer button after successful processing.
    def show_transfer_button(self):
        self.transfer_button.show()