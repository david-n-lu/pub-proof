from pathlib import Path
import pandas as pd
import re
from collections import defaultdict
from typing import Dict, Set
from core.text_normalization import lightweight_normalize, heavy_normalize
from itertools import combinations


sku_columns = ["Manufacturer SKU", "Part ID", "Part ID.1", "crispr_product_id"]
alias_columns = ["Alias", "Alias Names", "Symbol"]
product_name_column = "Product Name"


def build_product_map(csv_dir: str | Path) -> Dict[str, dict]:

    csv_dir = Path(csv_dir)

    product_map = {}

    csv_files = list(csv_dir.glob("*.csv"))

    for file_path in csv_files:
        df = pd.read_csv(file_path, encoding='cp1252', low_memory=False)

        for _, row in df.iterrows():
            
            sku = None
            for col in sku_columns:
                val = row.get(col)

                if pd.notna(val) and str(val).strip():
                    sku = lightweight_normalize(val)
                    break

            
            product_name = row.get(product_name_column)

            if not sku or not product_name:
                continue

            sku = lightweight_normalize(sku)
            product_name = heavy_normalize(product_name)

            aliases = set()

            for col in alias_columns:
                val = row.get(col)

                if pd.notna(val):
                    val = lightweight_normalize(str(val))

                    for p in val.split(" "):
                        p = lightweight_normalize(p)
                        if p:
                            aliases.add(p)

            if sku not in product_map:
                product_map[sku] = {
                    "product_name": product_name,
                    "aliases": set()
                }

            # include product name as alias
            product_map[sku]["aliases"].add(product_name)

            # include sku as alias
            product_map[sku]["aliases"].add(sku)

            for a in aliases:
                if a and a not in GENERIC_BIOTECH_TERMS:
                    product_map[sku]["aliases"].add(a)

            # add subsets of full product name to aliases for more permissive matching
            product_map[sku]["aliases"].update(generate_subsets(product_name))

    return product_map


def build_alias_index(product_map: Dict[str, dict]) -> Dict[str, set]:
    """
    alias → sku
    """

    index = {}

    # items = 0
    # sum = 0
    # dup = 0
    # unique = 0

    for sku, data in product_map.items():
        for alias in data["aliases"]:
            # alias_norm = alias
            alias_norm = lightweight_normalize(alias)

            if alias_norm and alias_norm not in GENERIC_BIOTECH_TERMS:
                if alias_norm in index:
                    index[alias_norm].add(sku)
                    # dup += 1
                else:
                    index[alias_norm] = {sku}
                    # unique += 1

                # sum += 1
        
        # items += 1
    
    # print(items, sum, dup, unique)

    return index


