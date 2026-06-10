"""
query_builder.py

Biotech entity query expansion for Europe PMC.

Purpose:
- Simulate Europe PMC recall behavior
- Expand manufacturer names into spelling + entity + context variants
- Produce structured OR queries for high-recall search
"""

from typing import List, Set


# -----------------------------
# 1. Name variants
# -----------------------------

def build_name_variants(name: str) -> List[str]:
    """
    Generate spelling + formatting variants of a manufacturer name.

    Example:
        GeneCopoeia →
        - GeneCopoeia
        - Gene Copoeia
        - "GeneCopoeia"
    """

    return [
        name,
        name.replace(" ", ""),            # Gene Copoeia → GeneCopoeia (or reverse edge cases)
        f'"{name}"',
    ]


# -----------------------------
# 2. Entity/legal variants
# -----------------------------

def build_entity_variants(name: str) -> List[str]:
    """
    Generate legal / citation-style variants often seen in papers.
    """

    return [
        f"{name} Inc",
        f"{name} Inc.",
        f"{name} Corporation",
        f"{name} Co",
    ]


# -----------------------------
# 3. Context (lab usage) variants
# -----------------------------

def build_context_variants(name: str) -> List[str]:
    """
    Generate usage-context terms where manufacturers appear in papers.

    These are NOT exact names, but common co-occurring patterns.
    """

    return [
        f"{name} kit",
        f"{name} reagent",
        f"{name} assay",
        f"{name} plasmid",
        f"{name} vector",
    ]


# -----------------------------
# 4. Main query builder
# -----------------------------

def build_query(manufacturer: str) -> str:
    """
    Build a high-recall Europe PMC query.

    Strategy:
    - expand name variants
    - expand legal variants
    - expand experimental context variants
    - combine all with OR

    Returns:
        String formatted for Europe PMC API
    """

    variants: Set[str] = set()

    # expand all layers
    variants.update(build_name_variants(manufacturer))
    variants.update(build_entity_variants(manufacturer))
    variants.update(build_context_variants(manufacturer))

    # remove empties / duplicates
    variants = {v.strip() for v in variants if v and v.strip()}

    # build OR query
    return " OR ".join(variants)


# -----------------------------
# 5. Debug helper
# -----------------------------

def explain_query(manufacturer: str) -> None:
    """
    Print expanded query in readable grouped format.

    Useful for debugging recall behavior.
    """

    print("\n--- Name Variants ---")
    print(build_name_variants(manufacturer))

    print("\n--- Entity Variants ---")
    print(build_entity_variants(manufacturer))

    print("\n--- Context Variants ---")
    print(build_context_variants(manufacturer))

    print("\n--- Final Query ---")
    print(build_query(manufacturer))


if __name__ == "__main__":
    explain_query("GeneCopoeia")