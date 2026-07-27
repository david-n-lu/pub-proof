import csv
import json
from product_building.product_map import build_alias_index, build_product_map
from matching.sku_matcher import find_sku
from matching.legacy.mention_extractor import extract_product_mention


def format_list_csv(list, delimiter = "|"):
    return delimiter.join(list)


def run_pipeline(manufacturer: str, sentence_corpus_path: str, product_map_path: str, output_csv_path: str):
    product_map = build_product_map(product_map_path)
    print("Built product map")

    alias_map = build_alias_index(product_map)
    print("Build alias map")

    results = []
    

    with open(sentence_corpus_path, "r", encoding="utf-8") as f:

        for line in f:
            record = json.loads(line)
            sentence = record.get("sentence", "")
            
            skus = find_sku(sentence=sentence, skus=product_map, manufacturer=manufacturer)

            result = record.copy()

            if not skus:
                results.append(result)
    
    print(f"Got {len(results)} sentences without known SKUs")


    sentences_processed = 0

    top_n = 3

    for result in results:
        sentence = result.get("sentence", "")
        statistics = extract_product_mention(sentence, alias_map, manufacturer=manufacturer)

        # result["statistics"] = statistics[:top_n]
        result["statistics"] = {}
        top_statistics = result["statistics"]
        
        for sku, statistic in dict(list(statistics.items())[:top_n]).items():
            statistic_copy = [s.copy() for s in statistic]
            top_statistics[sku] = statistic_copy

        sentences_processed += 1
        
        # print(f"Extracted: {top_statistics}")
        # print(f"Processed sentence without SKU: {sentence}")
        # print(f"Number of sentences processed: {sentences_processed}")
        # print("-"*60)

    with open(output_csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)

        writer.writerow([
            "manufacturer",
            "sku"
            "product_name",
            "statistics",
            "url",
            "sentence",
        ])

        check_product_names = {}

        # for r in results:

        for r in results:
            id = r.get("pmcid").replace("PMC","")
            sentence = r.get("sentence")
            statistics = r.get("statistics")

            skus = []
            products = []
            all_words = []

            print(statistics)

            for sku, words in statistics.items():
                skus.append(sku)
                products.append(product_map.get(sku,{}).get("product_name",""))
                all_words.append(str(words))

            separator = " | "
            skus = separator.join(skus)
            products = separator.join(products)
            all_words = separator.join(all_words)

            writer.writerow([
                manufacturer,
                skus,
                products,
                all_words,
                f"https://europepmc.org/article/PMC/{id}",
                sentence,
            ])


if __name__ == "__main__":
    manufacturer = "GeneCopoeia"
    sentence_corpus_path = "tests/data/genecopoeia_sentences.jsonl"
    product_map_path = "data/raw_products"
    output_csv_path = "tests/data/matcher_results_without_sku_statistics.csv"

    run_pipeline(manufacturer=manufacturer,
                 sentence_corpus_path=sentence_corpus_path,
                 product_map_path=product_map_path,
                 output_csv_path=output_csv_path)