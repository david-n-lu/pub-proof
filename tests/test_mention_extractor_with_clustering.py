import csv
import json
from math import prod
from matching.product_map import build_alias_index, build_product_map
from matching.sku_matcher import find_sku
from matching.mention_extractor import extract_product_mention, get_phrases, extract_best_product_mention, get_best_phrases, score_phrase


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

    for result in results:
        sentence = result.get("sentence", "")

        # phrase_data = get_phrases(sentence, alias_map)

        phrases = get_best_phrases(sentence, alias_map)
        
        skus = []
        products = []
        scores = []
        corresponding_phrases = []
        for phrase in phrases:
            phrase_skus = extract_best_product_mention(phrase, alias_map, n = 2)
            skus.extend(phrase_skus)

            phrase_products = [product_map.get(sku,{}).get("product_name","") for sku in phrase_skus]
            products.extend(phrase_products)

            for product in phrase_products:
                scores.append(str(score_phrase(phrase, product)))
                corresponding_phrases.append(phrase)
        
        top_n = 1
        # get indexes of top_n scores
        top_score_indexes = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_n]

        skus = [skus[i] for i in top_score_indexes]
        products = [products[i] for i in top_score_indexes]
        scores = [scores[i] for i in top_score_indexes]
        corresponding_phrases = [corresponding_phrases[i] for i in top_score_indexes]

        separator = " | "
        result["sku"] = separator.join(skus)
        result["product_name"] = separator.join(products)
        result["score"] = separator.join(scores)
        result["phrase"] = separator.join(corresponding_phrases)

        sentences_processed += 1
        
        print(f"Processed sentence without SKU: {sentence}")
        # print(f"Number of sentences processed: {sentences_processed}")
        # print("-"*60)

    with open(output_csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)

        writer.writerow([
            "manufacturer",
            "sku",
            "product_name",
            "score"
            "phrase",
            "url",
            "sentence",
        ])

        for r in results:
            id = r.get("pmcid").replace("PMC","")
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


    # sentence = "qRT‒PCR assays were conducted on a CFX96 Real-Time PCR System (Bio-Rad, USA) using BlazeTaq™ SYBR® Green qPCR Mix 2.0 (GeneCopoeia)."
    # test_sentence(manufacturer = manufacturer, sentence = sentence, product_map_path = product_map_path)