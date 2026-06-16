"""
sentence_corpus_matcher.py

Match products against a manufacturer sentence corpus.
"""

import json
from matching.normalization import normalize_for_matching
from matching.alias_scoring import score_alias, score_proximity

# ALIAS_WEIGHTS = {
#     "sku": 10.0,
#     "long_alias": 2.5,
#     "medium_alias": 1.0,
#     "short_alias": 0.5,
# }
# 
# def score_alias(alias: str, sku: str) -> float:
#     """
#     Classify an alias based on specificity.

#     More specific aliases receive higher evidence weights.
#     """

#     alias = alias.strip()

#     if alias == (sku):
#         return ALIAS_WEIGHTS["sku"]

#     if len(alias.split()) >= 4:
#         return ALIAS_WEIGHTS["long_alias"]

#     if len(alias.split()) >= 2 or len(alias) > 12:
#         return ALIAS_WEIGHTS["medium_alias"]

#     return ALIAS_WEIGHTS["short_alias"]


def match_sentence(sentence, alias_map, product_map, manufacturer = "GeneCopoeia", max_alias_words=15):
    words = normalize_for_matching(sentence).split()

    # Get all matching indices
    manufacturer = normalize_for_matching(manufacturer)
    manufacturer_indices = [i for i, x in enumerate(words) if x == manufacturer]

    matches = {}

    for start in range(len(words)):
        for length in range(1, max_alias_words + 1):

            end = start + length

            if end > len(words):
                break

            phrase = " ".join(words[start:end])

            if phrase not in alias_map:
                continue
            
            alias_skus = alias_map[phrase]
            alias_score = score_alias(phrase, length, alias_skus, product_map)
            alias_proximity = score_proximity(start, length, manufacturer_indices)
            # score = alias_quality + alias_proximity

            for sku in alias_skus:

                if sku not in matches:
                    matches[sku] = {} # dictionary
                
                if phrase not in matches[sku]:
                    # matches[sku][phrase] = {
                    #     "score": alias_score,
                    #     "proximity": alias_proximity,
                    # }

                    matches[sku][phrase] = alias_score + alias_proximity
                else:
                    matches[sku][phrase] = max(matches[sku][phrase], alias_score + alias_proximity)

    return matches


def match_corpus(sentence_corpus_path, product_map, alias_map, manufacturer, min_score = 3):
    """
    Match all sentences in a manufacturer sentence corpus.

    Args:
        sentence_corpus_path (str): path to manufacturer sentence JSONL
        product_map (dict): product lookup table
        alias_map (dict): alias lookup table

    Returns:
        list[dict]: matched evidence records
    """

    results = []
    no_matches = []
    total_hits = 0
    total_processed = 0

    with open(sentence_corpus_path, "r", encoding="utf-8") as f:

        for line in f:
            record = json.loads(line)
            sentence = record

            if isinstance(record, dict):
                sentence = record.get("sentence", "")

            matches = match_sentence(
                sentence, 
                alias_map, 
                product_map, 
                manufacturer=manufacturer
            )

            # # add all results
            # count = 0

            # for sku, aliases in matches.items():

            #     total = sum(alias.get("score", 0) for alias in aliases)

            #     if total < min_score:
            #         continue
                
            #     # record only has string data only: shallow copy allowed
            #     new_record = record.copy() if isinstance(record, dict) else {}
                
            #     new_record["product_name"] = product_map[sku]["product_name"]
            #     new_record["sku"] = sku
            #     new_record["score"] = total
            #     new_record["aliases"] = aliases

            #     results.append(new_record)
            #     count += 1
            
            # print(f"{count} results for {sentence}")


            # add result with highest score
            max = 0
            new_record = None
            for sku, aliases in matches.items():

                total = sum(aliases.values()) # dictionary
                # total = sum(v.get("score", 0) for v in aliases.values())
                # total += sum(v.get("proximity", 0) for v in aliases.values())

                if total < min_score:
                    continue
            
                if total <= max:
                    continue

                max = total
                
                # record only has string data only: shallow copy allowed
                new_record = record.copy() if isinstance(record, dict) else {}

                new_record["product_name"] = product_map[sku]["product_name"]
                new_record["sku"] = sku
                new_record["score"] = total
                new_record["aliases"] = aliases
            
            if new_record:
                results.append(new_record)
                total_hits += 1
            else:
                no_matches.append(record.copy())
            
            print(f"{1 if new_record else 0} results for {sentence[:100]}...")
            total_processed += 1

    print(f"Total Hits: {total_hits}")
    print(f"Total Processed: {total_processed}")

    return results, no_matches