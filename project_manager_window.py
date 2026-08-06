"""
project_manager_window.py

Main BioEvidence project dashboard.

TODO:
    - Load project.json
    - Display manufacturer status
    - Connect pipeline buttons
    - Track progress
"""


import sys
from PySide6.QtWidgets import QApplication

from annotator.annotator_window import AnnotatorWindow
from citation_generator.annotation_results_window import CitationGeneratorWindow
from citation_generator.sku_results_window import SKUResultsWindow
from corpus.downloader_window import DownloaderWindow
from corpus.manufacturer_corpus_window import ManufacturerCorpusWindow
from product_building.product_import_window import ProductImportWindow



from pathlib import Path
import json
import re

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
)
from PySide6.QtGui import QFont



class ProjectManagerWindow(QWidget):


    def __init__(
        self,
        project_dir,
    ):

        super().__init__()


        self.project_dir = Path(
            project_dir
        )


        self.manufacturer = self.get_manufacturer()


        safe_manufacturer_name = safe_filename(self.manufacturer)
        self.publications_path = f"{project_dir}/publications/{safe_manufacturer_name}_publications.jsonl"
        self.sentences_path = f"{project_dir}/sentences/{safe_manufacturer_name}_sentences.jsonl"
        self.sku_citations_path = f"{project_dir}/citations/{safe_manufacturer_name}_sku_citations.csv"
        self.auto_results_path = f"{project_dir}/annotations/{safe_manufacturer_name}_auto_results.json"
        self.annotations_path = f"{project_dir}/annotations/{safe_manufacturer_name}_annotations.json"
        self.annotation_citations_path = f"{project_dir}/citations/{safe_manufacturer_name}_annotation_citations.csv"

        self.product_index_cache_path = f"{project_dir}/cache/product_index.msgpack"
        self.genes_path = f"data/genes.csv"
        

        self.setWindowTitle(
            "BioEvidence Project"
        )


        # self.resize(
        #     800,
        #     400
        # )
        self.setFixedWidth(800)

        self.setFont(QFont("Segoe UI", 11))

        self.setup_ui()



    # =====================================================
    # UI
    # =====================================================

    def setup_ui(self):

        scroll = QScrollArea()

        scroll.setWidgetResizable(
            True
        )


        content = QWidget()

        layout = QVBoxLayout(
            content
        )


        # -------------------------
        # Project info
        # -------------------------

        layout.addWidget(
            QLabel(
                f"Project: {self.project_dir}"
            )
        )


        layout.addSpacing(
            20
        )


        # -------------------------
        # Pipeline
        # -------------------------


        self.download_button = self.add_button(
            layout,
            "1. Download Publications",
        )


        self.sentences_button = self.add_button(
            layout,
            "2. Extract Sentences",
        )


        self.products_button = self.add_button(
            layout,
            "3. Upload Products",
        )


        self.sku_citations_button = self.add_button(
            layout,
            "4. Export SKU Citations",
        )


        self.annotations_button = self.add_button(
            layout,
            "5A. Annotate Product Mentions in Sentences",
        )


        self.annotation_citations_button = self.add_button(
            layout,
            "5B. Export Annotation Citations",
        )

        self.refresh_buttons()


        layout.addStretch()


        scroll.setWidget(
            content
        )


        main_layout = QVBoxLayout(
            self
        )


        main_layout.addWidget(
            scroll
        )



        self.download_button.pressed.connect(
            self.open_downloader_window
        )

        self.sentences_button.pressed.connect(
            self.open_sentences_window
        )

        self.products_button.pressed.connect(
            self.open_products_window
        )

        self.sku_citations_button.pressed.connect(
            self.open_sku_window
        )

        self.annotations_button.pressed.connect(
            self.open_annotator_window
        )

        self.annotation_citations_button.pressed.connect(
            self.open_annotation_citations_window
        )



    def refresh_buttons(self):

        def path_exists(path):
            return Path(path).exists()

        def directory_not_empty(path):
            return path_exists(path) and any(Path(path).iterdir())


        if path_exists(self.publications_path):
            self.download_button.setText("1. Redownload Publications")

        if path_exists(self.sentences_path):
            self.sentences_button.setText("2. Extract Sentences Again")

        if directory_not_empty(f"{self.project_dir}/products") and path_exists(self.product_index_cache_path):
            self.products_button.setText("3. Reupload Products")
        elif directory_not_empty(f"{self.project_dir}/products"):
            self.products_button.setText("3. Create Product Index")

        if path_exists(self.sku_citations_path):
            self.sku_citations_button.setText("4. Export SKU Citations Again")

        if path_exists(self.sku_citations_path):
            self.annotation_citations_button.setText("5B. Export Annotation Citations Again")



        if path_exists(self.publications_path):
            self.sentences_button.setEnabled(True)
        else:
            self.sentences_button.setEnabled(False)

        if path_exists(self.sentences_path) and path_exists(self.product_index_cache_path):
            self.sku_citations_button.setEnabled(True)
        else:
            self.sku_citations_button.setEnabled(False)

        if path_exists(self.sentences_path) and path_exists(self.product_index_cache_path):
            self.annotations_button.setEnabled(True)
        else:
            self.annotations_button.setEnabled(False)

        if path_exists(self.annotations_path) and path_exists(self.auto_results_path):
            self.annotation_citations_button.setEnabled(True)
        else:
            self.annotation_citations_button.setEnabled(False)



    def add_button(
        self,
        layout,
        name,
    ):

        button = QPushButton(
            # "Open"
            name
        )

        button.setMinimumHeight(40)

        layout.addWidget(
            button
        )

        return button



    def get_manufacturer(self):
        if not self.project_dir.exists():
        
            raise ValueError(
                "Project directory does not exist."
            )

        project_metadata_path = (
            self.project_dir /
            "project.json"
        )

        if not project_metadata_path.exists():

            raise ValueError(
                "Not a valid BioEvidence project."
            )

        with open(
            project_metadata_path,
            "r",
            encoding="utf-8"
        ) as f:

            project = json.load(f)


        return project.get(
            "manufacturer"
        )



    def show_manager(self):

        self.show()

        self.activateWindow()

        self.refresh_buttons()


    def open_downloader_window(self):

        self.downloader_window = DownloaderWindow(
            self.publications_path
        )

        self.downloader_window.closed.connect(
            self.show_manager
        )

        self.downloader_window.show()

        self.hide()


    def open_sentences_window(self):
    
        self.sentences_window = ManufacturerCorpusWindow(
            self.publications_path,
            self.sentences_path
        )

        self.sentences_window.closed.connect(
            self.show_manager
        )

        self.sentences_window.show()

        self.hide()


    def open_products_window(self):
        
        self.products_window = ProductImportWindow(
            self.project_dir,
            self.product_index_cache_path,
            self.manufacturer,
        )

        self.products_window.closed.connect(
            self.show_manager
        )

        self.products_window.show()

        self.hide()


    def open_sku_window(self):
            
        self.sku_window = SKUResultsWindow(
            self.manufacturer,
            self.sentences_path,
            self.product_index_cache_path,
            self.sku_citations_path,
        )

        self.sku_window.closed.connect(
            self.show_manager
        )

        self.sku_window.show()

        self.hide()


    def open_annotator_window(self):
                
        self.annotator_window = AnnotatorWindow(
            self.manufacturer,
            str(self.project_dir / "products"),
            self.product_index_cache_path,
            self.sentences_path,
            self.annotations_path,
            self.auto_results_path,
            str(self.project_dir / "project.json"),
            self.genes_path,
        )

        self.annotator_window.closed.connect(
            self.show_manager
        )

        # self.annotator_window.show()

        self.hide()



    def open_annotation_citations_window(self):
                    
        self.annotation_citations_window = CitationGeneratorWindow(
            self.annotations_path,
            self.auto_results_path,
            self.annotation_citations_path,
        )

        self.annotation_citations_window.closed.connect(
            self.show_manager
        )

        self.annotation_citations_window.show()

        self.hide()








WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

def safe_filename(filename: str) -> str:
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", filename)
    filename = filename.strip(" .")

    if filename.upper().split(".")[0] in WINDOWS_RESERVED:
        filename = "_" + filename

    return filename.lower() or "untitled"