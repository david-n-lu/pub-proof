"""
sentence_corpus_matcher.py

Match products against a manufacturer sentence corpus.
"""

import json
import re

ALIAS_WEIGHTS = {
    "sku": 10.0,
    "long_alias": 2.5,
    "medium_alias": 1.0,
    "short_alias": 0.5,
}

def score_alias(alias: str, sku: str) -> str:
    """
    Classify an alias based on specificity.

    More specific aliases receive higher evidence weights.
    """

    alias = alias.strip()

    if alias == (sku):
        return ALIAS_WEIGHTS["sku"]

    if len(alias.split()) >= 4:
        return ALIAS_WEIGHTS["long_alias"]

    if len(alias.split()) >= 2 or len(alias) > 12:
        return ALIAS_WEIGHTS["medium_alias"]

    return ALIAS_WEIGHTS["short_alias"]

def normalize(text: str) -> str:
    text = str(text).lower()

    text = re.sub(r"[\u2010-\u2015]", "-", text)  # unify dash types

    # keep letters, numbers, spaces, and hyphens
    # remove everything else
    text = re.sub(r"[^a-z0-9\s-]", " ", text)

    text = re.sub(r"\s+", " ", text).strip()

    return text


def match_sentence(sentence, alias_map, max_alias_words=8):
    words = normalize(sentence).split()

    matches = {}

    for start in range(len(words)):
        for length in range(1, max_alias_words + 1):

            end = start + length

            if end > len(words):
                break

            phrase = " ".join(words[start:end])

            if phrase not in alias_map:
                continue

            # alias : [sku1, sku2, sku3]
            for sku in alias_map[phrase]:

                if sku not in matches:
                    matches[sku] = []
                
                matches[sku].append({
                        "alias": phrase,
                        "score": score_alias(phrase, sku)
                    })

    return matches


def match_corpus(sentence_corpus_path, product_map, alias_map, min_score = 3):
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
                sentence=sentence,
                alias_map=alias_map,
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

                total = sum(alias.get("score", 0) for alias in aliases)

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
                no_matches.append(sentence)
            
            print(f"{1 if new_record else 0} results for {sentence[:100]}...")
            total_processed += 1

    print(f"Total Hits: {total_hits}")
    print(f"Total Processed: {total_processed}")

    return results