import csv
import json
from matching.product_map import build_product_map
from matching.sku_matcher import find_sku
from matching.mention_extractor import extract_ollama


def format_list_csv(list, delimiter = "|"):
    return delimiter.join(list)


def run_pipeline(manufacturer: str, 
                 sentence_corpus_path: str, 
                 product_map_path: str, 
                 output_csv_path: str, 
                 batch_size: int = 5,
                 start_line: int = 1,
                 clear_output: bool = False):
    product_map = build_product_map(product_map_path)
    print("Built product map")

    results = []

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
    

    n = len(results)
    print(f"Got {n} sentences without known SKUs")


    if clear_output:
        with open(output_csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)

            writer.writerow([
                "manufacturer",
                "product_name",
                "url",
                "sentence",
            ])


    sentences_processed = 0

    for i in range(start_line-1, n, batch_size):
        batch = results[i: i+batch_size]

        for result in batch:
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
        
        with open(output_csv_path, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)

            for r in batch:
                id = r.get("pmcid").replace("PMC","")
                products = r.get("product_name","")
                sentence = r.get("sentence")

                writer.writerow([
                    manufacturer,
                    products,
                    f"https://europepmc.org/article/PMC/{id}",
                    sentence,
                ])
        
        print(f"\nProcessed batch from sentence {i+1} to sentence {min(n, i+batch_size)}\n")


if __name__ == "__main__":
    manufacturer = "GeneCopoeia"
    sentence_corpus_path = "tests/data/genecopoeia_sentences_1000.jsonl"
    product_map_path = "data/raw_products"
    output_csv_path = "tests/data/matcher_results_without_sku_1000.csv"


    run_pipeline(manufacturer=manufacturer,
                 sentence_corpus_path=sentence_corpus_path,
                 product_map_path=product_map_path,
                 output_csv_path=output_csv_path,
                 clear_output=True)

    # start_line = 56

    # run_pipeline(manufacturer=manufacturer,
    #              sentence_corpus_path=sentence_corpus_path,
    #              product_map_path=product_map_path,
    #              output_csv_path=output_csv_path,
    #              start_line=start_line)
    