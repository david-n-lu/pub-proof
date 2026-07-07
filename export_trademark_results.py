"""
export_trademark_results.py

Filters sentences from corpus that have known manufacturer trademark names

Exports citation results
"""


import csv
import json
from operator import index
from matching.split_sentences_by_sku import get_sentences_without_sku
from matching.product_map import build_alias_map, build_product_map, build_shortened_sku_map
from matching.mention_extractor import get_keyword_indexes, get_best_phrases, get_product_data_from_phrase
from matching.normalization import normalize_for_matching, shorten_product_name

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


def run_pipeline(manufacturer: str, sentence_corpus_path: str, product_map_path: str, output_csv_path: str):
    product_map = build_product_map(product_map_path)
    print("Built product map")

    alias_map = build_alias_map(product_map)
    print("Build alias map")

    shortened_sku_map = build_shortened_sku_map(product_map)
    print("Built shortened SKU map")

    records = get_sentences_without_sku(sentence_corpus_path, shortened_sku_map, manufacturer=manufacturer)

    results = []

    for r in records:
        sentence = r.get("sentence", "")
        words = normalize_for_matching(sentence[:-1]).split()

        for word in words:
            if word in trademark_names_norm:
                results.append(r.copy())
                break
    
    print(f"Got {len(results)} sentences without known SKUs but with trademark name")

    sentences_processed = 0

    for result in results:
        sentence = result.get("sentence", "")

        # phrase_data = get_phrases(sentence, alias_map)

        # gets phrases containing words in entire product map
        phrases = get_best_phrases(sentence, alias_map, penalty=4.0, n = None) # preserve phrase order with n = None

        # filter phrases with trademark name
        phrase_indexes = [i for i, phrase in enumerate(phrases) if any(trademark in phrase for trademark in trademark_names_norm)]
        # phrases = [phrase for phrase in phrases if any(trademark in phrase for trademark in trademark_names_norm)]
        
        skus = []
        products = []
        scores = []
        corresponding_phrases = []

        # for phrase in phrases:
        #     best_skus, best_products, best_scores = get_product_data_from_phrase(phrase, product_map, alias_map, n = 10)

        print(f"sentence: {sentence}")

        for index in phrase_indexes:
            best_skus = None
            best_products = None
            best_scores = None
            corresponding_phrase = None

            # get best matches with
            # 1. phrase with trademark name itself
            # 2. before + phrase
            # 3. phrase + after
            # 4. before + phrase + after
            phrases_to_check = [phrases[index]]
            before = phrases[index - 1] if index > 0 and index - 1 not in phrase_indexes else None
            after = phrases[index + 1] if index < len(phrases) - 1 and index + 1 not in phrase_indexes else None
            if before:
                phrases_to_check.append(before + " " + phrases[index])
            if after:
                phrases_to_check.append(phrases[index] + " " + after)
            if before and after:
                phrases_to_check.append(before + " " + phrases[index] + " " + after)
            
            for phrase in phrases_to_check:
                curr_skus, curr_products, curr_scores = get_product_data_from_phrase(phrase, product_map, alias_map, n = 10)

                # get highest score
                # if not best_scores or max(curr_scores) > max(best_scores):
                #     best_skus, best_products, best_scores = curr_skus, curr_products, curr_scores
                #     corresponding_phrase = phrase
                
                # get best ratio
                if not best_scores or max(curr_scores) % 1 > max(best_scores) % 1:
                    best_skus, best_products, best_scores = curr_skus, curr_products, curr_scores
                    corresponding_phrase = phrase
            
            print(f"best SKUs: {best_skus}")
            print(f"best products: {best_products}")
            print(f"best scores: {best_scores}")
            print(f"corresponding phrase: {corresponding_phrase}")

            skus.extend(best_skus)
            products.extend(best_products)
            scores.extend(best_scores)
            corresponding_phrases.append(corresponding_phrase)

        # separator = " | "
        # result["sku"] = separator.join(skus)
        # result["product_name"] = separator.join(products)
        # result["score"] = separator.join(scores)
        # result["phrase"] = separator.join(phrases)

        separator = " | "
        result["sku"] = json.dumps(skus)
        result["product_name"] = json.dumps(products)
        result["score"] = json.dumps(scores)
        result["phrase"] = separator.join(corresponding_phrases)
        result["token_indexes"] = json.dumps(get_keyword_indexes(sentence, alias_map))

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
            "token_indexes",
        ])

        for r in results:
            id = r.get("pmcid").replace("PMC","")
            sentence = r.get("sentence")
            sku = r.get("sku")
            product_name = r.get("product_name")
            score = r.get("score")
            phrase = r.get("phrase")
            token_indexes = r.get("token_indexes")

            writer.writerow([
                manufacturer,
                sku,
                product_name,
                score,
                phrase,
                f"https://europepmc.org/article/PMC/{id}",
                sentence,
                token_indexes,
            ])


if __name__ == "__main__":
    manufacturer = "GeneCopoeia"
    # sentence_corpus_path = "tests/data/genecopoeia_sentences_1000.jsonl"
    sentence_corpus_path = "data/europe_pmc/genecopoeia_sentences.jsonl"
    product_map_path = "data/raw_products"
    # output_csv_path = "tests/data/matcher_results_without_sku_trademark_1000.csv"
    output_csv_path = "data/europe_pmc/matcher_results_with_trademark.csv"

    run_pipeline(manufacturer=manufacturer,
                 sentence_corpus_path=sentence_corpus_path,
                 product_map_path=product_map_path,
                 output_csv_path=output_csv_path)
