"""
citation_window.py

PySide6 frontend for export_sku_results.py
"""

from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from citation_generator.export_annotator_results import run_pipeline


PROJECT_ROOT = Path.cwd()

# -------------------------------------------------------
# Worker
# -------------------------------------------------------

class CitationWorker(QObject):

    finished = Signal()
    message = Signal(str)
    error = Signal(str)

    def __init__(
        self,
        manufacturer,
        annotations_path,
        auto_results_path,
        output_csv_path,
    ):
        super().__init__()

        self.manufacturer = manufacturer
        self.annotations_path = annotations_path
        self.auto_results_path = auto_results_path
        self.output_csv_path = output_csv_path

    @Slot()
    def run(self):

        try:

            run_pipeline(
                manufacturer=self.manufacturer,
                annotations_path=self.annotations_path,
                auto_results_path=self.auto_results_path,
                output_csv_path=self.output_csv_path,
                progress_callback=self.message.emit,
            )

            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))


# -------------------------------------------------------
# Main Window
# -------------------------------------------------------

class CitationGeneratorWindow(QWidget):

    closed = Signal()

    def __init__(
            self,
            annotations_path,
            auto_results_path,
            output_csv_path,
        
        ):
        super().__init__()

        self.annotations_path = annotations_path
        self.auto_results_path = auto_results_path
        self.output_csv_path = output_csv_path

        self.setWindowTitle("Citation Generator")
        self.resize(700, 500)

        self.build_ui()
        self.populate_defaults()

    # ---------------------------------------------------
    # UI
    # ---------------------------------------------------

    def build_ui(self):

        self.manufacturer_edit = QLineEdit()

        self.annotations_edit = QLineEdit()
        self.auto_results_edit = QLineEdit()
        self.output_edit = QLineEdit()

        annotations_button = QPushButton("...")
        auto_results_button = QPushButton("...")
        output_button = QPushButton("...")

        self.generate_button = QPushButton(
            "Generate Citations"
        )

        self.status_box = QTextEdit()
        self.status_box.setReadOnly(True)

        annotations_button.clicked.connect(
            lambda: self.browse_open(self.annotations_edit)
        )

        auto_results_button.clicked.connect(
            lambda: self.browse_open(self.auto_results_edit)
        )

        output_button.clicked.connect(
            self.browse_save
        )

        self.generate_button.clicked.connect(
            self.generate
        )

        form = QFormLayout()

        form.addRow(
            "Manufacturer",
            self.manufacturer_edit,
        )

        form.addRow(
            "Annotations",
            self.path_row(
                self.annotations_edit,
                annotations_button,
            ),
        )

        form.addRow(
            "Auto Results",
            self.path_row(
                self.auto_results_edit,
                auto_results_button,
            ),
        )

        form.addRow(
            "Output CSV",
            self.path_row(
                self.output_edit,
                output_button,
            ),
        )

        layout = QVBoxLayout(self)

        layout.addLayout(form)
        layout.addWidget(self.generate_button)
        layout.addWidget(self.status_box)

    def path_row(
        self,
        edit,
        button,
    ):

        layout = QHBoxLayout()

        layout.addWidget(edit)
        layout.addWidget(button)

        return layout

    # ---------------------------------------------------
    # Defaults
    # ---------------------------------------------------

    def populate_defaults(self):

        # root = Path.cwd()

        self.manufacturer_edit.setText(
            "GeneCopoeia"
        )

        self.annotations_edit.setText(
            self.annotations_path
        )

        self.auto_results_edit.setText(
            self.auto_results_path
        )

        self.output_edit.setText(
            self.output_csv_path
        )


    def display_path(self, path: str | Path) -> str:
        """
        Return a relative path if the file is inside the project.
        Otherwise return the absolute path.
        """


        path = Path(path).resolve()

        try:
            return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
        except ValueError:
            return str(path).replace("\\", "/")



    # ---------------------------------------------------
    # Browse
    # ---------------------------------------------------

    def browse_open(
        self,
        line_edit,
    ):

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            line_edit.text(),
            "JSON (*.json)",
        )

        if filename:
            line_edit.setText(self.display_path(filename))

    def browse_save(self):

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV",
            self.output_edit.text(),
            "CSV (*.csv)",
        )

        if filename:
            self.output_edit.setText(self.display_path(filename))

    # ---------------------------------------------------
    # Generate
    # ---------------------------------------------------

    def generate(self):

        self.generate_button.setEnabled(False)
        self.status_box.clear()

        self.thread = QThread()

        self.worker = CitationWorker(
            manufacturer=self.manufacturer_edit.text().strip(),
            annotations_path=self.annotations_edit.text(),
            auto_results_path=self.auto_results_edit.text(),
            output_csv_path=self.output_edit.text(),
        )

        self.worker.moveToThread(self.thread)

        self.thread.started.connect(
            self.worker.run
        )

        self.worker.message.connect(
            self.status_box.append
        )

        self.worker.finished.connect(
            self.finished
        )

        self.worker.error.connect(
            self.error
        )

        self.worker.finished.connect(
            self.thread.quit
        )

        self.worker.finished.connect(
            self.worker.deleteLater
        )

        self.thread.finished.connect(
            self.thread.deleteLater
        )

        self.thread.start()

    # ---------------------------------------------------
    # Worker callbacks
    # ---------------------------------------------------

    def finished(self):

        self.status_box.append(
            "Done."
        )

        self.generate_button.setEnabled(True)

    def error(
        self,
        message,
    ):

        QMessageBox.critical(
            self,
            "Error",
            message,
        )

        self.generate_button.setEnabled(True)




    def closeEvent(self, event):
                
        self.closed.emit()

        event.accept()


if __name__ == "__main__":

    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    window = CitationGeneratorWindow(
        annotations_path=(
            "annotator/annotations.json"
        ),
        auto_results_path=(
            "annotator/auto_results.json"
        ),
        output_csv_path=(
            "data/europe_pmc/annotator_citations.csv"
        ),
    )
    window.show()

    sys.exit(app.exec())