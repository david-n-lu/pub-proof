from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QProgressBar,
)


class ProductIndexProgressDialog(QDialog):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Creating Product Index")
        self.setModal(True)
        self.setFixedWidth(400)

        layout = QVBoxLayout(self)

        layout.addWidget(
            QLabel("Building product index...")
        )

        # self.progress = QProgressBar()

        # # Indeterminate mode
        # self.progress.setRange(0, 0)

        # layout.addWidget(self.progress)

        self.progress = QProgressBar()

        self.progress.setRange(0, 4)

        layout.addWidget(self.progress)

        self.status_label = QLabel(
            "Preparing..."
        )

        layout.addWidget(self.status_label)


    def update_progress(self, text, value):

        self.status_label.setText(text)

        self.progress.setValue(value)