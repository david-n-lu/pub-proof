"""
export_ollama_results.py

Filters ollama phrase results that don't have a known SKU or have a "YES" label in the trademark results

Exports SKU obtained from ollama phrase results
"""

import csv
import json
from operator import index
from matching.product_map import build_alias_map, build_product_map, build_shortened_sku_map
from matching.mention_extractor import get_keyword_indexes, get_best_phrases, get_product_data_from_phrase
from matching.normalization import normalize_for_matching, shorten_product_name
from matching.sku_matcher import find_sku

trademark_names = {
    "OmicsArray™",
    "Luc-Pair™",
    "EndoFectin™",
    "CRISPR-Fectin™",
    "Fast-Fusion™",
    "CoolCutter™",
    "ExoSure™",
    "ExoCt™",
    "SuperCut™",
    "IndelCheck™",
    "Smart-Join™",
    "Genome-TALER™",
    "GeneHero™",
    "VividFISH™",
    "Lenti-Pac™",
    "Lentifect™",
    "AAVPrime™",
    "EZRecombinase™",
    "CytoCt™",
    "All-in-One™",
    "SureScript™",
    "BlazeTaq™",
    "ExProfile™",
    "miProfile™",
    "miTarget™",
    "OmicsLink™",
    "GLuc-ON™",
    "MiExpress™",
    "OmicsLink™",
    "RNAzol®",
    "AccelerRT®",
    "UltraHiPF®",
    "NileHiFi®",
}

trademark_names_norm = {normalize_for_matching(name) for name in trademark_names}

def format_list_csv(list, delimiter = "|"):
    return delimiter.join(list)


def run_pipeline(manufacturer: str, 
                 ollama_results_path: str,
                 sku_results_path: str,
                 trademark_results_path : str,
                 product_map_path: str, 
                 output_csv_path: str):
    product_map = build_product_map(product_map_path)
    print("Built product map")

    alias_map = build_alias_map(product_map)
    print("Build alias map")

    shortened_sku_map = build_shortened_sku_map(product_map)
    print("Built shortened SKU map")

    # exclude publications with SKU or "YES" trademark results
    exclude = set()
    identifier = "url"
    with open(sku_results_path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            exclude.add(row.get(identifier))
    with open(trademark_results_path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            exclude.add(row.get(identifier))

    results = []

    with open(ollama_results_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            if row.get(identifier) not in exclude:
                result = {
                    "phrase": row.get("product_name"),
                    "url" : row.get("url"),
                    "sentence" : row.get("sentence"),
                }
                results.append(result)
    
    print(f"Got {len(results)} sentences without known SKUs and without trademark name")


    phrase_delimiter = "|"  # input separator
    separator = " | "       # output separator

    sentences_processed = 0

    for result in results:
        phrases = result.get("phrase").split(phrase_delimiter)

        # print(f"phrases: {phrases}")
        # print(f"sentence: {result["sentence"]}")

        skus = []
        products = []
        scores = []

        for phrase in phrases:
            phrase_norm = normalize_for_matching(phrase)

            curr_skus, curr_products, curr_scores = get_product_data_from_phrase(phrase_norm, product_map, alias_map, n = 10)

            skus.extend(curr_skus)
            products.extend(curr_products)
            scores.extend(curr_scores)

            
        result["sku"] = json.dumps(skus)
        result["product_name"] = json.dumps(products)
        result["score"] = json.dumps(scores)

        # print(f"skus: {result["sku"]}")
        # print(f"products: {result["product_name"]}")
        # print(f"scores: {result["score"]}")
        

        sentences_processed += 1
        
        # print(f"Processed sentence without SKU: {sentence}")
        print(f"Number of sentences processed: {sentences_processed}")
        print("-"*60)


    with open(output_csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)

        writer.writerow([
            "manufacturer",
            "sku",
            "product_name",
            "score",
            "phrase",
            "url",
            "sentence",
        ])

        for r in results:
            url = r.get("url")
            sentence = r.get("sentence")
            sku = r.get("sku")
            product_name = r.get("product_name")
            score = r.get("score")
            phrase = r.get("phrase")

            writer.writerow([
                manufacturer,
                sku,
                product_name,
                score,
                phrase,
                url,
                sentence,
            ])


if __name__ == "__main__":
    manufacturer = "GeneCopoeia"
    ollama_results_path = "data/europe_pmc/matcher_results_without_sku_ollama.csv"
    sku_results_path = "data/europe_pmc/matcher_results_with_sku.csv"
    trademark_results_path = "data/europe_pmc/matcher_results_with_trademark_annotated_07-02-2026_citation_07-06-2026.csv"
    product_map_path = "data/raw_products"
    output_csv_path = "data/europe_pmc/ollama_results.csv"

    run_pipeline(manufacturer=manufacturer,
                 ollama_results_path=ollama_results_path,
                 sku_results_path=sku_results_path,
                 trademark_results_path=trademark_results_path,
                 product_map_path=product_map_path,
                 output_csv_path=output_csv_path)