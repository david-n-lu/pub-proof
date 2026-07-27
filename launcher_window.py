from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QMessageBox
)
from PySide6.QtGui import QFont
from PySide6.QtCore import QSettings

from launcher import ProjectLauncher
from project_manager_window import ProjectManagerWindow


class LauncherWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.settings = QSettings(
            "BioEvidence",
            "BioEvidence"
        )

        self.launcher = ProjectLauncher()

        self.setFont(QFont("Segoe UI", 11))

        self.setWindowTitle("BioEvidence Launcher")
        self.setMinimumWidth(500)

        self.setup_ui()
        self.load_last_project()


    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # =========================
        # Create New Project
        # =========================

        create_group = QGroupBox("Create new project")
        create_layout = QVBoxLayout()

        # Working directory
        create_directory_layout = QHBoxLayout()

        self.create_directory_edit = QLineEdit()
        self.create_directory_edit.setPlaceholderText(
            "Select working directory"
        )

        self.create_directory_button = QPushButton("Browse")
        self.create_directory_button.clicked.connect(
            lambda: self.select_directory(
                self.create_directory_edit
            )
        )

        create_directory_layout.addWidget(
            self.create_directory_edit
        )
        create_directory_layout.addWidget(
            self.create_directory_button
        )

        # Manufacturer
        manufacturer_layout = QHBoxLayout()

        manufacturer_label = QLabel("Manufacturer:")

        self.manufacturer_edit = QLineEdit()
        self.manufacturer_edit.setPlaceholderText(
            "Enter manufacturer"
        )

        manufacturer_layout.addWidget(
            manufacturer_label
        )
        manufacturer_layout.addWidget(
            self.manufacturer_edit
        )

        # Create button
        self.create_project_button = QPushButton(
            "Create Project"
        )

        self.create_project_button.clicked.connect(
            self.create_project
        )

        create_layout.addLayout(
            create_directory_layout
        )
        create_layout.addLayout(
            manufacturer_layout
        )
        create_layout.addWidget(
            self.create_project_button
        )

        create_group.setLayout(
            create_layout
        )


        # =========================
        # Open Existing Project
        # =========================

        open_group = QGroupBox("Open existing project")
        open_layout = QVBoxLayout()

        # Project directory
        open_directory_layout = QHBoxLayout()

        self.open_directory_edit = QLineEdit()
        self.open_directory_edit.setPlaceholderText(
            "Select project directory"
        )

        self.open_directory_button = QPushButton(
            "Browse"
        )

        self.open_directory_button.clicked.connect(
            lambda: self.select_directory(
                self.open_directory_edit
            )
        )

        open_directory_layout.addWidget(
            self.open_directory_edit
        )
        open_directory_layout.addWidget(
            self.open_directory_button
        )

        # Open button
        self.open_project_button = QPushButton(
            "Open Project"
        )

        self.open_project_button.clicked.connect(
            self.open_project
        )

        open_layout.addLayout(
            open_directory_layout
        )
        open_layout.addWidget(
            self.open_project_button
        )

        open_group.setLayout(
            open_layout
        )


        # =========================
        # Final Layout
        # =========================

        main_layout.addWidget(
            create_group
        )

        main_layout.addWidget(
            open_group
        )

        main_layout.addStretch()


    def select_directory(self, line_edit):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory"
        )

        if directory:
            line_edit.setText(directory)


    # =========================
    # Backend Hooks
    # =========================

    def create_project(self):
        """
        Create project callback.
        Implement backend logic here.
        """
        
        try:
            working_directory = (
                self.create_directory_edit.text()
            )
    
            manufacturer = (
                self.manufacturer_edit.text()
            )

            project_dir = self.launcher.create_project(
                working_directory,
                manufacturer,
            )

            self.settings.setValue(
                "last_project",
                str(project_dir)
            )

            self.open_manager(
                project_dir
            )


        except Exception as e:

            QMessageBox.warning(
                self,
                "Cannot Create Project",
                str(e)
            )


    def open_project(self):
        """
        Open project callback.
        Implement backend logic here.
        """
        
        try:

            project_dir = (
                self.open_directory_edit.text()
            )
    
            project_dir = self.launcher.open_project(
                project_dir
            )

            self.settings.setValue(
                "last_project",
                str(project_dir)
            )

            self.open_manager(
                project_dir
            )


        except Exception as e:

            QMessageBox.warning(
                self,
                "Invalid Project",
                str(e)
            )


    def load_last_project(self):

        last_project = self.settings.value(
            "last_project",
            ""
        )

        if last_project:

            self.open_directory_edit.setText(
                last_project
            )

            self.open_project_button.setDefault(True)
            self.open_project_button.setFocus()


    def open_manager(
        self,
        project_dir,
    ):
        self.project_window = ProjectManagerWindow(
            project_dir
        )

        self.project_window.show()

        self.close()