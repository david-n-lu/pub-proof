"""
Test for finding products using sku_matcher.py and mention_extractor.py
"""

import csv
import json
from matching.product_map import build_product_map
from matching.sku_matcher import find_sku
from matching.mention_extractor import extract_ollama_batch, extract_product_mention, extract_ollama
from matching.normalization import normalize_for_matching


def format_list_csv(list, delimiter = "|"):
    return delimiter.join(list)


def run_pipeline(manufacturer: str, sentence_corpus_path: str, product_map_path: str, output_csv_path: str):

    product_map = build_product_map(product_map_path)
    print("Built product map")

    product_names = [normalize_for_matching(product["product_name"]) for product in product_map.values()]


    results_with_skus = []
    results_without_skus = []
    
    sentences_processed = 0

    results = []

    with open(sentence_corpus_path, "r", encoding="utf-8") as f:

        sentence_index = 0

        for line in f:
            record = json.loads(line)
            sentence = record.get("sentence", "")
            
            skus = find_sku(sentence=sentence, skus=product_map, manufacturer=manufacturer)

            result = record.copy()
            result["idx"] = sentence_index
            sentence_index += 1

            if skus:
                skus = [s["sku"] for s in skus]
                products = [product_map.get(sku).get("product_name") for sku in skus]

                result["product_name"] = format_list_csv(products)
                result["sku"] = format_list_csv(skus)

                results_with_skus.append(result)

                sentences_processed += 1

                print(f"SKU: {skus}")
                print(f"Processed sentence with SKU: {sentence}")
                print(f"Number of sentences processed: {sentences_processed}")
                print("-"*60)
                continue

            results_without_skus.append(result)


    # for result in results_without_skus:
    #     sentence = result.get("sentence", "")
    #     products = extract_ollama(sentence)

    #     if isinstance(products, list):
    #         result["product_name"] = format_list_csv(products)
    #     else:
    #         result["product_name"] = products

    #     sentences_processed += 1
        
    #     print(f"Extracted: {products}")
    #     print(f"Processed sentence without SKU: {sentence}")
    #     print(f"Number of sentences processed: {sentences_processed}")
    #     print("-"*60)

    batch_size = 30
    for i in range(0, len(results_without_skus), batch_size):
        batch = results_without_skus[i: i + batch_size]
        sentences = []
        for r in batch:
            sentences.append(r.get("sentence", ""))
        
        batch_results = extract_ollama_batch(sentences)

        for r in batch_results:
            idx = r.get("index")
            products = r.get("products")
            skus = r.get("catalog_numbers")

            batch[idx]["product_name"] = format_list_csv(products)
            batch[idx]["sku"] = "AI: " + format_list_csv(skus)

        n = len(batch)
        sentences_processed += n
        print(f"Processed {n} sentences without SKU")
        print("-"*60)


    results = results_with_skus
    results.extend(results_without_skus)
    results = sorted(results, key=lambda x: x["idx"])


    with open(output_csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)

        writer.writerow([
            "manufacturer",
            "sku",
            "product_name",
            "score",
            "url",
            "sentence",
        ])


        for r in results:
            id = r.get("pmcid").replace("PMC","")

            writer.writerow([
                manufacturer,
                r.get("sku",""),
                r.get("product_name"),
                r.get("score"),
                f"https://europepmc.org/article/PMC/{id}",
                r.get("sentence"),
            ])


if __name__ == "__main__":
    manufacturer = "GeneCopoeia"
    sentence_corpus_path = "tests/data/genecopoeia_sentences.jsonl"
    product_map_path = "data/raw_products"
    output_csv_path = "tests/data/matcher_results.csv"

    run_pipeline(manufacturer=manufacturer,
                 sentence_corpus_path=sentence_corpus_path,
                 product_map_path=product_map_path,
                 output_csv_path=output_csv_path)