"""
phrase_extractor.py

Groups sentence tokens found in product map into phrases based on token distance.
"""

from typing import Dict, List
from matching.normalization import normalize_for_matching


# -----------------------------
# Extract matched phrases from sentence
# -----------------------------

def get_phrases_from_sentence(sentence: str, alias_map, max_gap: int = 2):
    """
    Extract grouped keyword phrases from a sentence.
    """

    indexes = get_keyword_indexes(
        sentence,
        alias_map
    )

    groups = group_matches(
        indexes,
        max_gap=max_gap
    )

    phrases = extract_phrases(
        groups
    )

    return phrases


# -----------------------------
# Get phrases from matched indexes
# -----------------------------

def group_matches(
    index_to_keyword: Dict[int, str],
    max_gap: int = 1,
) -> List[List[str]]:
    """
    Group keywords if they are within max_gap words apart.

    max_gap:
        0 = adjacent
        1 = one word apart
        2 = two words apart
    """

    if not index_to_keyword:
        return []

    indices = sorted(index_to_keyword)

    groups = []
    current_group = [indices[0]]

    for previous, current in zip(indices, indices[1:]):
        gap = current - previous - 1

        if gap <= max_gap:
            current_group.append(current)
        else:
            groups.append(current_group)
            current_group = [current]

    groups.append(current_group)

    return [
        [index_to_keyword[index] for index in group]
        for group in groups
    ]


def calculate_gap(index_a: int, index_b: int) -> int:
    """Return number of words between two token indexes."""

    return index_b - index_a - 1


def extract_phrases(grouped_matches):
    """
    Convert grouped matches into phrase strings.
    """

    return [
        " ".join(group)
        for group in grouped_matches
    ]


# -----------------------------
# Get matched indexes from sentence
# -----------------------------

SUBSTITUTIONS = {
    "rt qpcr": "qrt-pcr",
    "rt-qpcr": "qrt-pcr",
}


def get_word_variations(word: str):
    """
    Return matching variations of a word.

    Includes:
    - substitutions
    - singular/plural forms
    - removed trademark suffix
    """

    variations = [word]

    # Apply substitutions
    if word in SUBSTITUTIONS:
        variations.append(SUBSTITUTIONS[word])

    # Remove trademark suffix
    if word.endswith("tm"):
        variations.append(word[:-2])

    # Singular/plural variants
    if word.endswith("s") and len(word) > 1:
        variations.append(word[:-1])
    else:
        variations.append(word + "s")

    # Remove duplicates while preserving order
    return list(dict.fromkeys(variations))


def get_keyword_indexes(sentence: str, alias_map):
    """
    Return token indexes whose words match entries in alias_map.
    """

    if sentence.endswith("."):
        sentence = sentence[:-1]

    words = normalize_for_matching(sentence).split()

    indexes = {}

    for i, word in enumerate(words):
        # Try normalized word variations first
        for variation in get_word_variations(word):
            if variation in alias_map:
                indexes[i] = variation
                break

        if i in indexes:
            continue

        # Handle hyphenated terms (e.g. LT001-02, Endofectin-Max)
        parts = word.split("-")
        matches = [part for part in parts if part in alias_map]

        if matches:
            indexes[i] = "-".join(matches)

    return indexes



# -----------------------------
# test phrase extraction on manufacturer sentences.
# -----------------------------


if __name__ == "__main__":
    import json

    from product_building.product_map import build_product_map
    from product_building.product_map import build_alias_map


    sentence_path = r"data/europe_pmc/genecopoeia_sentences_OLD.jsonl"
    product_map_dir = f"data/raw_products/"

    # Build alias map
    product_map = build_product_map(product_map_dir)
    alias_map = build_alias_map(product_map)

    phrases = []

    with open(sentence_path, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)

            sentence = data["sentence"]

            sentence_phrases = get_phrases_from_sentence(
                sentence,
                alias_map,
                max_gap=2,
            )

            if sentence_phrases:
                phrases.append(sentence_phrases)
            else:
                print(sentence)

    print(f"Found {len(phrases)} sentences with phrases\n")

    for phrase_group in phrases[:100]:
        print(phrase_group)
