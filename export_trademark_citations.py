"""
export_trademark_citations.py

Takes annotated results from export_trademark_results.py and generates a citation for each sentence

Only generates citations marked "YES" in the validation column of the results CSV
"""

import token

import pandas as pd
from matching.citation import get_citation_from_url, get_citation
from matching.normalization import shorten_product_name
import json


def get_citation_info(records_path: str, records: dict):
    """
    For each pmcid in records, searches for the record in records_path and 
    adds relevant citation info to the records dictionary

    records_path: string of .jsonl path of manufacturer publications
    records: dictionary mapping pmcid's to trademark results for that publication
    """

    with open(records_path, "r", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)

            pmcid = r.get("pmcid")

            if pmcid not in records:
                continue

            citation_keys = ["doi", "title", "journal_iso", "authors", "year"]
            citation_record = {k: r[k] for k in citation_keys if k in r}

            records[pmcid]["citation_record"] = citation_record


def run_pipeline(input_csv_path: str, records_path: str):
    records = {} # pmcid: record

    df = pd.read_csv(input_csv_path, encoding='utf-8-sig', low_memory=False)

    for _, row in df.iterrows():
        if row.get("validation", "") != "YES":
            continue

        url = row.get("url", "")
        pmcid = "PMC" + url.rstrip("/").split("/")[-1]

        if pmcid not in records:
            records[pmcid] = {
                "manufacturer": row.get("manufacturer", ""),
                "sku": [],
                "product_name": [],
                "score": [],
                "phrase": [],
                "url": row.get("url", ""),
                "sentence": [],
                "token_indexes": [],
                "validation": "YES",
            }

        skus = json.loads(row.get("sku", []))
        products = json.loads(row.get("product_name", []))
        scores = json.loads(row.get("score", []))
        phrase = row.get("phrase", "")
        sentence = row.get("sentence", "")
        token_indexes = json.loads(row.get("token_indexes", {}))

        records[pmcid]["sku"].extend(skus)
        records[pmcid]["product_name"].extend(products)
        records[pmcid]["score"].extend(scores)
        records[pmcid]["phrase"].append(phrase)
        records[pmcid]["sentence"].append(sentence)
        records[pmcid]["token_indexes"].append(token_indexes)
    

    print(f"Got {len(records)} publications")

    get_citation_info(records_path, records)

    print(f"Got citation records")

    unique_product_counts = set()
    
    count = 0
    for pmcid, record in records.items():
        products = record.get("product_name", [])
        skus = record.get("sku", [])

        shortened_products = [shorten_product_name(p) for p in products]

        # All-in-One™ miRNA qRT-PCR Detection Kit 2.0 --> QP015, QP016
        unique_product_map = {}
        for unique in list(dict.fromkeys(shortened_products)):
            unique_product_map[unique] = []

        original_product_map = {}
        for i in range(len(skus)):
            unique_product = shortened_products[i]
            unique_product_map[unique_product].append(skus[i])

            if unique_product not in original_product_map:
                original_product_map[unique_product] = products[i]

        # "QP015/QP016", "QP056/QP057"
        # condensed_products = list(unique_product_map.keys())
        condensed_products = list(original_product_map.values())
        condensed_skus = ["/".join(sorted(list(sku_list))) for sku_list in unique_product_map.values()]

        unique_product_counts.add(len(condensed_products))

        if len(condensed_products) >= 3:
            print(record.get("sentence"))
            print(record.get("phrase"))
            print(condensed_products)
            print(condensed_skus)
            print("")

        # url = record.get("url", "")
        # citation = get_citation_from_url(url, condensed_skus, condensed_products)
        citation_record = record.get("citation_record", {})
        citation = get_citation(citation_record, condensed_skus, condensed_products)

        record["citation"] = citation

        count += 1
        # print(f"Processed publication {count}")
        # print(condensed_products)
        # print(condensed_skus)
        # print(citation)
        # print("-" * 60)

    print(f"Unique Product Counts: {unique_product_counts}")

    df = pd.DataFrame.from_dict(records, orient="index")
    df.to_csv(
        f"{input_csv_path.replace(".csv", "")}_citation.csv",
        index=False,
        encoding="utf-8-sig",
    )


if __name__ == "__main__":
    input_csv_path = "data/europe_pmc/matcher_results_with_trademark_annotated_07-02-2026.csv"
    records_path = "data/europe_pmc/genecopoeia.jsonl"

    run_pipeline(input_csv_path, records_path)