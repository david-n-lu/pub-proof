from PySide6.QtCore import QObject, Signal


class MatcherWorker(QObject):

    finished = Signal()
    error = Signal(str)
    message = Signal(str)

    def __init__(self, backend):
        super().__init__()

        self.backend = backend


    def run(self):

        try:

            self.message.emit(
                "Running auto matcher..."
            )

            self.backend.run_auto_matcher()

            self.message.emit(
                "Finished."
            )

            self.finished.emit()

        except Exception as e:

            self.error.emit(str(e))