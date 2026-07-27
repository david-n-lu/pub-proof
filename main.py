import sys
from PySide6.QtWidgets import QApplication

from launcher_window import LauncherWindow


app = QApplication(sys.argv)

window = LauncherWindow()
window.show()

sys.exit(app.exec())