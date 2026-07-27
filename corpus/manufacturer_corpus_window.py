"""
manufacturer_corpus_window.py

PySide6 UI for building a manufacturer sentence corpus.

Runs:
    build_manufacturer_sentence_corpus()

inside a QThread so the UI remains responsive.
"""


import os

from PySide6.QtCore import (
    QThread,
    Signal,
)

from PySide6.QtWidgets import (
    QWidget,
)


from corpus.manufacturer_corpus import (
    build_manufacturer_sentence_corpus,
)


# ---------------------------------------------------------
# Worker Thread
# ---------------------------------------------------------

class ManufacturerCorpusWorker(QThread):
    """
    Runs manufacturer corpus generation in background.

    Signals:
        progress(current, total)
        log(message)
        finished()
        error(message)
    """

    progress = Signal(int, int)

    log = Signal(str)

    error = Signal(str)


    def __init__(
        self,
        input_path,
        output_path,
        manufacturer,
        documents_to_process,
        batch_size,
        clear_output,
        start_line,
        resume,
    ):

        super().__init__()


        self.input_path = input_path

        self.output_path = output_path

        self.manufacturer = manufacturer

        self.documents_to_process = documents_to_process

        self.batch_size = batch_size

        self.clear_output = clear_output

        self.start_line = start_line

        self.resume = resume

        self.cancel_requested = False



    # Store latest processed line for recovery
    def update_current_line(self, line):
        
        self.current_line = line


    # -----------------------------------------------------
    # Cancel
    # -----------------------------------------------------

    def cancel(self):
        """
        Request cancellation.

        Does not force kill the thread.
        The backend exits safely.
        """

        self.cancel_requested = True



    def should_cancel(self):
        """
        Callback used by backend.
        """

        return self.cancel_requested



    # -----------------------------------------------------
    # Backend callbacks
    # -----------------------------------------------------

    def send_log(self, message):
        """
        Forward backend logs to UI.
        """

        self.log.emit(
            message
        )



    def update_progress(
        self,
        current,
        total
    ):
        """
        Forward progress updates.
        """

        self.progress.emit(
            current,
            total
        )



    # -----------------------------------------------------
    # Thread entry point
    # -----------------------------------------------------

    def run(self):

        try:

            build_manufacturer_sentence_corpus(

                input_path=self.input_path,

                output_path=self.output_path,

                manufacturer=self.manufacturer,

                documents_to_process=self.documents_to_process,

                batch_size=self.batch_size,

                clear_output=self.clear_output,

                start_line=self.start_line,

                resume=self.resume,

                progress_callback=self.update_progress,

                log_callback=self.send_log,

                should_cancel=self.should_cancel,
            )


            self.finished.emit()


        except Exception as e:

            self.error.emit(
                str(e)
            )



# ---------------------------------------------------------
# Main Window
# ---------------------------------------------------------

from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QSpinBox,
    QCheckBox,
    QTextEdit,
    QProgressBar,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
)


