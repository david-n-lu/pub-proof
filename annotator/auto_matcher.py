"""
auto_matcher.py

Finds product mentions in sentence and returns the best ones
- Checks for SKUs
- Compares sentence phrases to products if no SKU present

Scores product mentions
"""

import json
from product_building.product_map import (
    build_product_map,
    build_alias_map,
    build_shortened_sku_map,
)
from matching.matcher import match



def run_pipeline(
    manufacturer,
    sentences,
    product_map,
    alias_map,
    shortened_sku_map,
):
    """
    Runs the auto matcher pipeline.

    Args:
        manufacturer (str): Manufacturer name.
        sentences (list): List of sentence dictionaries.
        product_map (dict): SKU/product mapping.
        alias_map (dict): Alias lookup mapping.
        shortened_sku_map (dict): Shortened SKU lookup mapping.
        output_path (str): CSV output path.

    Returns:
        list: Auto matcher results.
    """

    results = auto_match_sentences(
        manufacturer,
        sentences,
        product_map,
        alias_map,
        shortened_sku_map,
    )

    return results


def auto_match_sentences(
    manufacturer,
    sentences,
    product_map,
    alias_map,
    shortened_sku_map,
):
    results = []

    for count, record in enumerate(sentences, start=1):

        sentence = record.get("sentence", "")

        matches = match(
            manufacturer,
            sentence,
            product_map,
            alias_map,
            shortened_sku_map,
        )

        for m in matches:
            sku = m.get("original_sku", m.get("sku"))

            product_data = product_map.get(sku, {})

            m["product_name"] = product_data.get("product_name")

        record["matches"] = matches

        results.append(record)

        print(f"Processed sentence {count}")

    return results



def export_results(
    results,
    manufacturer,
    output_csv_path,
):
    import csv

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
                "matches",
                "pmcid",
                "url",
                "sentence",
                "validation",
            ]
        )

        for result in results:

            pmcid = result.get("pmcid", "")

            article_id = (
                pmcid.replace("PMC", "")
                if pmcid
                else ""
            )

            writer.writerow(
                [
                    manufacturer,
                    result.get("matches", []),
                    pmcid,
                    (
                        f"https://europepmc.org/article/PMC/{article_id}"
                        if article_id
                        else ""
                    ),
                    result.get("sentence", ""),
                    "",
                ]
            )

    print(f"Exported results to {output_csv_path}")



if __name__ == "__main__":

    product_map = build_product_map(
        "data/raw_products"
    )

    alias_map = build_alias_map(
        product_map
    )

    shortened_sku_map = build_shortened_sku_map(
        product_map
    )

    with open(
        "data/europe_pmc/genecopoeia_sentences.jsonl",
        encoding="utf-8"
    ) as f:
        sentences = [
            json.loads(line)
            for line in f
        ]

    results = run_pipeline(
        "GeneCopoeia",
        sentences,
        product_map,
        alias_map,
        shortened_sku_map,
    )

    export_results(
        results,
        "GeneCopoeia",
        "data/europe_pmc/auto_matcher_results.csv"
    )