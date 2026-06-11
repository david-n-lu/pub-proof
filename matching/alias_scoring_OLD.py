# alias_scoring.py

from dataclasses import dataclass
from typing import Dict, List
from operator import itemgetter
import math


# ----------------------------
# Config
# ----------------------------

ALPHANUM_RATIO_BONUS = 0.15
LONG_ALIAS_BONUS_CAP = 0.25


# ----------------------------
# Core scoring model
# ----------------------------

@dataclass
class AliasStats:
    alias: str
    sku_count: int          # how many SKUs this alias maps to
    alias_length: int       # number of tokens or chars (your choice upstream)


def _clean_alias(alias: str) -> str:
    return alias.strip().lower()


def _alphanum_ratio(s: str) -> float:
    if not s:
        return 0.0
    alnum = sum(c.isalnum() for c in s)
    return alnum / len(s)


def score_alias(
    stats: AliasStats,
    total_skus: int,
    product_map: Dict[str, Dict[str]],
) -> float:
    """
    Higher score = better alias (more specific, less ambiguous, cleaner)
    """

    alias = _clean_alias(stats.alias)

    # 1. specificity signal (inverse frequency across SKUs)
    # if alias maps to many SKUs -> penalize
    idf_like = math.log((total_skus + 1) / (stats.sku_count + 1))

    # 2. length signal (moderate preference for longer aliases)
    # but capped so it doesn't dominate
    length_score = math.tanh(stats.alias_length / 10.0) * LONG_ALIAS_BONUS_CAP

    # 3. cleanliness signal
    clean_bonus = _alphanum_ratio(alias) * ALPHANUM_RATIO_BONUS

    # 4. ambiguity penalty (strong)
    ambiguity_penalty = 1.0 / (1.0 + stats.sku_count)

    # 5. sku boost
    sku_boost = 20 if alias in product_map else 0

    score = (
        idf_like * 0.6 +
        length_score +
        clean_bonus +
        ambiguity_penalty +
        sku_boost
    )

    return score


# ----------------------------
# Batch scoring
# ----------------------------

def rank_aliases(
    alias_map: Dict[str, List[str]],
    product_map: Dict[str, Dict[str]],
) -> List[tuple]:
    """
    alias_map: {alias -> [sku1, sku2, ...]}

    returns: [(alias, score), ...] sorted high to low
    """

    total_skus = sum(len(v) for v in alias_map.values())

    results = {}

    for alias, skus in alias_map.items():
        stats = AliasStats(
            alias=alias,
            sku_count=len(skus),
            alias_length=len(alias.split())  # swap if you prefer char-based
        )

        score = score_alias(stats, total_skus, product_map)
        results[alias] = score

    return results


def test():
    from matching.product_map import build_product_map, build_alias_index
    alias_path = "data/raw_products"

    product_map = build_product_map(alias_path)
    print("Built product map")

    alias_map = build_alias_index(product_map)
    print("Build alias map")

    ranked_aliases = rank_aliases(alias_map, product_map)
    print("Ranked aliases")

    # print(next(iter(ranked_aliases.items())))

    sample_size = 5
    ranked_aliases = sorted(ranked_aliases.items(), key=lambda x: x[1], reverse=True)
    n = len(ranked_aliases)

    for p in range(100, -1, -10):
        # define bucket boundaries
        start = int(n * ((100-p) / 100))

        if p == 0:
            end = start
            start = end - sample_size
        else:
            end = start + sample_size

        bucket = ranked_aliases[start:end]

        print(f"\n{p}th percentile:")

        if not bucket:
            print("EMPTY")
            continue

        for alias, score in bucket:
            print(f"{alias}: {score}")

if __name__ == "__main__":
    test()

