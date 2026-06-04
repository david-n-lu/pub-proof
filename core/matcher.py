"""
matcher.py

High-performance biotech entity matching pipeline for linking product mentions in biomedical
literature (PubMed / PMC) to structured product records.

This module uses Aho-Corasick for fast multi-pattern alias matching, combined with
section-aware scoring to identify strong evidence sentences linking products and manufacturers.

Pipeline:
XML → section parsing → sentence extraction → alias matching → scoring → ranked evidence output
"""

import ahocorasick
from collections import defaultdict
from typing import List, Dict

from core.text_normalization import lightweight_normalize as normalize

# -------------------------
# Build automaton
# -------------------------

def build_automaton(product_map: Dict[str, dict]):
    """
    Build an Aho-Corasick automaton from product aliases.
    Enables fast multi-pattern matching across large alias sets.
    Maps matched aliases back to their corresponding SKUs.
    """

    A = ahocorasick.Automaton()

    for sku, data in product_map.items():
        for alias in data["aliases"]:
            alias_norm = normalize(alias)

            if not alias_norm or not isinstance(alias_norm, str):
                continue

            alias_norm = alias_norm.strip()

            if len(alias_norm) < 2:
                continue
            
            A.add_word(alias_norm, (alias_norm, sku, classify_alias(alias_norm, product_map)))

    A.make_automaton()

    return A


def classify_alias(alias: str, product_map: Dict[str, dict]):
    alias = alias.strip()

    if alias in product_map: # hashmap lookup
        return "sku"

    if len(alias.split()) >= 4: # 4 words = long alias
        return "long_alias"

    if len(alias.split()) >= 2 or len(alias) > 12: # 2+ words or 12 chars = mediumm alias
        return "medium_alias"

    return "short_alias"

# -------------------------
# Candidate extraction
# -------------------------

ALIAS_WEIGHTS = {
    "sku": 5.0,
    "long_alias": 2.5,
    "medium_alias": 1.5,
    "short_alias": 0.5
}

def extract_candidates(text: str, automaton, allowed_skus=None):
    """
    Scan a sentence for product aliases using the automaton.
    Returns all SKUs whose aliases appear in the text.
    Runs in near-linear time over input text.
    """
    
    matches = defaultdict(float)

    if not text:
        return []

    text_norm = normalize(text)

    for _, value in automaton.iter(text_norm):
        alias, sku, alias_type = value

        if allowed_skus is not None and sku not in allowed_skus:
            continue

        weight = ALIAS_WEIGHTS.get(alias_type, 1.0)
        matches[sku] += weight

    return matches


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
    "unknown": 1
}

def score_match(section: str, text: str, manufacturer: str, alias_scores: dict[str, float] = None) -> int:
    """
    Heuristic scoring for evidence strength.
    Rewards manufacturer co-occurrence and high-value sections like Methods.
    Returns a confidence score used for filtering matches.
    """

    score = SECTION_WEIGHT.get(section.lower(), 1)

    t = text.lower()
    m = manufacturer.lower()

    if m in t:
        score += 2

    if f"by {m}" in t:
        score += 2

    if f"from {m}" in t:
        score += 1

    if "purchased" in t or "obtained" in t:
        score += 1
    
    if alias_scores:
        score += max(alias_scores.values())

    return score


# -------------------------
# Main function
# -------------------------
def find_product_manufacturer_evidence(
    sentences: List[Dict],
    automaton,
    manufacturer: str,
    min_score: int = 3
) -> List[Dict]:
    """
    Main pipeline for extracting product-manufacturer evidence.
    Matches aliases in sentences using Aho-Corasick and applies scoring filters.
    Returns ranked high-confidence evidence snippets with matched SKUs.
    """

    evidence = defaultdict(lambda: {"score": 0, "hits": None})

    for s in sentences:
        text = s.get("context", "")
        section = s.get("section", "unknown")

        if not text:
            continue

        skus = extract_candidates(text, automaton)

        if not skus:
            continue

        score = score_match(section, text, manufacturer, skus)

        if score >= min_score:
            key = text

            source = s.get("source", None)
            id = s.get("id", None)

            evidence[key]["source"] = source
            evidence[key]["id"] = id

            evidence[key]["score"] = max(evidence[key]["score"], score)
            evidence[key]["hits"] = {
                "section": section,
                "text": text,
                "skus": skus
            }

    return sorted(evidence.values(), key=lambda x: x["score"], reverse=True)