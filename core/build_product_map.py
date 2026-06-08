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

                    # unify separators
                    val = re.sub(r"[|,]", ";", val)

                    for p in val.split(";"):
                        p = p.strip()
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
                if a:
                    product_map[sku]["aliases"].add(a)

            # add subsets of full product name to aliases for more permissive matching
            product_map[sku]["aliases"].update(generate_subsets(product_name))

    return product_map


def build_alias_index(product_map: Dict[str, dict]) -> Dict[str, str]:
    """
    alias → sku
    """

    index = {}

    for sku, data in product_map.items():
        for alias in data["aliases"]:
            alias_norm = lightweight_normalize(alias)

            if alias_norm:
                index[alias_norm] = sku

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
    "human", "mouse", "rat", "recombinant", "synthetic",
    "natural", "purified"
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