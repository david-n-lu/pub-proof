"""
main.py

Entry point for the Product Annotator application.
"""

import sys

from PySide6.QtWidgets import QApplication

from annotator.annotator_window import AnnotatorWindow


def main():
    app = QApplication(sys.argv)

    window = AnnotatorWindow(
        manufacturer="GeneCopoeia",

        product_map_path=
            "data/raw_products/",

        sentence_path=
            "data/europe_pmc/genecopoeia_sentences.jsonl",

        annotation_path=
            "annotator/annotations.json",

        auto_match_path=
            "annotator/auto_results.json",
    )

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()