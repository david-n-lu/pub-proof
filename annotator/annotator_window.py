"""
annotator_window.py

PySide6 frontend for product annotator.
"""

from PySide6.QtCore import (
    QTimer,
    Qt,
    QThread,
    Signal,
)

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QPushButton,
    QLabel,
    QTextEdit,
    QProgressBar,
    QSplitter,
    QComboBox,
    QLineEdit,
    QScrollArea,
    QCheckBox,
    QMessageBox,
    QApplication,
    QDialog,
    QSizePolicy,
)

from PySide6.QtGui import QFont, QShortcut, QKeySequence
from click import edit

from annotator.annotator_backend import AnnotatorBackend
from annotator.highlighter import highlight_sentence
from annotator.matcher_worker import MatcherWorker

from annotator.loading_window import LoadingWindow
from annotator.loading_worker import LoadingWorker
from matching.normalization import normalize_for_matching


class AnnotatorWindow(QWidget):

    closed = Signal()

    def __init__(
        self,
        manufacturer,
        product_map_path,
        product_index_path,
        sentence_path,
        annotation_path,
        auto_match_path,
        config_path = None,
        genes_path = None,
        genes_product_map_path = None,
    ):
        super().__init__()


        self.backend = AnnotatorBackend(
            manufacturer=manufacturer,
            product_map_path=product_map_path,
            product_index_path=product_index_path,
            sentence_path=sentence_path,
            annotation_path=annotation_path,
            auto_match_path=auto_match_path,
            config_path=config_path,
            genes_path=genes_path,
            gene_product_map_path=genes_product_map_path,
        )
    

        # self.backend.initialize()


        self.thread = None
        self.worker = None
        self.loading = None


        self.auto_checkboxes = []
        self.search_checkboxes = []


        self._start_loading()


    def _start_loading(self):
        """
        Start loading the annotator backend in a background thread.
        """

        self.loading = LoadingWindow(self)
        self.loading.show()

        self.thread = QThread()

        self.worker = LoadingWorker(self.backend)
        self.worker.moveToThread(self.thread)

        # Start loading
        self.thread.started.connect(self.worker.run)

        # Update loading window
        self.worker.progress.connect(self.loading.set_status)

        # Success
        self.worker.finished.connect(self._finish_loading)

        # Error
        self.worker.error.connect(self._loading_error)

        # Cleanup
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.finished.connect(self.thread_deleted)

        self.thread.start()
    

    def _finish_loading(self):
        """
        Called when backend initialization completes.
        """

        self.loading.close()

        print("Annotator initialized.")

        self.setWindowTitle(
            "Product Annotator"
        )

        self.resize(
            1300,
            695,
        )

        font = QFont()
        font.setPointSize(11)

        self.setFont(font)

        self.center_window()


        self.build_ui()

        self.show()

    
    def _loading_error(self, message):
        """
        Called if initialization fails.
        """

        self.loading.close()

        QMessageBox.critical(
            self,
            "Initialization Error",
            message,
        )

        self.thread.quit()
    

    def center_window(self):
        screen = QApplication.primaryScreen().availableGeometry()

        x = (screen.width() - self.width()) // 2
        # y = (screen.height() - self.height()) // 2
        y = (screen.height() - self.height()) // 3

        self.move(x, y)


    # ============================================================
    # BUILD UI
    # ============================================================

    def build_ui(self):

        main_layout = QVBoxLayout(
            self
        )


        # ========================================================
        # AUTO MATCHER TOP PANEL
        # ========================================================

        matcher_group = QGroupBox(
            "Auto Matcher"
        )

        matcher_layout = QVBoxLayout(
            matcher_group
        )


        self.run_matcher_button = QPushButton(
            "Run Auto Matcher"
        )


        matcher_layout.addWidget(
            self.run_matcher_button
        )


        self.progress_bar = QProgressBar()

        matcher_layout.addWidget(
            self.progress_bar
        )


        self.log_box = QTextEdit()

        self.log_box.setMaximumHeight(
            56
        )


        self.log_box.setReadOnly(
            True
        )

        matcher_layout.addWidget(
            self.log_box
        )


        main_layout.addWidget(
            matcher_group,
            stretch=0
        )



        # ========================================================
        # BOTTOM SPLITTER
        # ========================================================

        splitter = QSplitter(
            Qt.Horizontal
        )



        # ========================================================
        # LEFT: ANNOTATION
        # ========================================================

        annotation_group = QGroupBox(
            "Annotation"
        )

        annotation_layout = QVBoxLayout(
            annotation_group
        )

        


        # navigation

        nav_layout = QHBoxLayout()


        self.previous_button = QPushButton(
            "Previous"
        )


        self.search_sentence_button = QPushButton(
            "Search Sentence"
        )


        self.next_button = QPushButton(
            "Next"
        )


        nav_layout.addWidget(
            self.previous_button
        )

        nav_layout.addWidget(
            self.search_sentence_button
        )

        nav_layout.addWidget(
            self.next_button
        )


        annotation_layout.addLayout(
            nav_layout
        )



        self.sentence_label = QLabel()

        self.sentence_label.setMinimumWidth(0)

        self.sentence_label.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Preferred
        )

        annotation_layout.addWidget(
            self.sentence_label
        )



        # highlighted sentence

        self.sentence_box = QTextEdit()

        self.sentence_box.setMaximumHeight(
            72
        )

        self.sentence_box.setReadOnly(
            True
        )

        annotation_layout.addWidget(
            self.sentence_box
        )



        # auto results scroll

        self.auto_scroll = QScrollArea()

        self.auto_scroll.setWidgetResizable(
            True
        )


        self.auto_widget = QWidget()


        self.auto_layout = QVBoxLayout(
            self.auto_widget
        )


        self.auto_scroll.setWidget(
            self.auto_widget
        )


        annotation_layout.addWidget(
            self.auto_scroll
        )



        # annotation buttons

        annotation_buttons = QHBoxLayout()


        self.save_button = QPushButton(
            "Save Annotation"
        )


        self.clear_button = QPushButton(
            "Clear Selection"
        )


        annotation_buttons.addWidget(
            self.save_button
        )


        annotation_buttons.addWidget(
            self.clear_button
        )


        annotation_layout.addLayout(
            annotation_buttons
        )


        splitter.addWidget(
            annotation_group
        )



        # ========================================================
        # RIGHT: MANUAL SEARCH
        # ========================================================

        search_group = QGroupBox(
            "Manual Product Search"
        )


        search_layout = QVBoxLayout(
            search_group
        )



        keyword_layout = QHBoxLayout()

        keyword_label = QLabel("Keyword:")

        keyword_layout.addWidget(
            keyword_label
        )

        self.keyword_edit = QLineEdit()

        keyword_layout.addWidget(
            self.keyword_edit,
            1
        )

        search_layout.addLayout(
            keyword_layout
        )


        column_filter_layout = QHBoxLayout()

        column_filter_label = QLabel("Column:")

        column_filter_layout.addWidget(
            column_filter_label
        )

        self.column_dropdown = QComboBox()

        column_filter_layout.addWidget(
            self.column_dropdown,
            1
        )

        self.search_button = QPushButton(
            "Search"
        )


        column_filter_layout.addWidget(
            self.search_button
        )


        search_layout.addLayout(
            column_filter_layout
        )

        
        filter_layout = QHBoxLayout()

        filter_label = QLabel("Filter Results:")

        filter_layout.addWidget(
            filter_label
        )

        self.filter_edit = QLineEdit()

        filter_layout.addWidget(
            self.filter_edit
        )

        self.filter_button = QPushButton(
            "Filter"
        )

        filter_layout.addWidget(
            self.filter_button
        )

        search_layout.addLayout(
            filter_layout
        )


        max_width = max(
            keyword_label.sizeHint().width(),
            column_filter_label.sizeHint().width(),
            # filter_label.sizeHint().width(),
        )

        padding = 10
        keyword_label.setFixedWidth(max_width + padding)
        column_filter_label.setFixedWidth(max_width + padding)
        # filter_label.setFixedWidth(max_width + padding)


        self.search_scroll = QScrollArea()

        self.search_scroll.setWidgetResizable(
            True
        )


        self.search_widget = QWidget()


        self.search_results_layout = QVBoxLayout(
            self.search_widget
        )


        self.search_scroll.setWidget(
            self.search_widget
        )


        search_layout.addWidget(
            self.search_scroll
        )

        self.search_status_label = QLabel(
            "Showing 0-0 of 0 products"
        )


        search_layout.addWidget(
            self.search_status_label
        )


        self.previous_page_button = QPushButton(
            "◀ Previous"
        )

        self.page_label = QLabel(
            "Page 1 of 1"
        )

        self.next_page_button = QPushButton(
            "Next ▶"
        )


        pagination_layout = QHBoxLayout()

        pagination_layout.addWidget(
            self.previous_page_button
        )

        pagination_layout.addStretch()

        pagination_layout.addWidget(
            self.page_label
        )

        pagination_layout.addStretch()

        pagination_layout.addWidget(
            self.next_page_button
        )


        search_layout.addLayout(
            pagination_layout
        )
        

        self.add_products_button = QPushButton(
            "Add Selected Products"
        )



        search_layout.addWidget(
            self.add_products_button
        )



        splitter.addWidget(
            search_group
        )



        splitter.setStretchFactor(
            0,
            3
        )

        splitter.setStretchFactor(
            1,
            2
        )

        splitter.setSizes([1050, 450])

        main_layout.addWidget(
            splitter,
            stretch=1
        )



        # ========================================================
        # STATUS
        # ========================================================

        self.status_label = QLabel()

        main_layout.addWidget(
            self.status_label
        )



        # ========================================================
        # INITIALIZE
        # ========================================================

        self.populate_search_columns()

        self.refresh_sentence()



        # ========================================================
        # SIGNALS
        # ========================================================

        self.previous_button.clicked.connect(
            self.previous_sentence
        )


        self.search_sentence_button.clicked.connect(
            self.open_go_to_dialog
        )


        self.next_button.clicked.connect(
            self.next_sentence
        )

        self.keyword_edit.returnPressed.connect(
            self.search_products
        )

        self.keyword_edit.returnPressed.connect(
            # self.keyword_edit.clearFocus
            self.filter_edit.setFocus
        )
        

        self.search_button.clicked.connect(
            self.search_products
        )

        self.filter_edit.returnPressed.connect(
            self.filter_search_results
        )

        self.filter_edit.returnPressed.connect(
            self.filter_edit.clearFocus
        )

        shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        shortcut.activated.connect(self.focus_filter)

        self.filter_button.clicked.connect(
            self.filter_search_results
        )

        self.previous_page_button.clicked.connect(
            self.on_previous_page
        )

        self.next_page_button.clicked.connect(
            self.on_next_page
        )


        self.add_products_button.clicked.connect(
            self.add_manual_products
        )


        self.save_button.clicked.connect(
            self.save_annotation
        )


        self.clear_button.clicked.connect(
            self.clear_selection
        )


        self.run_matcher_button.clicked.connect(
            self.run_auto_matcher
        )



        # existing matcher state

        if self.backend.has_auto_results():

            self.log_box.append(
                "Loaded existing matcher results."
            )

            self.run_matcher_button.setText(
                "Re-run Auto Matcher"
            )

        else:

            self.log_box.append(
                "No matcher results found."
            )


    # ============================================================
    # REFRESH FUNCTIONS
    # ============================================================

    def refresh_sentence(self):

        self.sentence_box.setHtml(
            self.backend.get_highlighted_sentence()
        )


        self.backend.load_current_selection()

        self.auto_select_results()

        self.populate_auto_matches()

        self.update_status()



    def update_status(self):

        current = (
            self.backend.current_sentence_index + 1
        )

        total = (
            self.backend.get_sentence_count()
        )

        annotated = (
            self.backend.get_annotation_count()
        )

        url = (
            self.backend.get_current_europe_pmc_url()
        )

        date = (
            self.backend.get_current_europe_pmc_date()
        )


        space = "\u00A0" * 5
        self.sentence_label.setText(
            f"Sentence: {current} / {total}{space}Date: {date}{space}URL: <a href=\"{url}\">{url}</a>"
        )
        self.sentence_label.setOpenExternalLinks(True)


        self.status_label.setText(
            f"Annotated: {annotated}"
        )



    def clear_layout(self, layout):

        while layout.count():

            item = layout.takeAt(0)

            widget = item.widget()

            if widget:

                widget.deleteLater()



    # ============================================================
    # POPULATE WIDGETS
    # ============================================================

    def populate_search_columns(self):

        self.column_dropdown.clear()

        self.column_dropdown.addItems(
            self.backend.get_search_columns()
        )



    def populate_auto_matches(self):

        self.clear_layout(
            self.auto_layout
        )

        self.auto_checkboxes = []

        matches = []
        checkmarks = []

        selected = self.backend.get_current_selected_products()
        auto_matches = self.backend.get_current_auto_matches()

        # don't duplicate automatches already in annotations
        auto_matches = [match for match in auto_matches if match not in selected]

        matches.extend(selected)
        matches.extend(auto_matches)

        checkmarks += [True] * len(selected)
        checkmarks += [False] * len(auto_matches)


        for i in range(len(matches)):

            checkbox_widget, checkbox = self.create_match_checkbox(
                matches[i],
                checkmarks[i],
            )

            self.auto_layout.addWidget(
                checkbox_widget
            )

            self.auto_checkboxes.append(
                checkbox
            )

        self.auto_layout.addStretch()

    def auto_select_results(self):
        
        if self.backend.current_has_annotation():
            return

        auto_matches = self.backend.get_current_auto_matches()

        max_value = max(m["score"] for m in auto_matches) if auto_matches else 0

        auto_matches = [m for m in auto_matches if m["score"] == max_value]

        auto_select_score_threshold = 0.85

        for match in auto_matches:
            if match.get("score", 0) >= auto_select_score_threshold:
                self.backend.select_product(match)
    

    def populate_search_results(self):

        self.update_search_labels(self.backend.get_product_keyword())

        self.clear_layout(
            self.search_results_layout
        )


        self.search_checkboxes = []

        products = self.backend.get_current_search_results()

        alias_columns = ["Alias", "Alias Names", "Gene Name", "Symbol", "Acession Number", "NCBI Accession"]

        for product in products:
            product_name = product.get("Product Name", "")
            sku = product.get("Part ID", "")
            description = product.get("Description", "")
            aliases = []

            for alias_col in alias_columns:
                alias = product.get(alias_col, "")
                
                if alias:
                    aliases.append(alias)
            
            aliases = ", ".join(aliases)
            

            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)

            row_layout.setContentsMargins(0, 0, 0, 0)
            # row_layout.setSpacing(0)

            checkbox = QCheckBox()
            label = QLabel(
                f"{product_name}<br>SKU: {sku}<br>Description: {description}<br>Aliases: {aliases}"
            )

            label.setTextInteractionFlags(
                Qt.TextSelectableByMouse |
                Qt.TextSelectableByKeyboard
            )

            row_layout.addWidget(checkbox, alignment=Qt.AlignTop)
            row_layout.addWidget(label)
            row_layout.addStretch()

            checkbox.product = product

            self.search_results_layout.addWidget(row_widget)


            self.search_checkboxes.append(
                checkbox
            )

        self.search_results_layout.addStretch()
    


    # ============================================================
    # NAVIGATION
    # ============================================================

    def previous_sentence(self):

        self.backend.previous_sentence()

        self.refresh_sentence()



    def next_sentence(self):

        self.backend.next_sentence()

        self.refresh_sentence()
    


    def on_previous_page(self):
        self.backend.previous_search_page()
        self.populate_search_results()


    def on_next_page(self):
        self.backend.next_search_page()
        self.populate_search_results()

    
    def open_go_to_dialog(self):
        dialog = GoToSentenceDialog(self, max_sentences=self.backend.get_sentence_count())

        dialog.first_unannotated_button.clicked.connect(
            lambda: (
                self.backend.first_unannotated(),
                self.refresh_sentence(),
                dialog.accept(),
            )
        )

        dialog.next_unannotated_button.clicked.connect(
            lambda: (
                self.backend.next_unannotated(),
                self.refresh_sentence(),
                # dialog.accept(),
            )
        )

        dialog.last_annotated_button.clicked.connect(
            lambda: (
                self.backend.last_annotated(),
                self.refresh_sentence(),
                dialog.accept(),
            )
        )

        dialog.go_button.clicked.connect(
            lambda: self.goto_sentence(dialog)
        )
        dialog.sentence_edit.returnPressed.connect(
            lambda: self.goto_sentence(dialog)
        )

        dialog.exec()


    def goto_sentence(self, dialog):

        text = dialog.sentence_edit.text().strip()

        try:
            index = int(text) - 1
        except ValueError:
            dialog.sentence_edit.clear()
            return

        if 0 <= index < self.backend.get_sentence_count():
            self.backend.goto_sentence(index)
            self.refresh_sentence()
            dialog.accept()
        else:
            dialog.sentence_edit.clear()


    # ============================================================
    # AUTO CHECKBOXES
    # ============================================================

    def auto_checkbox_changed(self):

        checkbox = self.sender()


        if checkbox.isChecked():

            self.backend.select_product(
                checkbox.product
            )


        else:

            self.backend.remove_product(
                checkbox.product
            )


    def create_match_checkbox(self, match, checked=False):
        """
        Creates a checkbox with a highlightable HTML label.

        Returns:
            QWidget containing checkbox + label
            QCheckBox reference
        """

        container = QWidget()

        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        checkbox = QCheckBox()
        
        

        checkbox.product = match
        checkbox.setChecked(checked)

        checkbox.toggled.connect(
            self.auto_checkbox_changed
        )

        layout.addWidget(checkbox, alignment=Qt.AlignTop)
        layout.addLayout(self.create_label_layout(match), 1)

        return container, checkbox


    RED_HIGHLIGHT = '<span style="background-color: red; color: black;">{}</span>'
    ORANGE_HIGHLIGHT = '<span style="background-color: orange; color: black;">{}</span>'
    YELLOW_HIGHLIGHT = '<span style="background-color: yellow; color: black;">{}</span>'
    GREEN_HIGHLIGHT = '<span style="background-color: lime; color: black;">{}</span>'

    def create_label_layout(self, match):
        info_layout = QVBoxLayout()

        info_layout.setSpacing(0)
        info_layout.setContentsMargins(0, 0, 0, 0)

        product = match["product_name"]
        phrase = match.get("phrase")
        sku = match["sku"].upper()
        match_method = match["type"]
        score = match["score"]

        if phrase:
            product = highlight_sentence(match["product_name"], self.backend.manufacturer, phrase.split(), {},)        

        if match_method == "sku":
            match_method = match_method.upper()
        else:
            match_method = match_method.capitalize()
        
        great_score = 0.8
        good_score = 0.6
        ok_score = 0.4

        highlight = self.GREEN_HIGHLIGHT if score >= great_score \
            else self.YELLOW_HIGHLIGHT if score >= good_score \
            else self.ORANGE_HIGHLIGHT if score >= ok_score \
        else self.RED_HIGHLIGHT

        score = "<b>" + highlight.format(f"Score: {score:.2f}") + "</b>"

        product_label = QLabel(f"{product}")
        score_label = QLabel(f"{score}")

        sku_row = QHBoxLayout()
        sku_row.addWidget(QLabel("SKU: "))

        if match_method == "Gene" or match_method == "Manual":
            sku_line_edit = self.create_sku_line_edit(sku, match)
            sku_row.addWidget(sku_line_edit)

            edit_sku_button = QPushButton("Edit SKU")
            edit_sku_button.clicked.connect(sku_line_edit.setFocus)
            edit_sku_button.setStyleSheet("""
                QPushButton {
                    padding: 3.5px;
                    margin-left: 5px;
                }
            """)
            sku_row.addWidget(edit_sku_button)

            sku_row.addStretch()
        else:
            sku_label = QLabel(f"{sku}")
            sku_row.addWidget(sku_label, 1)
        

        match_method_label = QLabel(f"Matcher Method: {match_method}")

        for label in [product_label, score_label, match_method_label]:
            # allow HTML highlighting
            label.setTextFormat(Qt.RichText)

            label.setTextInteractionFlags(
                Qt.TextSelectableByMouse |
                Qt.TextSelectableByKeyboard
            )

        info_layout.addWidget(product_label)
        info_layout.addWidget(score_label)
        info_layout.addLayout(sku_row)
        info_layout.addWidget(match_method_label)

        return info_layout


    def create_sku_line_edit(self, sku, product):
        sku_line_edit = QLineEdit(f"{sku}")
        sku_line_edit.setFrame(False)

        sku_line_edit.product = product

        sku_line_edit.returnPressed.connect(sku_line_edit.clearFocus)

        sku_line_edit.editingFinished.connect(self.update_sku)

        def resize_sku(line_edit):
            width = line_edit.fontMetrics().horizontalAdvance(line_edit.text()) + 12
            line_edit.setFixedWidth(width)

        sku_line_edit.textChanged.connect(
            lambda _: resize_sku(sku_line_edit)
        )

        QTimer.singleShot(0, lambda: resize_sku(sku_line_edit))
        # sku_line_edit.textChanged.connect(
        #     lambda text: sku_line_edit.setFixedWidth(
        #         sku_line_edit.fontMetrics().horizontalAdvance(text) + padding
        #     )
        # )

        return sku_line_edit


    def update_sku(self):
        sku_line_edit = self.sender()

        sku_line_edit.product["sku"] = normalize_for_matching(sku_line_edit.text())
    

    # ============================================================
    # MANUAL SEARCH
    # ============================================================

    def search_products(self):

        keyword = (
            self.keyword_edit.text()
        )


        column = (
            self.column_dropdown.currentText()
        )

        if not keyword:
            return


        self.filter_edit.clear()


        self.backend.search_products(
            keyword,
            column
        )


        self.populate_search_results()
    

    def filter_search_results(self):

        if not self.backend.get_product_keyword():
            return

        keyword = (
            self.filter_edit.text()
        )

        self.backend.filter_search_results(
            keyword,
        )

        self.populate_search_results()
    

    def focus_filter(self):
        """
        Pressing Ctrl+F allows user to filter search results
        """
        self.keyword_edit.setFocus()
        self.keyword_edit.selectAll()



    def update_search_labels(self, keyword):
        # Update page label
        current_page = self.backend.get_current_search_page()
        total_pages = self.backend.get_num_search_pages()

        self.page_label.setText(
            f"Page {current_page} / {total_pages}"
        )

        # Update search status label
        total_products = self.backend.get_num_search_results()
        start, end = self.backend.get_current_search_result_indexes()

        if total_products > 0:
            start += 1

        max_keyword_length = 19 - 2
        if len(keyword) > max_keyword_length:
            keyword = keyword[:max_keyword_length] + "..."
        
        self.search_status_label.setText(
            f"Showing {start}-{end} of {total_products} products for \"{keyword}\""
        )


    def add_manual_products(self):

        selected = []


        for checkbox in self.search_checkboxes:


            if checkbox.isChecked():

                selected.append(
                    checkbox.product
                )


        self.backend.add_manual_products(
            selected
        )


        self.log_box.append(
            f"Added {len(selected)} manual products."
        )

        self.populate_auto_matches()




    # ============================================================
    # ANNOTATION
    # ============================================================

    def save_annotation(self):

        self.backend.save_annotation()


        self.log_box.append(
            "Annotation saved."
        )


        self.next_sentence()


        self.update_status()



    def clear_selection(self):

        self.backend.clear_current_selection()


        for checkbox in self.auto_checkboxes:

            checkbox.setChecked(
                False
            )



    # ============================================================
    # AUTO MATCHER THREAD
    # ============================================================

    def run_auto_matcher(self):

        self.run_matcher_button.setEnabled(
            False
        )


        self.set_annotation_enabled(
            False
        )


        self.progress_bar.setRange(
            0,
            0
        )


        self.thread = QThread()


        self.worker = MatcherWorker(
            self.backend
        )


        self.worker.moveToThread(
            self.thread
        )


        self.thread.started.connect(
            self.worker.run
        )


        self.worker.message.connect(
            self.log_box.append
        )


        self.worker.finished.connect(
            self.matcher_finished
        )


        self.worker.error.connect(
            self.matcher_error
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



    def matcher_finished(self):

        self.progress_bar.setRange(
            0,
            100
        )


        self.progress_bar.setValue(
            100
        )


        self.run_matcher_button.setEnabled(
            True
        )


        self.set_annotation_enabled(
            True
        )


        self.refresh_sentence()



    def matcher_error(
        self,
        message
    ):


        self.progress_bar.setRange(
            0,
            100
        )


        self.progress_bar.setValue(
            0
        )


        self.run_matcher_button.setEnabled(
            True
        )


        self.set_annotation_enabled(
            True
        )


        self.log_box.append(
            f"Error: {message}"
        )



    # ============================================================
    # UI ENABLE / DISABLE
    # ============================================================

    def set_annotation_enabled(
        self,
        enabled
    ):


        self.previous_button.setEnabled(
            enabled
        )


        self.next_button.setEnabled(
            enabled
        )


        self.search_sentence_button.setEnabled(
            enabled
        )


        self.save_button.setEnabled(
            enabled
        )


        self.clear_button.setEnabled(
            enabled
        )


        self.keyword_edit.setEnabled(
            enabled
        )


        self.column_dropdown.setEnabled(
            enabled
        )


        self.search_button.setEnabled(
            enabled
        )


        self.add_products_button.setEnabled(
            enabled
        )



    # ============================================================
    # CLEANUP
    # ============================================================

    def thread_deleted(self):
        self.thread = None

    def closeEvent(
        self,
        event
    ):


        if self.thread:

            if self.thread.isRunning():

                self.thread.quit()

                self.thread.wait()


        event.accept()



    def closeEvent(self, event):
                
        self.closed.emit()

        event.accept()


# ============================================================
# Pop Up when "Search Sentence" is pressed
# ============================================================

class GoToSentenceDialog(QDialog):

    def __init__(self, parent=None, max_sentences = 0):
        super().__init__(parent)

        self.setWindowTitle("Go to Sentence")

        self.resize(250, 150)

        font = QFont()
        font.setPointSize(11)
        self.setFont(font)

        self.sentence_edit = QLineEdit()
        self.sentence_edit.setPlaceholderText("Sentence number")

        self.go_button = QPushButton("Go")
        self.cancel_button = QPushButton("Cancel")


        self.first_unannotated_button = QPushButton("First Unannotated")
        self.next_unannotated_button = QPushButton("Next Unannotated")
        self.last_annotated_button = QPushButton("Last Annotated")
        
        self.cancel_button.clicked.connect(self.reject)
        # self.sentence_edit.returnPressed.connect(self.accept)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Jump to sentence:"))
        layout.addWidget(self.sentence_edit)
        # layout.addWidget(self.next_button)

        buttons = QHBoxLayout()
        buttons.addWidget(self.go_button)
        buttons.addWidget(self.cancel_button)
        

        layout.addLayout(buttons)

        layout.addWidget(self.first_unannotated_button)
        layout.addWidget(self.next_unannotated_button)
        layout.addWidget(self.last_annotated_button)

