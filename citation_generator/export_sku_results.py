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

from matching.legacy.split_sentences_by_sku import get_sentences_with_sku
from matching.normalization import shorten_product_name
from citation_generator.citation import get_citation
from matching.sku_matcher import find_sku
from product_building.product_import import load_product_index_cache



def format_list_csv(values, delimiter="|"):
    """
    Converts a list into a CSV-friendly string.

    Example:
        ["A", "B"] -> "A | B"
    """

    return delimiter.join(values)



def run_pipeline(
    manufacturer: str,
    sentence_corpus_path: str,
    product_index_path: str,
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
    # Build product lookup tables
    # -----------------------------

    progress(
        "Retrieving Product Map and Shortened SKU Map"
    )

    cache = load_product_index_cache(product_index_path)

    product_map = cache["product_map"]

    shortened_sku_map = cache["shortened_sku_map"]


    # -----------------------------
    # Find sentences containing SKUs
    # -----------------------------

    progress(
        f"Finding sentences with SKUs"
    )

    records = get_sentences_with_sku(
        sentence_corpus_path,
        shortened_sku_map,
        manufacturer=manufacturer,
    )


    progress(
        f"Found {len(records)} sentences with SKUs"
    )



    # -----------------------------
    # Group results by publication
    #
    # Multiple sentences can come
    # from the same paper.
    # -----------------------------

    results = {}



    for record in records:

        pmcid = record.get(
            "pmcid"
        )

        sentence = record.get(
            "sentence",
            ""
        )


        # Find SKU mentions inside sentence

        sku_matches = find_sku(
            sentence=sentence,
            skus=shortened_sku_map,
            manufacturer=manufacturer,
        )



        # Convert shortened SKU
        # back to original SKU

        for match in sku_matches:

            shortened_sku = match.get(
                "sku"
            )

            original_skus = shortened_sku_map.get(
                shortened_sku,
                []
            )


            if original_skus:

                match["original_sku"] = (
                    next(iter(original_skus))
                )



        # Create publication entry

        if pmcid not in results:

            results[pmcid] = record.copy()

            results[pmcid]["product_name"] = []
            results[pmcid]["sku"] = []
            results[pmcid]["sentences"] = []



        # -----------------------------
        # Add SKU/product associations
        # -----------------------------

        for match in sku_matches:

            sentence_sku = match.get(
                "sentence_sku"
            )

            original_sku = match.get(
                "original_sku"
            )


            # Ignore invalid duplicates

            if (
                not sentence_sku
                or sentence_sku in results[pmcid]["sku"]
            ):
                continue



            product = product_map.get(
                original_sku
            )


            if not product:
                continue



            product_name = product.get(
                "product_name",
                ""
            )


            results[pmcid]["product_name"].append(
                product_name
            )

            results[pmcid]["sku"].append(
                sentence_sku
            )



        results[pmcid]["sentences"].append(
            sentence
        )



    progress(
        f"Processed {len(records)} sentences"
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



        for pmcid, record in results.items():


            # Remove PMC prefix

            pmcid = record["pmcid"]



            article_id = (
                pmcid
                .replace("PMC", "")
            )


            skus = record.get(
                "sku",
                []
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
        f"Exported results to {output_csv_path}"
    )



    # Optional debugging output

    for long_name, short_name in shortened_products.items():

        print(
            f"Original:  {long_name}"
        )

        print(
            f"Shortened: {short_name}"
        )



if __name__ == "__main__":


    run_pipeline(
        manufacturer="GeneCopoeia",
        sentence_corpus_path=(
            "data/europe_pmc/genecopoeia_sentences.jsonl"
        ),
        product_map_path=(
            "data/raw_products"
        ),
        output_csv_path=(
            "data/europe_pmc/matcher_results_with_sku.csv"
        ),
    )