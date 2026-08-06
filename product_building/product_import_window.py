from pathlib import Path
import shutil
import json

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QFileDialog,
    QMessageBox,
    QComboBox,
    QMessageBox,
    QDialog,
)
from PySide6.QtCore import Qt, Signal, QThread

from product_building.product_import import (
    get_column_counts,
    save_trademark_names
)

from product_building.product_index_window import ProductIndexProgressDialog
from product_building.product_index_worker import ProductIndexWorker

from PySide6.QtGui import QFont


class ProductImportWindow(QWidget):

    closed = Signal()

    def __init__(self, project_dir, product_index_cache_path, manufacturer):
        super().__init__()

        self.project_dir = Path(project_dir)
        self.products_dir = self.project_dir / "products"
        self.products_dir.mkdir(parents=True, exist_ok=True)

        self.product_index_cache_path = product_index_cache_path

        self.manufacturer = manufacturer

        self.setWindowTitle("Import Product CSVs")
        self.resize(500, 400)

        self.setFont(QFont("Segoe UI", 11))

        self.selected_files = []

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Selected CSV files:"))

        self.file_list = QListWidget()
        layout.addWidget(self.file_list)

        self.select_button = QPushButton("Select CSV Files")
        self.select_button.clicked.connect(self.select_files)
        layout.addWidget(self.select_button)

        self.import_button = QPushButton("Import")
        self.import_button.clicked.connect(self.import_files)
        layout.addWidget(self.import_button)


        def path_exists(path):
            return Path(path).exists()

        def directory_not_empty(path):
            return path_exists(path) and any(Path(path).iterdir())


        if directory_not_empty(self.products_dir):
            self.import_button.setText("Reimport")

        layout.addSpacing(6)

        label = QLabel("After importing, choose relevant .csv columns for matching")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        layout.addSpacing(3)

        self.column_button = QPushButton("Choose Columns")
        self.column_button.pressed.connect(self.open_column_window)
        layout.addWidget(self.column_button)

        

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Product CSV Files",
            "",
            "CSV Files (*.csv)",
        )

        if not files:
            return

        self.selected_files = files

        self.file_list.clear()
        self.file_list.addItems(files)

    def import_files(self):
        if not self.selected_files:
            QMessageBox.warning(
                self,
                "No Files",
                "Please select at least one CSV file."
            )
            return

        copied = 0

        for file in self.selected_files:
            src = Path(file)
            dst = self.products_dir / src.name

            shutil.copy2(src, dst)
            copied += 1

        QMessageBox.information(
            self,
            "Import Complete",
            f"Imported {copied} CSV file(s)."
        )

        # self.close()


    def open_column_window(self):

        self.column_window = ProductColumnWindow(
            self.project_dir,
            self.product_index_cache_path,
            self.manufacturer,
        )

        self.column_window.closed.connect(
            self.close
        )

        self.column_window.show()

        self.hide()



    def closeEvent(self, event):
        
        self.closed.emit()

        event.accept()







class ProductColumnWindow(QWidget):

    closed = Signal()

    def __init__(self, project_dir, product_index_cache_path, manufacturer):
        super().__init__()

        self.project_dir = Path(project_dir)
        self.products_dir = self.project_dir / "products"
        self.product_index_cache_path = product_index_cache_path

        self.manufacturer = manufacturer

        self.setWindowTitle(
            "Select Product Columns"
        )

        self.resize(500, 225)

        self.setFont(QFont("Segoe UI", 11))

        self.setup_ui()
        self.load_columns()


    def setup_ui(self):

        layout = QVBoxLayout(self)

        layout.addWidget(
            QLabel("SKU Column: Unique product identifier")
        )

        self.sku_combo = QComboBox()
        layout.addWidget(
            self.sku_combo
        )


        layout.addWidget(
            QLabel("Product Name Column: Standard product name used for matching")
        )

        self.name_combo = QComboBox()
        layout.addWidget(
            self.name_combo
        )


        layout.addWidget(
            QLabel("Description Column: Extra column for matching if product name ambiguous")
        )

        self.description_combo = QComboBox()
        layout.addWidget(
            self.description_combo
        )


        layout.addSpacing(10)


        self.product_index_button = QPushButton(
            "Create Product Index"
        )

        self.product_index_button.clicked.connect(
            self.create_product_index
        )

        layout.addWidget(
            self.product_index_button
        )


        # self.save_button = QPushButton(
        #     "Save Columns"
        # )

        # self.save_button.clicked.connect(
        #     self.save_columns
        # )

        # layout.addWidget(
        #     self.save_button
        # )


    def load_columns(self):

        counts = get_column_counts(
            self.products_dir
        )

        columns = sorted(
            counts,
            key=counts.get,
            reverse=True
        )
        

        self.sku_combo.addItems(columns)
        self.name_combo.addItems(columns)
        self.description_combo.addItems(columns)

        if self.sku_combo.count() > 0:
            self.sku_combo.setCurrentIndex(0)

        if self.name_combo.count() > 1:
            self.name_combo.setCurrentIndex(1)

        if self.description_combo.count() > 2:
            self.description_combo.setCurrentIndex(2)


    def save_columns(self):

        config_path = (
            self.project_dir /
            "project.json"
        )

        if config_path.exists():
            with open(
                config_path,
                "r",
                encoding="utf-8"
            ) as f:
                config = json.load(f)
        else:
            config = {
                "manufacturer": self.manufacturer
            }


        config["product_columns"] = {
            "sku": self.sku_combo.currentText(),
            "product_name": self.name_combo.currentText(),
            "description": self.description_combo.currentText(),
        }


        with open(
            config_path,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                config,
                f,
                indent=4
            )

        return config["product_columns"]


    def create_product_index(self):
        config = self.save_columns()

        dialog = ProductIndexProgressDialog()

        self.thread = QThread()

        self.worker = ProductIndexWorker(
            self.products_dir,
            self.product_index_cache_path,
            config["sku"],
            config["product_name"],
            config["description"],
            self.project_dir / "project.json",
        )

        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)

        self.worker.finished.connect(dialog.accept)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.progress.connect(dialog.update_progress)
        self.thread.finished.connect(self.thread.deleteLater)

        self.worker.finished.connect(self.close)

        self.worker.error.connect(print)

        self.thread.start()

        dialog.exec()



    def closeEvent(self, event):
        
        self.closed.emit()

        event.accept()






if __name__ == "__main__":

    import sys

    from PySide6.QtWidgets import QApplication


    app = QApplication(sys.argv)


    window = ProductImportWindow(
        project_dir = "C:/Users/jingh/Projects/BioEvidence_GeneCopoeia"
    )

    window.show()


    sys.exit(
        app.exec()
    )