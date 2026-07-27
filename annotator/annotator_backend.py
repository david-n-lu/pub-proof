"""
annotator_backend.py

Backend controller for the PySide6 product annotator.

Responsibilities:
- Load product data
- Load sentences
- Load previous annotations
- Run auto matcher
- Provide sentence navigation
- Provide highlighted sentences
- Search products manually
- Track current annotation state
- Save annotations
"""

import os
import json
import pandas as pd
from math import ceil

from pathlib import Path

from matching.normalization import normalize_for_matching
from product_building.product_import import load_product_index_cache
from annotator.manual_search import (
    create_df,
    search,
    search_all,
)
from annotator.highlighter import highlight_sentence
from annotator.auto_matcher import run_pipeline



class AnnotatorBackend:

    def __init__(
        self,
        manufacturer,
        product_map_path,
        product_index_path,
        sentence_path,
        annotation_path,
        auto_match_path,
    ):
        """
        Store paths and initialize empty state.
        """

        self.manufacturer = manufacturer
        self.product_map_path = product_map_path
        self.product_index_path = product_index_path
        self.sentence_path = sentence_path
        self.annotation_path = annotation_path
        self.auto_match_path = auto_match_path

        # Product data
        self.product_map = {}
        self.alias_map = {}
        self.shortened_sku_map = {}

        # Search dataframe
        self.product_df = None

        # Sentences
        self.sentences = []
        self.current_sentence_index = 0

        # Auto matcher results
        self.auto_results = {}

        # Previous annotations
        self.annotations = {}

        # Current annotation session
        self.current_selected_products = []

        # Product search results
        self.product_search_results = pd.DataFrame()
        self.filtered_search_results = self.product_search_results
        self.current_search_page = 0
        self.page_size = 100
        self.product_keyword = ""
        self.column_filter = ""
        self.filter_keyword = ""


    # ============================================================
    # INITIALIZATION
    # ============================================================

    def initialize(self):
        """
        Run heavy initialization.

        Call once when opening annotator.
        """

        self.load_products()

        self.load_sentences()

        self.load_annotations()

        self.load_auto_results()

        print("Annotator initialized")


    def load_products(self):
        """
        Create:

        - product_map
        - alias_map
        - shortened_sku_map
        - product dataframe for searching

        Replace with your existing product_map builder.
        """

        print("Loading products...")

        cache = load_product_index_cache(self.product_index_path)

        self.product_map = cache["product_map"]
        self.alias_map = cache["alias_map"]
        self.shortened_sku_map = cache["shortened_sku_map"]

        self.product_df = create_df(self.product_map_path)


    # ============================================================
    # SENTENCES
    # ============================================================

    def load_sentences(self):
        """
        Load sentence corpus.

        Expected format example:

        [
            {
                "id": 1,
                "text": "...",
                "citation": "..."
            }
        ]
        """

        print("Loading sentences...")


        with open(
            self.sentence_path,
            "r",
            encoding="utf-8"
        ) as f:

            self.sentences = [
                json.loads(line)
                for line in f
            ]


    def get_sentence_count(self):
        return len(self.sentences)


    def get_current_sentence(self):
        """
        Return current sentence object.
        """

        if not self.sentences:
            return None

        return self.sentences[
            self.current_sentence_index
        ]
    
    def get_current_europe_pmc_url(self):
        """
        Return url of current sentence's publication.
        """

        if not self.sentences:
            return None
        
        pmcid = self.sentences[self.current_sentence_index].get("pmcid")

        pmcid = pmcid.replace("PMC", "")

        return f"https://europepmc.org/article/PMC/{pmcid}"

    def get_current_europe_pmc_date(self):
        """
        Return date of current sentence's publication.
        """

        if not self.sentences:
            return None
        
        return self.sentences[self.current_sentence_index].get("date")


    def next_sentence(self):
        """
        Move forward.
        """

        if self.current_sentence_index < self.get_sentence_count() - 1:
            self.current_sentence_index += 1

        return self.get_current_sentence()


    def previous_sentence(self):
        """
        Move backward.
        """

        if self.current_sentence_index > 0:
            self.current_sentence_index -= 1

        return self.get_current_sentence()


    def goto_sentence(
        self,
        index
    ):
        if 0 <= index < self.get_sentence_count():
            self.current_sentence_index = index
        
        return self.get_current_sentence()

    
    def next_unannotated(self):
        for i in range(self.current_sentence_index + 1, self.get_sentence_count()):
            if str(i) not in self.annotations:
                self.goto_sentence(i)
                return True

        return False


    def first_unannotated(self):
        for i in range(0, self.get_sentence_count()):
            if str(i) not in self.annotations:
                self.goto_sentence(i)
                return True

        return False
    

    def last_annotated(self):
        for i in range(self.get_sentence_count() - 1, -1, -1):
            if str(i) in self.annotations:
                self.goto_sentence(i)
                return True

        return False

    
    # ============================================================
    # HIGHLIGHTING
    # ============================================================

    def get_highlighted_sentence(self):
        """
        Generate HTML highlighted sentence.

        Do lazy highlighting here.

        Replace with your highlighter.
        """


        return highlight_sentence(
            sentence = self.get_current_sentence().get("sentence",""), 
            manufacturer = self.manufacturer,
            alias_map = self.alias_map,
            shortened_sku_map = self.shortened_sku_map,
        )


    # ============================================================
    # AUTO MATCHER
    # ============================================================

    def has_auto_results(self):

        return bool(self.auto_results)


    def load_auto_results(self):
        """
        Load existing matcher results.
        """

        if not os.path.exists(
            self.auto_match_path
        ):
            return


        with open(
            self.auto_match_path,
            "r",
            encoding="utf-8"
        ) as f:

            self.auto_results = json.load(f)


    def run_auto_matcher(self):
        """
        Run auto matcher.

        Saves auto matcher results too

        Should eventually be moved into QThread worker.
        """

        print("Running matcher...")


        self.auto_results = run_pipeline(
            manufacturer = self.manufacturer,
            sentences = self.sentences,
            product_map = self.product_map,
            alias_map = self.alias_map,
            shortened_sku_map = self.shortened_sku_map,
        )

        self.auto_results = {
            str(index): result | {"id": str(index)}
            for index, result in enumerate(self.auto_results)
        }

        self.save_auto_results()



    def save_auto_results(self):

        with open(
            self.auto_match_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.auto_results,
                f,
                indent=2
            )


    def get_current_auto_matches(self):
        """
        Return matcher suggestions
        for current sentence.
        """

        sentence_id = self.get_sentence_id()

        current_auto_match = self.auto_results.get(
            str(sentence_id),
        )

        if current_auto_match:
            return current_auto_match.get("matches")

        return []
    

    def get_current_annotations(self):
        """
        Return annotations
        for current sentence.
        """

        sentence_id = self.get_sentence_id()

        current_annotations = self.annotations.get(
            str(sentence_id),
            [],
        )
        
        return current_annotations


    # ============================================================
    # ANNOTATIONS
    # ============================================================

    def load_annotations(self):

        if not os.path.exists(
            self.annotation_path
        ):
            self.annotations = {}
            return

        with open(
            self.annotation_path,
            "r",
            encoding="utf-8"
        ) as f:
            self.annotations = json.load(f)


    def get_sentence_id(self):

        return str(self.current_sentence_index)


    def get_current_selected_products(self):
        """
        Add product to current selection.
        """

        return self.current_selected_products


    def select_product(self, product, insert_at_top = False):
        """
        Add product to current selection.
        """

        if product not in self.current_selected_products:
            
            if insert_at_top:
                self.current_selected_products.insert(
                    0,
                    product
                )

            else:
                self.current_selected_products.append(
                    product
                )


    def remove_product(self, product):

        if product in self.current_selected_products:

            self.current_selected_products.remove(
                product
            )


    def clear_current_selection(self):

        self.current_selected_products = []
    

    def current_has_annotation(self):
        return self.get_sentence_id() in self.annotations


    def load_current_selection(self):
        """
        Load saved annotation for current sentence.
        """

        sentence_id = self.get_sentence_id()

        self.current_selected_products = (
            self.annotations.get(sentence_id, []).copy()
        )


    def save_annotation(self):
        """
        Save current sentence annotation.
        """

        sentence_id = self.get_sentence_id()


        self.annotations[sentence_id] = (
            self.current_selected_products
        )


        self.write_annotations()


    def write_annotations(self):
        """
        Save annotations dictionary to JSON.
        """

        with open(
            self.annotation_path,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                self.annotations,
                f,
                indent=2
            )
    

    def get_annotation_count(self):
        """
        Return number of annotated sentences/results.
        """
        return len(self.annotations)


    # ============================================================
    # MANUAL PRODUCT SEARCH
    # ============================================================

    def get_product_keyword(self):
        return self.product_keyword
    
    def get_filter_keyword(self):
        return self.filter_keyword


    def get_search_columns(self):
        """
        Return available columns for product search dropdown.

        Used by UI to populate the search column combo box.
        """

        if self.product_df is None:
            return []

        return ["All"] + list(self.product_df.columns)


    def search_products(
        self,
        keyword,
        column,
    ):
        """
        Search product dataframe.

        Returns:
            list[dict]: Matching products
        """

        if keyword == self.product_keyword and column == self.column_filter:
            self.current_search_page = 0
            return

        self.product_keyword = keyword
        self.column_filter = column
        self.filter_keyword = ""

        if self.product_df is None:
            self.product_search_results = pd.DataFrame()
            return

        if column == "All":
            self.product_search_results = search_all(
                self.product_df,
                keyword,
            )
        else:
            self.product_search_results = search(
                self.product_df,
                keyword,
                column,
            )
        
        self.filtered_search_results = self.product_search_results

        self.current_search_page = 0

    
    def filter_search_results(
        self,
        keyword,
    ):  
        if keyword == "":

            self.filtered_search_results = self.product_search_results

            self.filter_keyword = ""

        elif keyword != self.filter_keyword:

            self.filtered_search_results = search_all(
                self.product_search_results,
                keyword,
            )

            self.filter_keyword = keyword

        self.current_search_page = 0
        
    
    def get_current_search_results(self):
        start = self.current_search_page * self.page_size
        end = start + self.page_size

        results = self.filtered_search_results.iloc[start:end]

        return results.to_dict(
            orient="records"
        )

    def next_search_page(self):
        if (self.current_search_page + 1) * self.page_size < self.get_num_search_results():
            self.current_search_page += 1
    
    def previous_search_page(self):
        if self.current_search_page > 0:
            self.current_search_page -= 1
    
    def get_num_search_results(self):
        return len(self.filtered_search_results)
    
    def get_current_search_page(self):
        
        return self.current_search_page + 1
    
    def get_num_search_pages(self):
        
        return max(
            1,
            ceil(
                self.get_num_search_results() / self.page_size
            )
        )

    def get_current_search_result_indexes(self):
        start = max(0, self.current_search_page * self.page_size)
        end = min(self.get_num_search_results(), start + self.page_size)

        return start, end


    def add_manual_products(
        self,
        selected_products
    ):
        """
        Add manually selected products
        to current annotation.
        """

        manual_matches = []

        for product in selected_products:

            sku = product["Part ID"]

            sku = normalize_for_matching(sku)

            product_info = self.product_map.get(sku)

            if product_info:
                product_name = product_info["product_name"]
            else:
                product_name = product.get("Product Name")

            manual_matches.append(
                {
                    "sku": sku,
                    "product_name": product_name,
                    "score": 1.0,
                    "type": "manual"
                }
            )

        for match in manual_matches:
            self.select_product(match, insert_at_top=True)

