import csv
import json
from matching.product_map import build_product_map
from matching.sku_matcher import find_sku
from matching.mention_extractor import extract_ollama


def format_list_csv(list, delimiter = "|"):
    return delimiter.join(list)


def run_pipeline(manufacturer: str, sentence_corpus_path: str, product_map_path: str, output_csv_path: str):
    product_map = build_product_map(product_map_path)
    print("Built product map")

    results = []
    
    sentences_processed = 0

    with open(sentence_corpus_path, "r", encoding="utf-8") as f:

        # sentence_index = 0

        for line in f:
            record = json.loads(line)
            sentence = record.get("sentence", "")
            
            skus = find_sku(sentence=sentence, skus=product_map, manufacturer=manufacturer)

            result = record.copy()
            # result["idx"] = sentence_index
            # sentence_index += 1

            if not skus:
                results.append(result)
    
    print(f"Got {len(results)} sentences without known SKUs")

    for result in results:
        sentence = result.get("sentence", "")
        products = extract_ollama(sentence)

        if isinstance(products, list):
            result["product_name"] = format_list_csv(products)
        else:
            result["product_name"] = products

        sentences_processed += 1
        
        print(f"Extracted: {products}")
        print(f"Processed sentence without SKU: {sentence}")
        print(f"Number of sentences processed: {sentences_processed}")
        print("-"*60)



    with open(output_csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)

        writer.writerow([
            "manufacturer",
            "product_name",
            "url",
            "sentence",
        ])

        check_product_names = {}

        # for r in results:

        for r in results:
            id = r.get("pmcid").replace("PMC","")
            products = r.get("product_name","")
            sentence = r.get("sentence")

            writer.writerow([
                manufacturer,
                products,
                f"https://europepmc.org/article/PMC/{id}",
                sentence,
            ])


if __name__ == "__main__":
    manufacturer = "GeneCopoeia"
    sentence_corpus_path = "tests/data/genecopoeia_sentences.jsonl"
    product_map_path = "data/raw_products"
    output_csv_path = "tests/data/matcher_results_without_sku.csv"

    run_pipeline(manufacturer=manufacturer,
                 sentence_corpus_path=sentence_corpus_path,
                 product_map_path=product_map_path,
                 output_csv_path=output_csv_path)