GENERIC_BIOTECH_TERMS = {
    # core product packaging
    "kit", "assay", "system", "solution", "reagent", "reagents",
    "panel", "set", "bundle", "pack", "package", "packaging",
    "mix", "mixture", "formulation", "cocktail",

    # lab consumables
    "buffer", "buffers", "substrate", "media", "medium",
    "diluent", "diluents", "concentrate", "control", "controls",
    "standard", "standards", "calibrator", "calibrators",

    # molecular biology workflows
    "expression", "purification", "amplification", "detection",
    "quantification", "sequencing", "cloning", "transfection",
    "transformation", "labeling", "staining", "extraction",
    "isolation", "synthesis", "screening", "profiling",

    # biomolecules / entities (generic context words)
    "protein", "proteins", "antibody", "antibodies",
    "enzyme", "enzymes", "dna", "rna", "plasmid", "plasmids",
    "vector", "vectors", "virus", "viral",
    "cell", "cells", "tissue", "tissues",
    "serum", "plasma",

    # commercial / marketing descriptors
    "premium", "grade", "ultra", "plus", "max", "mini",
    "starter", "advanced", "complete", "ready", "ready-to-use",
    "high-performance", "research", "research-grade", "rtu",

    # biological modifiers (often not identity)
    "human", "mouse", "rat", "rabbit", "recombinant", "synthetic",
    "natural", "purified",

    # basic function words
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "nor",
    "for",
    "so",
    "yet",
    "to",
    "of",
    "in",
    "on",
    "at",
    "by",
    "with",
    "without",
    "from",
    "into",
    "over",
    "under",
    "after",
    "before",
    "during",

    # numbers
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",

    # letters
    "a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z",

    # verb / auxiliary / generic actions
    "used",
    "using",
    "use",
    "was",
    "were",
    "is",
    "are",
    "be",
    "been",
    "being",

    # research / paper structure words
    "study",
    "studies",
    "analysis",
    "analyses",
    "result",
    "results",
    "method",
    "methods",
    "protocol",
    "protocols",
    "assay",
    "assays",
    "kit",
    "kits",
    "system",
    "systems",
    "effect",
    "effects",
    "data",
    "figure",
    "figures",
    "table",
    "sample",
    "samples",

    # biological entities (too generic for alias matching)
    "cell",
    "cells",
    "lines",
    "line",
    "patient",
    "patients",
    "group",
    "groups",
    "treatment",
    "treated",
    "control",
    "controls",
    "expression",
    "level",
    "levels",
    "activity",
    "activities",
    "protein",
    "proteins",
    "rna",
    "dna",
    "mrna",
    "gene",
    "genes",
    "model",
    "models",
    "mouse",
    "mice",
    "human",
    "humans",
    "animal",
    "animals",

    # statistical / interpretation words
    "significant",
    "significantly",
    "increase",
    "increases",
    "decrease",
    "decreases",
    "higher",
    "lower",
    "compared",
    "respectively",
    "therefore",
    "however",
    "thus",
    "moreover",
    "furthermore",
    "addition",
}


def generate_subsets(product_name: str):
    """
    Build relevant word subsets of full product names for better aliases matching

    Example: "Lenti-Pac HIV Expression Packaging Kit (20 reactions)"
    - "Lenti-Pac"
    - "HIV"
    - "Lenti-Pac HIV"
    """

    words = product_name.split()

    words = [ w for w in words if w not in GENERIC_BIOTECH_TERMS]

    return [
        " ".join(combo)
        for r in range(1, len(words) + 1)
        for combo in combinations(words, r)
    ]



def test():

    csv_dir = "data/raw_products"

    print("\n[BUILDING PRODUCT MAP]")
    product_map = build_product_map(csv_dir)

    print(f"\nTotal SKUs: {len(product_map)}")

    # show first n products
    n = 10
    print(f"\n--- FIRST {n} PRODUCTS ---")
    for i, (sku, data) in enumerate(product_map.items()):
        if i >= n:
            break
        print(f"\nSKU: {sku}")
        print(f"Product: {data['product_name']}")
        print(f"Alias count: {len(data['aliases'])}")
        print(f"Sample aliases: {list(data['aliases'])}")

    print("\n[BUILDING ALIAS INDEX]")
    alias_index = build_alias_index(product_map)

    print(f"\nTotal aliases indexed: {len(alias_index)}")

    # show first n alias mappings
    n = 10
    print(f"\n--- FIRST {n} ALIASES ---")
    for i, (alias, sku) in enumerate(alias_index.items()):
        if i >= n:
            break
        print(f"{alias}  ->  {sku}")

    # quick sanity stats
    alias_lengths = [len(v["aliases"]) for v in product_map.values()]
    print("\n--- STATS ---")
    print(f"Avg aliases per product: {sum(alias_lengths)/len(alias_lengths):.2f}")
    print(f"Max aliases per product: {max(alias_lengths)}")

    # # SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (20 RT reactions)
    # product_name = "SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (20 RT reactions)"
    
    # product_name = heavy_normalize(product_name)
    # print(product_name)

    # for alias in generate_subsets(product_name):
    #     sku = alias_index.get(alias.lower(), "")
    #     print(alias+":", sku)


    alias = "SureScript"
    alias = heavy_normalize(alias)
    sku = alias_index.get(alias, "")
    print(alias + ":", sku)


# test()