class ManufacturerCorpusWindow(QWidget):
    """
    UI for manufacturer corpus generation.
    """

    closed = Signal()

    def __init__(
        self,
        publications_path,
        sentences_path,
        ):

        super().__init__()

        self.publications_path = publications_path
        self.sentences_path = sentences_path

        self.worker = None


        self.setWindowTitle(
            "Manufacturer Corpus Builder"
        )


        self.resize(
            800,
            700
        )


        self.setup_ui()



    # -----------------------------------------------------
    # UI Setup
    # -----------------------------------------------------

    def setup_ui(self):

        layout = QVBoxLayout()


        # ---------------------------------------------
        # Paths
        # ---------------------------------------------

        path_group = QGroupBox(
            "Files"
        )

        path_layout = QVBoxLayout()


        # input
        input_row = QHBoxLayout()

        self.input_edit = QLineEdit(
            self.publications_path
        )

        input_button = QPushButton(
            "Browse"
        )

        input_button.clicked.connect(
            self.browse_input
        )


        input_row.addWidget(
            QLabel("Input JSONL:")
        )

        input_row.addWidget(
            self.input_edit
        )

        input_row.addWidget(
            input_button
        )


        # output
        output_row = QHBoxLayout()


        self.output_edit = QLineEdit(
            self.sentences_path
        )


        output_button = QPushButton(
            "Browse"
        )

        output_button.clicked.connect(
            self.browse_output
        )


        output_row.addWidget(
            QLabel("Output JSONL:")
        )

        output_row.addWidget(
            self.output_edit
        )

        output_row.addWidget(
            output_button
        )


        path_layout.addLayout(
            input_row
        )

        path_layout.addLayout(
            output_row
        )


        path_group.setLayout(
            path_layout
        )

        layout.addWidget(
            path_group
        )


        # ---------------------------------------------
        # Settings
        # ---------------------------------------------

        settings_group = QGroupBox(
            "Settings"
        )

        settings_layout = QVBoxLayout()


        # manufacturer

        manufacturer_row = QHBoxLayout()

        self.manufacturer_edit = QLineEdit(
            "GeneCopoeia"
        )


        manufacturer_row.addWidget(
            QLabel("Manufacturer:")
        )

        manufacturer_row.addWidget(
            self.manufacturer_edit
        )


        settings_layout.addLayout(
            manufacturer_row
        )


        # numeric settings

        self.start_line_spin = QSpinBox()

        self.start_line_spin.setRange(
            1,
            10_000_000
        )

        self.start_line_spin.setValue(
            0
        )


        self.documents_to_process_spin = QSpinBox()

        self.documents_to_process_spin.setRange(
            0,
            10_000_000
        )

        self.documents_to_process_spin.setSpecialValueText(
            "All Remaining"
        )

        self.batch_size_spin = QSpinBox()

        self.batch_size_spin.setRange(
            1,
            10000
        )

        self.batch_size_spin.setValue(
            100
        )


        settings_layout.addLayout(
            self.create_row(
                "Start from line:",
                self.start_line_spin
            )
        )

        settings_layout.addLayout(
            self.create_row(
                "Documents to process:",
                self.documents_to_process_spin
            )
        )

        settings_layout.addLayout(
            self.create_row(
                "Batch size:",
                self.batch_size_spin
            )
        )


        self.clear_checkbox = QCheckBox(
            "Clear output before starting"
        )

        self.clear_checkbox.setChecked(
            True
        )

        settings_layout.addWidget(
            self.clear_checkbox
        )


        self.resume_checkbox = QCheckBox(
            "Resume from checkpoint"
        )

        self.resume_checkbox.setChecked(
            True
        )

        self.clear_checkbox.toggled.connect(
            self.toggle_resume_checkbox
        )

        self.toggle_resume_checkbox(
            self.clear_checkbox.isChecked()
        )

        settings_layout.addWidget(
            self.resume_checkbox
        )


        settings_group.setLayout(
            settings_layout
        )

        layout.addWidget(
            settings_group
        )


        # ---------------------------------------------
        # Controls
        # ---------------------------------------------

        button_row = QHBoxLayout()


        self.start_button = QPushButton(
            "Start"
        )

        self.start_button.clicked.connect(
            self.start_worker
        )


        self.cancel_button = QPushButton(
            "Cancel"
        )

        self.cancel_button.clicked.connect(
            self.cancel_worker
        )

        self.cancel_button.setEnabled(
            False
        )


        button_row.addWidget(
            self.start_button
        )

        button_row.addWidget(
            self.cancel_button
        )


        layout.addLayout(
            button_row
        )


        # ---------------------------------------------
        # Progress
        # ---------------------------------------------

        self.progress_bar = QProgressBar()

        self.progress_bar.setValue(
            0
        )

        layout.addWidget(
            self.progress_bar
        )


        self.progress_label = QLabel(
            "0 / 0"
        )

        layout.addWidget(
            self.progress_label
        )


        # ---------------------------------------------
        # Logs
        # ---------------------------------------------

        self.log_box = QTextEdit()

        self.log_box.setReadOnly(
            True
        )


        layout.addWidget(
            self.log_box
        )


        self.setLayout(
            layout
        )





