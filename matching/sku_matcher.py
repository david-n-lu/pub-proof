"""
SKU Matcher

Finds manufacturer SKUs in sentences mentioning manufacturer

Returns all SKU matches and their distance to the manufacturer in the sentence
"""


from matching.normalization import normalize_for_matching


def find_sku(sentence, skus, manufacturer = "GeneCopoeia"):

    words = normalize_for_matching(sentence).split()

    # Get all matching indices
    manufacturer = normalize_for_matching(manufacturer)
    manufacturer_indices = [i for i, x in enumerate(words) if manufacturer in x]

    # print(sentence)
    # print(words)
    # print(manufacturer_indices)

    matches = []

    for i, word in enumerate(words):

        all_words = [word]
        all_words.extend(word.split("-"))

        # works for LT001 and LT001-02
        for w in all_words:
            
            # skus is a set or dictionary
            if w in skus:
                matches.append({
                    "sku": w,
                    "distance": min([abs(i-index) for index in manufacturer_indices])
                })

                break

    return matches