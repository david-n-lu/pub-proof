"""
downloader_window.py

PySide6 UI for Europe PMC downloader
"""

import os
import sys

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QFileDialog,
    QSpinBox,
    QMessageBox,
)

from PySide6.QtCore import QThread, Signal, QObject

from corpus.downloader import (
    get_total_hits,
    fetch_articles_stream,
    delete_checkpoint,
    erase_output_file,
)


# -----------------------------
# Worker
# -----------------------------

class DownloaderWorker(QObject):

    finished = Signal(dict)
    message = Signal(str)
    error = Signal(str)

    def __init__(
        self,
        manufacturer,
        output_path,
        checkpoint_path,
        page_size,
        max_pages,
    ):
        super().__init__()

        self.manufacturer = manufacturer
        self.output_path = output_path
        self.checkpoint_path = checkpoint_path
        self.page_size = page_size
        self.max_pages = max_pages

    def run(self):

        try:

            self.message.emit(
                f"Searching Europe PMC for: {self.manufacturer}"
            )

            total_hits = get_total_hits(
                self.manufacturer
            )

            self.message.emit(
                f"Found {total_hits:,} articles"
            )

            self.message.emit(
                "Starting download..."
            )

            stats = fetch_articles_stream(
                self.manufacturer,
                self.output_path,
                self.checkpoint_path,
                page_size=self.page_size,
                max_pages=self.max_pages,
            )

            self.message.emit(
                f"Downloaded {stats['saved']:,} articles "
                f"({stats['skipped']:,} skipped)"
            )

            self.finished.emit(
                stats
            )

        except Exception as e:

            self.error.emit(
                str(e)
            )


# -----------------------------
# Window
# -----------------------------

class DownloaderWindow(QWidget):

    closed = Signal()

    def __init__(
        self,
        publications_path,
    ):

        super().__init__()

        self.publications_path = publications_path    

        self.thread = None
        self.worker = None

        self.setWindowTitle(
            "Europe PMC Downloader"
        )

        self.resize(
            700,
            500
        )

        self.setup_ui()

    def setup_ui(self):

        layout = QVBoxLayout()

        # Manufacturer

        row = QHBoxLayout()

        row.addWidget(
            QLabel("Manufacturer:")
        )

        self.manufacturer = QLineEdit(
            "GeneCopoeia"
        )

        row.addWidget(
            self.manufacturer
        )

        layout.addLayout(row)

        # Output path

        row = QHBoxLayout()

        self.output = QLineEdit(
            self.publications_path
        )
        
        self.output.textChanged.connect(
            self.update_buttons
        )

        browse = QPushButton(
            "Browse"
        )

        browse.clicked.connect(
            self.select_output
        )

        row.addWidget(
            self.output
        )

        row.addWidget(
            browse
        )

        layout.addLayout(row)

        # Checkpoint path

        row = QHBoxLayout()

        self.checkpoint = QLineEdit(
            self.publications_path.replace(".jsonl", "") + ".checkpoint.json"
        )

        self.checkpoint.textChanged.connect(
            self.update_buttons
        )

        row.addWidget(
            QLabel("Checkpoint:")
        )

        row.addWidget(
            self.checkpoint
        )

        layout.addLayout(row)

        # Parameters

        row = QHBoxLayout()

        row.addWidget(
            QLabel("Page size:")
        )

        self.page_size = QSpinBox()

        self.page_size.setRange(
            1,
            1000
        )

        self.page_size.setValue(
            100
        )

        row.addWidget(
            self.page_size
        )

        row.addWidget(
            QLabel("Max pages:")
        )

        self.max_pages = QSpinBox()

        self.max_pages.setRange(
            1,
            10000
        )

        self.max_pages.setValue(
            1000
        )

        row.addWidget(
            self.max_pages
        )

        layout.addLayout(row)

        # Buttons

        row = QHBoxLayout()

        self.start_button = QPushButton()

        self.start_button.clicked.connect(
            self.start_download
        )

        self.restart_button = QPushButton(
            "Restart Download"
        )

        self.restart_button.clicked.connect(
            self.restart_download
        )

        row.addWidget(
            self.start_button
        )

        row.addWidget(
            self.restart_button
        )

        layout.addLayout(row)

        # Log

        self.log = QTextEdit()

        self.log.setReadOnly(
            True
        )

        layout.addWidget(
            self.log
        )

        self.setLayout(
            layout
        )

        self.update_buttons()

    def update_buttons(self):

        can_continue = (
            os.path.exists(self.checkpoint.text())
            and os.path.exists(self.output.text())
        )

        if can_continue:

            self.start_button.setText(
                "Continue Download"
            )

            self.restart_button.show()

        else:

            self.start_button.setText(
                "Start Download"
            )

            self.restart_button.hide()

    def restart_download(self):

        reply = QMessageBox.question(
            self,
            "Restart Download",
            (
                "This will delete the current output file "
                "and checkpoint.\n\n"
                "Are you sure you want to continue?"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        erase_output_file(
            self.output.text()
        )

        delete_checkpoint(
            self.checkpoint.text()
        )

        self.update_buttons()

        self.start_download()

    def select_output(self):

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save JSONL",
            "",
            "JSONL (*.jsonl)"
        )

        if path:

            self.output.setText(
                path
            )

        self.update_buttons()

    def start_download(self):

        self.start_button.setEnabled(False)
        self.restart_button.setEnabled(False)

        self.log.clear()

        self.thread = QThread()

        self.worker = DownloaderWorker(
            self.manufacturer.text(),
            self.output.text(),
            self.checkpoint.text(),
            self.page_size.value(),
            self.max_pages.value(),
        )

        self.worker.moveToThread(
            self.thread
        )

        self.thread.started.connect(
            self.worker.run
        )

        self.worker.message.connect(
            self.log.append
        )

        self.worker.error.connect(
            self.log.append
        )

        self.worker.finished.connect(
            self.download_finished
        )

        self.thread.start()

    def download_finished(self, stats):

        self.log.append("")

        self.log.append(
            f"Searched: {stats['searched']:,}"
        )

        self.log.append(
            f"Saved: {stats['saved']:,}"
        )

        self.log.append(
            f"Skipped: {stats['skipped']:,}"
        )

        self.start_button.setEnabled(True)
        self.restart_button.setEnabled(True)

        self.update_buttons()

        self.thread.quit()
        self.thread.wait()


    def closeEvent(self, event):
    
        self.closed.emit()

        event.accept()

    


# -----------------------------
# standalone runner
# -----------------------------

if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = DownloaderWindow(
        "data/europe_pmc/genecopoeia_articles.json"
    )

    window.show()

    sys.exit(
        app.exec()
    )