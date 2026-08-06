"""
loading_worker.py

Background worker for loading annotator data without freezing the UI.
"""

from PySide6.QtCore import QObject, Signal, Slot


class LoadingWorker(QObject):
    """
    Loads all annotator data in a background thread.

    Signals
    -------
    progress(str)
        Status message for the loading window.

    finished()
        Emitted when loading completes successfully.

    error(str)
        Emitted if an exception occurs.
    """

    progress = Signal(str)
    finished = Signal()
    error = Signal(str)

    def __init__(self, backend):
        super().__init__()

        self.backend = backend
        self.running = True


    @Slot()
    def run(self):
        """Perform backend initialization."""

        try:
            self.progress.emit("Loading products indexes...")
            self.backend.load_products()

            
            self.progress.emit("Loading genes database...")
            self.backend.load_genes()


            self.progress.emit("Loading sentences...")
            self.backend.load_sentences()


            self.progress.emit("Loading annotations...")
            self.backend.load_annotations()


            self.progress.emit("Loading auto matches...")
            self.backend.load_auto_results()


            self.progress.emit("Done!")

            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))