"""
export_sku_results.py

Filters sentences from corpus that have known manufacturer skus

Exports citation results
"""


import csv
from matching.legacy.split_sentences_by_sku import get_sentences_with_sku
from matching.normalization import shorten_product_name
from citation_generator.citation import get_citation
from product_building.product_map import build_product_map, build_shortened_sku_map
from matching.sku_matcher import find_sku


def format_list_csv(list, delimiter = "|"):
    return delimiter.join(list)


def run_pipeline(manufacturer: str, sentence_corpus_path: str, product_map_path: str, output_csv_path: str):
    product_map = build_product_map(product_map_path)
    print("Built product map")

    shortened_sku_map = build_shortened_sku_map(product_map)
    print("Built shortened SKU map")

    records = get_sentences_with_sku(sentence_corpus_path, shortened_sku_map, manufacturer=manufacturer)

    results = {} # pmcid: record

    for r in records:
        pmcid = r.get("pmcid") # always exists because of manufacturer_corpus.py filtering
        sentence = r.get("sentence", "")

        # shortened skus
        skus = find_sku(sentence=sentence, skus=shortened_sku_map, manufacturer=manufacturer)

        # original skus
        # get first edition if shortened sku wasn't specific enough
        for s in skus:
            shortened_sku = s.get("sku")
            
            original_skus = shortened_sku_map.get(shortened_sku)
            original_sku = next(iter(original_skus))

            if original_sku:
                s["original_sku"] = original_sku
        
        result = r.copy()

        # create publication entry
        if not pmcid in results:
            results[pmcid] = result
            results[pmcid]["product_name"] = []
            results[pmcid]["sku"] = []
            results[pmcid]["sentences"] = []
        
        for sku in skus:
            shortened_sku = sku.get("sku")
            sentence_sku = sku.get("sentence_sku")
            original_sku = sku.get("original_sku")

            if not sentence_sku or sentence_sku in results[pmcid]["sku"]:
                continue
            
            product = product_map.get(original_sku).get("product_name")

            results[pmcid]["product_name"].append(product)
            results[pmcid]["sku"].append(sentence_sku)
        results[pmcid]["sentences"].append(sentence)

    print(f"Processed {len(records)} sentences")


    with open(output_csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)

        writer.writerow([
            "manufacturer",
            "sku",
            "product_name",
            "citation",
            "url",
            "sentence",
        ])

        check_product_names = {}

        for pmcid, r in results.items():
            id = r.get("pmcid").replace("PMC","")
            skus = r.get("sku","")
            products = r.get("product_name","")
            citation = get_citation(r, skus, products)
            sentences = r.get("sentences")

            for p in products:
                check_product_names[p] = shorten_product_name(p)

            writer.writerow([
                manufacturer,
                format_list_csv(skus),
                format_list_csv(products),
                citation,
                f"https://europepmc.org/article/PMC/{id}",
                " ".join(sentences),
            ])
        
        for long, short in check_product_names.items():
            print(f"Original:  {long}")
            print(f"Shortened: {short}")


if __name__ == "__main__":
    manufacturer = "GeneCopoeia"
    sentence_corpus_path = "data/europe_pmc/genecopoeia_sentences.jsonl"
    product_map_path = "data/raw_products"
    output_csv_path = "data/europe_pmc/matcher_results_with_sku.csv"

    run_pipeline(manufacturer=manufacturer,
                 sentence_corpus_path=sentence_corpus_path,
                 product_map_path=product_map_path,
                 output_csv_path=output_csv_path)