# alias_scoring.py
"""
Scores an alias based on its quality and proximity to manufacturer
"""


def score_alias(alias, alias_length, alias_skus, product_map):
    """
    Scores an alias based on its length and number of skus it could refer to

    Better aliases are:
    - longer
    - refer to less skus

    alias: known alias in product_map
    alias_length: number of words of alias
    num_alias_skus: number of skus alias can refer too
    product_map: check if alias is sku: O(1) lookup
    """
    alias_length_multiplier = 2
    alias_skus_multiplier = 1

    # alias is a sku
    if alias in product_map:
        return 100

    score = alias_length * alias_length_multiplier
    
    # 10 if only points to 1 sku
    # 10, 6.67, 5, 4, ...
    score += 20 / (1 + len(alias_skus)) * alias_skus_multiplier

    # round
    num_decimal_places = 2
    score = round(score, num_decimal_places)

    return score


def score_proximity(start_index, length, manufacturer_indices):
    """
    scores alias by where it is relative to manufacturer
    
    better aliases are closer

    proximity determined by number of words away from manufacturer
    """

    min_proximity = 6769420

    for manufactuer_index in manufacturer_indices:

        words_apart = start_index - manufactuer_index

        # manufacturer_index - start_index - length
        if start_index < manufactuer_index:
            words_apart = -words_apart - length
        
        if words_apart < 0:
            words_apart = -words_apart

        min_proximity = min(min_proximity, words_apart)

    # 10 if right next to manufacturer: min_proximity = 0
    # 10, 6.67, 5, 4, ...
    score = 20 / (2 + min_proximity)

    # round
    num_decimal_places = 2
    score = round(score, num_decimal_places)

    return score