"""
export_sku_results.py

Backend pipeline for:
    1. Loading product/SKU data
    2. Finding sentences containing manufacturer SKUs
    3. Mapping SKUs back to products
    4. Generating citations
    5. Exporting CSV results

This file contains no UI code.
It can be called from:
    - PySide6
    - command line
    - other pipelines
"""


import csv
import json
import os

from matching.normalization import shorten_product_name
from citation_generator.citation import get_citation
from product_building.product_map import (
    build_product_map,
    build_shortened_sku_map,
)
from matching.sku_matcher import find_sku



def format_list_csv(values, delimiter="|"):
    """
    Converts a list into a CSV-friendly string.

    Example:
        ["A", "B"] -> "A | B"
    """

    return delimiter.join(values)



def run_pipeline(
    manufacturer: str,
    annotations_path: str,
    auto_results_path: str,
    output_csv_path: str,
    progress_callback=None,
):
    """
    Main SKU extraction pipeline.

    Parameters
    ----------
    manufacturer:
        Manufacturer name to search for.

    sentence_corpus_path:
        JSONL sentence corpus.

    product_map_path:
        Directory containing product CSV files.

    output_csv_path:
        Destination CSV.

    progress_callback:
        Optional callback function for UI updates.

        Example:
            progress_callback("Loading products")

        PySide6 connects this to a Signal.
    """


    def progress(message):
        """
        Send progress updates either to UI
        or fallback to terminal.
        """

        if progress_callback:
            progress_callback(message)
        else:
            print(message)


    # -----------------------------
    # Load auto results and annotations
    # -----------------------------

    auto_results = {}
    annotations = {}

    if not os.path.exists(
        auto_results_path
    ):
        progress(
            f"Auto results could not be opened"
        )
        return


    with open(
        auto_results_path,
        "r",
        encoding="utf-8"
    ) as f:

        auto_results = json.load(f)
    

    progress(
        f"Loaded Auto Results"
    )


    if not os.path.exists(
        annotations_path
    ):
        progress(
            f"Annotations could not be opened"
        )
        return


    with open(
        annotations_path,
        "r",
        encoding="utf-8"
    ) as f:

        annotations = json.load(f)
    

    progress(
        f"Loaded Annotations"
    )



    # -----------------------------
    # Group annotations by publication
    # -----------------------------


    results = {}
    
    for index in annotations.keys():

        record = auto_results.get(index).copy()
        annotation = annotations.get(index)


        pmcid = record.get("pmcid")


        if pmcid not in results:
            results[pmcid] = record
            results[pmcid]["sku"] = []
            results[pmcid]["product_name"] = []
            results[pmcid]["sentences"] = []


        for entry in annotation:
            results[pmcid]["sku"].append(entry.get("sku"))
            results[pmcid]["product_name"].append(entry.get("product_name"))

        results[pmcid]["sentences"].append(record.get("sentence"))
    

    progress(
        f"Grouped Annotations By Publication"
    )


    # -----------------------------
    # Group products if they have similar shortened product name
    # -----------------------------


    for record in results.values():
        skus = record.get("sku")
        products = record.get("product_name")

        group_by_short = {}

        for i in range(len(skus)):
            sku = skus[i]
            product = products[i]

            shortened_product = shorten_product_name(product)

            if shortened_product not in group_by_short:
                group_by_short[shortened_product] = {
                    "sku": [],
                    "product_name": product,
                }
            
            group_by_short[shortened_product]["sku"].append(sku)
        
        
        condensed_skus = []
        condensed_products = []

        for group in group_by_short.values():

            condensed_skus.append(
                "/".join(sorted(group.get("sku")))
            )

            condensed_products.append(group.get("product_name"))

        record["sku"] = condensed_skus
        record["product_name"] = condensed_products


    progress(
        f"Condensed Annotations by Shortened Product Name"
    )


    # -----------------------------
    # Export CSV
    # -----------------------------

    with open(
        output_csv_path,
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as f:


        writer = csv.writer(f)


        writer.writerow(
            [
                "manufacturer",
                "sku",
                "product_name",
                "citation",
                "pmcid",
                "url",
                "sentence",
            ]
        )

        shortened_products = {}

        num_results = 0

        for pmcid, record in results.items():

            skus = record.get(
                "sku",
                []
            )

            if not skus:
                continue

            num_results += 1


            # Remove PMC prefix
            pmcid = record["pmcid"]

            article_id = (
                pmcid
                .replace("PMC", "")
            )

            products = record.get(
                "product_name",
                []
            )

            citation = get_citation(
                record,
                skus,
                products,
            )

            sentences = record.get(
                "sentences",
                []
            )

            # Debug shortened names

            for product in products:

                shortened_products[product] = (
                    shorten_product_name(product)
                )

            writer.writerow(
                [
                    manufacturer,
                    format_list_csv(skus),
                    format_list_csv(products),
                    citation,
                    pmcid,
                    f"https://europepmc.org/article/PMC/{article_id}",
                    " ".join(sentences),
                ]
            )


    progress(
        f"Exported {num_results} citations to {output_csv_path}"
    )


    # Optional debugging output

    # for long_name, short_name in shortened_products.items():

    #     print(
    #         f"Original:  {long_name}"
    #     )

    #     print(
    #         f"Shortened: {short_name}"
    #     )



if __name__ == "__main__":


    run_pipeline(
        manufacturer="GeneCopoeia",
        annotations_path=(
            "annotator/annotations.json"
        ),
        auto_results_path=(
            "annotator/auto_results.json"
        ),
        output_csv_path=(
            "data/europe_pmc/annotator_citations.csv"
        ),
    )