"""
loading_window.py

Loading screen displayed while the annotator backend initializes.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QProgressBar,
    QVBoxLayout,
)
from PySide6.QtGui import QFont


class LoadingWindow(QDialog):
    """Simple loading dialog for annotator startup."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Opening Annotator")
        self.setFixedSize(400, 140)

        font = QFont()
        font.setPointSize(10)

        self.setFont(font)

        # Prevent closing while loading
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)

        self.title_label = QLabel("Initializing Annotator")
        self.title_label.setAlignment(Qt.AlignCenter)

        self.status_label = QLabel("Starting...")
        self.status_label.setAlignment(Qt.AlignCenter)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.setTextVisible(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        layout.addWidget(self.title_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)

    def set_status(self, text: str):
        """Update the loading status message."""
        self.status_label.setText(text)