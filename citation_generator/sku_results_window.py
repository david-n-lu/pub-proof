"""
sku_results_window.py

PySide6 frontend for SKU result extraction.

Runs:
    sentence corpus
        ↓
    SKU matcher backend
        ↓
    product mapping
        ↓
    citation CSV export
"""


from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QFileDialog,
)

from PySide6.QtCore import (
    QThread,
    Signal,
)

from citation_generator.export_sku_results import run_pipeline

from pathlib import Path

PROJECT_ROOT = Path.cwd()


# ============================================================
# Worker Thread
# ============================================================

class SKUResultsWorker(QThread):
    """
    Runs the backend pipeline without freezing the UI.
    """

    progress = Signal(str)
    pipeline_finished = Signal()
    error = Signal(str)


    def __init__(
        self,
        manufacturer = "",
        sentence_path = "",
        product_path = "",
        output_path = "",
    ):
        super().__init__()

        self.manufacturer = manufacturer
        self.sentence_path = sentence_path
        self.product_path = product_path
        self.output_path = output_path



    def run(self):

        try:

            run_pipeline(
                manufacturer=self.manufacturer,
                sentence_corpus_path=self.sentence_path,
                product_index_path=self.product_path,
                output_csv_path=self.output_path,
                progress_callback=self.progress.emit,
            )


            self.pipeline_finished.emit()


        except Exception as e:

            self.error.emit(
                str(e)
            )



# ============================================================
# Main Window
# ============================================================

class SKUResultsWindow(QWidget):

    closed = Signal()


    def __init__(
            self,
            manufacturer="",
            sentence_corpus_path="",
            product_index_path="",
            output_csv_path="",
        ):

        super().__init__()

        self.manufacturer = manufacturer
        self.sentence_corpus_path = sentence_corpus_path
        self.product_index_path = product_index_path
        self.output_csv_path = output_csv_path

        self.worker = None

        self.setWindowTitle(
            "SKU Results Exporter"
        )

        self.resize(
            700,
            500
        )


        self.setup_ui()



    def setup_ui(self):

        layout = QVBoxLayout()



        # -------------------------
        # Manufacturer
        # -------------------------

        layout.addWidget(
            QLabel("Manufacturer")
        )


        self.manufacturer_input = QLineEdit()

        self.manufacturer_input.setText(
            self.manufacturer
        )

        layout.addWidget(
            self.manufacturer_input
        )


        # -------------------------
        # Sentence corpus
        # -------------------------

        layout.addWidget(
            QLabel("Sentence Corpus (.jsonl)")
        )


        sentence_layout = QHBoxLayout()


        self.sentence_input = QLineEdit()

        self.sentence_input.setText(
            self.sentence_corpus_path
        )

        sentence_button = QPushButton(
            "Browse"
        )

        sentence_button.clicked.connect(
            self.select_sentence_file
        )


        sentence_layout.addWidget(
            self.sentence_input
        )

        sentence_layout.addWidget(
            sentence_button
        )


        layout.addLayout(
            sentence_layout
        )



        # -------------------------
        # Product index path
        # -------------------------

        layout.addWidget(
            QLabel("Product Index Path")
        )


        product_layout = QHBoxLayout()


        self.product_input = QLineEdit()

        self.product_input.setText(
            self.product_index_path
        )


        product_button = QPushButton(
            "Browse"
        )


        product_button.clicked.connect(
            self.select_product_path
        )


        product_layout.addWidget(
            self.product_input
        )

        product_layout.addWidget(
            product_button
        )


        layout.addLayout(
            product_layout
        )



        # -------------------------
        # Output CSV
        # -------------------------

        layout.addWidget(
            QLabel("Output CSV")
        )


        output_layout = QHBoxLayout()


        self.output_input = QLineEdit()


        self.output_input.setText(
            self.output_csv_path
        )


        output_button = QPushButton(
            "Save"
        )


        output_button.clicked.connect(
            self.select_output_file
        )


        output_layout.addWidget(
            self.output_input
        )

        output_layout.addWidget(
            output_button
        )


        layout.addLayout(
            output_layout
        )



        # -------------------------
        # Run button
        # -------------------------

        self.run_button = QPushButton(
            "Run SKU Export"
        )


        self.run_button.clicked.connect(
            self.start_pipeline
        )


        layout.addWidget(
            self.run_button
        )



        # -------------------------
        # Log window
        # -------------------------

        layout.addWidget(
            QLabel("Progress")
        )


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




    # ========================================================
    # File selectors
    # ========================================================


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


    def select_sentence_file(self):

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select sentence corpus",
            "",
            "JSONL Files (*.jsonl)"
        )


        if path:

            self.sentence_input.setText(
                self.display_path(path)
            )




    def select_product_path(self):

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Product Index Cache",
            "",
            "MsgPack Files (*.msgpack);;All Files (*)"
        )


        if path:

            self.product_input.setText(
                self.display_path(path)
            )




    def select_output_file(self):

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV",
            "",
            "CSV Files (*.csv)"
        )


        if path:

            self.output_input.setText(
                self.display_path(path)
            )



    # ========================================================
    # Run backend
    # ========================================================

    def start_pipeline(self):

        manufacturer = (
            self.manufacturer_input.text()
            .strip()
        )


        sentence_path = (
            self.sentence_input.text()
            .strip()
        )


        product_path = (
            self.product_input.text()
            .strip()
        )


        output_path = (
            self.output_input.text()
            .strip()
        )


        if not all(
            [
                manufacturer,
                sentence_path,
                product_path,
                output_path,
            ]
        ):

            self.log.append(
                "Missing input fields."
            )

            return



        self.log.clear()


        self.run_button.setEnabled(
            False
        )


        # self.log.append(
        #     "Starting pipeline..."
        # )



        self.worker = SKUResultsWorker(
            manufacturer,
            sentence_path,
            product_path,
            output_path,
        )


        self.worker.progress.connect(
            self.update_log
        )


        self.worker.pipeline_finished.connect(
            self.pipeline_finished
        )


        self.worker.error.connect(
            self.pipeline_error
        )


        self.worker.start()




    def update_log(self, message):

        self.log.append(
            message
        )




    def pipeline_finished(self):

        self.log.append(
            "DONE!"
        )


        self.run_button.setEnabled(
            True
        )




    def pipeline_error(self, error):

        self.log.append(
            f"ERROR:\n{error}"
        )


        self.run_button.setEnabled(
            True
        )



    def closeEvent(self, event):
        
        self.closed.emit()

        event.accept()

