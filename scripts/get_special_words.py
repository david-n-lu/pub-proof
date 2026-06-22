from matching.normalization import normalize
from matching.product_map import build_product_map, build_alias_index
from matching.mention_extractor import get_keyword_indexes
import json
import re

def is_special(word):
    
    letters = 0
    numbers = 0
    capital = 0
    G = 0
    C = 0
    T = 0
    A = 0

    for c in word:
        if c.isalpha():
            letters += 1
            if c.isupper():
                capital += 1

                if c == "A":
                    A += 1
                if c == "C":
                    C += 1
                if c == "G":
                    G += 1
                if c == "T":
                    T += 1
                    

        if c.isdigit():
            numbers += 1
    
    # cDNA
    # LT001
    # qPCR
    # 
    # return capital >= 2 or letters and numbers
    return capital >= 2 and numbers and A + C + G + T <= 4



def get_special_words(sentence):
    words = normalize(sentence[:-1]).split()

    special = set()

    for w in words:

        # no chinese
        if s != re.sub(r'[\u4e00-\u9fff]+', '', s):
            continue

        if is_special(w):
            special.add(w)
    
    return special


if __name__ == "__main__":
    # sentence_corpus_path = "tests/data/genecopoeia_sentences.jsonl"
    sentence_corpus_path = "data/europe_pmc/genecopoeia_sentences.jsonl"
    product_map_path = "data/raw_products"

    sentences = []
    with open(sentence_corpus_path, "r", encoding="utf-8") as f:

        for line in f:
            record = json.loads(line)
            sentences.append(record.get("sentence", ""))
    
    print(f"Got {len(sentences)} sentences")


    special = set()

    for s in sentences:
        special.update(get_special_words(s))
    

    print(len(special))
    
    # line_length = 170
    # curr = ""

    # for s in special:
    #     if len(curr + ", " + s) > line_length:
    #         print(curr)
    #         curr = ""
        
    #     if curr:
    #         curr += ", "
    #     curr += s

    product_map = build_product_map(product_map_path)
    print("Built product map")

    alias_map = build_alias_index(product_map)
    print("Built alias map")


    line_length = 170
    curr = ""
    count = 0

    for s in special:
        s = s.replace("GeneCopoeia", "")

        if get_keyword_indexes(s, alias_map):
            continue

        count += 1

        # if len(repr(curr + s + ",")) > line_length:
        #     print(curr)
        #     # print(len(curr), repr(curr))
        #     curr = ""
        
        # curr += s + ", "
        curr += s + ", "
    
    print(curr)

    print(f"{count} special words NOT in product map")