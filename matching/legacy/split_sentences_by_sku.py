"""
split_sentences_by_sku.py

Reads sentences from a .json file and returns
1. Sentences with SKUs
2. Sentences without SKUs
"""


import json
from matching.sku_matcher import find_sku


def get_sentences_with_sku(sentence_corpus_path, skus, manufacturer = "GeneCopoeia"):
    return get_sentences(sentence_corpus_path, skus, have_skus=True, manufacturer=manufacturer)

def get_sentences_without_sku(sentence_corpus_path, skus, manufacturer = "GeneCopoeia"):
    return get_sentences(sentence_corpus_path, skus, have_skus=False, manufacturer=manufacturer)

def get_sentences(sentence_corpus_path, all_skus, have_skus = True, manufacturer = "GeneCopoeia"):

    results = []

    with open(sentence_corpus_path, "r", encoding="utf-8") as f:

        for line in f:
            record = json.loads(line)
            sentence = record.get("sentence", "")
            
            skus = find_sku(sentence=sentence, skus=all_skus, manufacturer=manufacturer)

            if have_skus and skus or not have_skus and not skus:
                results.append(record.copy())
    
    return results
