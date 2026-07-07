from matching.mention_extractor import get_best_phrases, extract_best_product_mention, score_phrase
from matching.product_map import build_alias_index, build_product_map


product_map_path = "data/raw_products"

product_map = build_product_map(product_map_path)
print("Built product map")

alias_map = build_alias_index(product_map)
print("Build alias map")


sentence = "Real-time PCR reactions were prepared using the All-in-One qPCR Mix (GeneCopoeia)."


phrases = get_best_phrases(sentence, alias_map, penalty=10.0)

print(phrases)
        
skus = []
products = []
scores = []
corresponding_phrases = []
for phrase in phrases:
    phrase_skus = extract_best_product_mention(phrase, alias_map, n = 10)
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

print(skus)
print(products)
print(scores)
print(corresponding_phrases)