"""
matcher.py

Product-specific biotech evidence matcher.

This module identifies mentions of a single product within biomedical
literature (PubMed / PMC) by searching for known product aliases in
sentence-level text.

Pipeline:
XML → section parsing → sentence extraction → alias matching → scoring → ranked evidence output

Design:
- Searches aliases for one product at a time.
- Uses lightweight normalized string matching.
- Applies alias-specific confidence weights.
- Scores evidence using section context and manufacturer co-occurrence.
"""

from collections import defaultdict
from typing import List, Dict, Set

from core.text_normalization import lightweight_normalize as normalize

# -------------------------
# Alias matching
# -------------------------

ALIAS_WEIGHTS = {
    "sku": 10.0,
    "long_alias": 2.5,
    "medium_alias": 1.5,
    "short_alias": 0.5,
}


def classify_alias(alias: str, sku: str) -> str:
    """
    Classify an alias based on specificity.

    More specific aliases receive higher evidence weights.
    """

    alias = alias.strip()

    if alias == normalize(sku):
        return "sku"

    if len(alias.split()) >= 4:
        return "long_alias"

    if len(alias.split()) >= 2 or len(alias) > 12:
        return "medium_alias"

    return "short_alias"


def find_alias_matches(
    text: str,
    sku: str,
    aliases: Set,
) -> Dict[str, float]:
    """
    Search text for aliases belonging to a single product.

    Returns:
        {
            "Lipofectamine 3000": 2.5,
            "L3000": 0.5
        }
    """

    if not text:
        return {}

    text_norm = normalize(text)
    alias_scores = {}

    for alias in aliases:
        alias_norm = normalize(alias)

        if not alias_norm:
            continue

        if alias_norm not in text_norm:
            continue

        alias_type = classify_alias(alias_norm, sku)
        weight = ALIAS_WEIGHTS.get(alias_type, 1.0)

        alias_scores[alias] = weight

    return alias_scores


# -------------------------
# Scoring
# -------------------------

SECTION_WEIGHT = {
    "methods": 3,
    "materials and methods": 3,
    "results": 2,
    "abstract": 2,
    "introduction": 1,
    "discussion": 1,
    "unknown": 1,
}


def score_match(
    section: str,
    text: str,
    manufacturer: str,
    alias_scores: Dict[str, float] = None,
) -> float:
    """
    Heuristic scoring for evidence strength.

    Rewards:
    - Methods / Results sections
    - Manufacturer mentions
    - Purchasing language
    - Strong alias matches
    """

    # score = SECTION_WEIGHT.get(section.lower(), 1)
    score = 0

    t = text.lower()
    m = manufacturer.lower()

    # if m in t:
    #     score += 2

    # if f"by {m}" in t:
    #     score += 2

    # if f"from {m}" in t:
    #     score += 1

    # if "purchased" in t or "obtained" in t:
    #     score += 1

    if alias_scores:
        # score += max(alias_scores.values())
        score += sum(alias_scores.values())

    return score


# -------------------------
# Main function
# -------------------------

def find_product_manufacturer_evidence(
    sentences: List[Dict],
    manufacturer: str,
    sku: str,
    aliases: Set,
    min_score: int = 2,
) -> List[Dict]:
    """
    Extract evidence linking a manufacturer and product
    from publication text.

    Returns ranked evidence snippets containing:
    - source metadata
    - evidence score
    - matched aliases
    - section information
    """

    evidence = defaultdict(lambda: {"score": 0, "hits": None})

    for s in sentences:
        text = s.get("context", "")
        section = s.get("section", "unknown")

        if not text:
            continue

        alias_scores = find_alias_matches(
            text=text,
            sku=sku,
            aliases = aliases,
        )

        if not alias_scores:
            continue

        score = score_match(
            section=section,
            text=text,
            manufacturer=manufacturer,
            alias_scores=alias_scores,
        )

        if score < min_score:
            continue

        key = text

        evidence[key]["source"] = s.get("source")
        evidence[key]["id"] = s.get("id")

        evidence[key]["score"] = max(
            evidence[key]["score"],
            score,
        )

        evidence[key]["hits"] = {
            "section": section,
            "text": text,
            "sku": sku,
            "aliases": alias_scores,
        }

    return sorted(
        evidence.values(),
        key=lambda x: x["score"],
        reverse=True,
    )