# -----------------------------------------------------
    # UI Helpers
    # -----------------------------------------------------

    def create_row(
        self,
        label,
        widget
    ):
        """
        Create a simple label + widget row.
        """

        row = QHBoxLayout()

        row.addWidget(
            QLabel(label)
        )

        row.addWidget(
            widget
        )

        return row


    # -----------------------------------------------------
    # Checkbox Behavior
    # -----------------------------------------------------

    def toggle_resume_checkbox(self, checked):
        """
        Disable checkpoint resume when clearing output.
        """

        self.resume_checkbox.setEnabled(
            not checked
        )

        if checked:
            self.resume_checkbox.setChecked(
                False
            )


    # -----------------------------------------------------
    # File Browsers
    # -----------------------------------------------------

    def browse_input(self):

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Input JSONL",
            "",
            "JSONL Files (*.jsonl)"
        )

        if path:

            self.input_edit.setText(
                path
            )



    def browse_output(self):

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Select Output JSONL",
            "",
            "JSONL Files (*.jsonl)"
        )

        if path:

            self.output_edit.setText(
                path
            )



    # -----------------------------------------------------
    # Worker Control
    # -----------------------------------------------------

    def start_worker(self):

        if self.worker and self.worker.isRunning():

            return


        input_path = self.input_edit.text()

        output_path = self.output_edit.text()


        manufacturer = (
            self.manufacturer_edit.text()
            .strip()
        )


        documents_to_process = (
            self.documents_to_process_spin.value()
            if self.documents_to_process_spin.value() > 0
            else None
        )


        batch_size = (
            self.batch_size_spin.value()
        )


        start_line = (
            self.start_line_spin.value()
        )


        clear_output = (
            self.clear_checkbox.isChecked()
        )


        resume = (
            self.resume_checkbox.isChecked()
        )


        self.log_box.clear()


        self.progress_bar.setValue(
            0
        )


        self.worker = ManufacturerCorpusWorker(
            input_path=input_path,
            output_path=output_path,
            manufacturer=manufacturer,
            documents_to_process=documents_to_process,
            batch_size=batch_size,
            clear_output=clear_output,
            start_line=start_line,
            resume=resume,
        )


        # ---------------------------------------------
        # Connect signals
        # ---------------------------------------------

        self.worker.progress.connect(
            self.update_progress
        )

        self.worker.log.connect(
            self.append_log
        )

        self.worker.finished.connect(
            self.worker_finished
        )

        self.worker.error.connect(
            self.worker_error
        )


        # ---------------------------------------------
        # Button state
        # ---------------------------------------------

        self.start_button.setEnabled(
            False
        )

        self.cancel_button.setEnabled(
            True
        )


        self.worker.start()



    def cancel_worker(self):

        if self.worker:

            self.worker.cancel()

            self.append_log(
                "[CANCEL REQUESTED]"
            )



    # -----------------------------------------------------
    # Updates
    # -----------------------------------------------------

    def update_progress(
        self,
        current,
        total
    ):

        if total <= 0:

            return


        percent = int(
            current / total * 100
        )


        self.progress_bar.setValue(
            percent
        )


        self.progress_label.setText(
            f"{current} / {total}"
        )



    def append_log(
        self,
        message
    ):

        self.log_box.append(
            message
        )


        # auto scroll
        scrollbar = (
            self.log_box.verticalScrollBar()
        )

        scrollbar.setValue(
            scrollbar.maximum()
        )



    # -----------------------------------------------------
    # Worker Completion
    # -----------------------------------------------------

    def worker_finished(self):

        self.append_log(
            "[DONE] Manufacturer corpus complete"
        )


        self.start_button.setEnabled(
            True
        )

        self.cancel_button.setEnabled(
            False
        )


        self.worker = None



    def worker_error(
        self,
        message
    ):

        self.append_log(
            f"[ERROR] {message}"
        )


        self.start_button.setEnabled(
            True
        )

        self.cancel_button.setEnabled(
            False
        )


        self.worker = None


    def closeEvent(self, event):
        
        self.closed.emit()

        event.accept()





if __name__ == "__main__":

    import sys

    from PySide6.QtWidgets import QApplication


    app = QApplication(sys.argv)


    window = ManufacturerCorpusWindow(
        publications_path = "data/europe_pmc/genecopoeia.jsonl",
        sentences_path = "data/europe_pmc/genecoppoeia_sentences.jsonl"
    )

    window.show()


    sys.exit(
        app.exec()
    )