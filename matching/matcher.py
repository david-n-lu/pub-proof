from matching.phrase_extractor import get_phrases_from_sentence
from matching.product_matcher import get_product_candidates
from matching.sku_matcher import find_sku


def match(
    manufacturer: str,
    sentence: str,
    product_map: dict,
    alias_map: dict,
    shortened_sku_map: dict,
    threshold: float = 0.0,
    max_candidates: int = 10,
):
    """
    Gets best product results of a sentence through SKU matching and product name string matching
    - SKU matching tracks additional SKU in sentence and original SKU
    
    Returns max_candidates results in this format:
    [
        {
            "sku": "explicit_sku",
            "sentence_sku": "explicit_sku_in_sentence",
            "original_sku": "explicit_sku_in_product_map",
            "score": 1.0
        },
        {
            "sku": "matched_sku",
            "score": 0.83,
        },
        {
            "sku": "matched_sku_2",
            "score": 0.75,
        },
    ]
    """
    
    results = []

    # -----------------------------
    # Get explicit SKU results first
    # -----------------------------

    sku_matches = find_sku(
        sentence=sentence,
        skus=shortened_sku_map,
        manufacturer=manufacturer,
    )

    for match in sku_matches:

        shortened_sku = match.get("sku")

        original_skus = shortened_sku_map.get(shortened_sku, [])

        if original_skus:
            match["original_sku"] = (next(iter(original_skus)))

        match["score"] = 1.0

        match["type"] = "sku"

        sentence = sentence.replace(match.get("sentence_sku"),"") # potentially get other products without explicit SKU

    results.extend(sku_matches)


    # -----------------------------
    # Use phrase tokens to get product mentions without explicit SKUs
    # -----------------------------

    phrases = get_phrases_from_sentence(sentence, alias_map)

    for phrase in phrases:
        token_matches = get_product_candidates(phrase, product_map, alias_map)

        results.extend(token_matches)
    

    # -----------------------------
    # Get top results
    # -----------------------------

    results = sorted(results, key=lambda result: result["score"], reverse=True)

    results = results[:max_candidates]

    results = [result for result in results if result["score"] >= threshold]

    return results