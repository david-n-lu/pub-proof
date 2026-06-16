from pathlib import Path
import pandas as pd
import re
from collections import defaultdict
from typing import Dict, Set
from matching.normalization import normalize, normalize_for_matching
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
                    sku = str(val)
                    break

            
            product_name = row.get(product_name_column)

            if not sku or not product_name:
                continue

            sku = normalize(sku)
            product_name = normalize(product_name)

            aliases = set()

            # for col in alias_columns:
            #     val = row.get(col)

            #     if pd.isna(val):
            #         continue

            #     val = normalize(str(val))

            #     for a in val.split(" "):
            #         if a:
            #             aliases.add(a)


            sku = normalize_for_matching(sku)
            if sku not in product_map:
                product_map[sku] = {
                    "product_name": product_name,
                    "aliases": set()
                }

            product_name = normalize_for_matching(product_name)

            # include product name and as alias
            product_map[sku]["aliases"].add(product_name)

            # include sku as alias
            product_map[sku]["aliases"].add(sku)

            for a in aliases:
                a = normalize_for_matching(a)
                if a and a not in GENERIC_BIOTECH_TERMS:
                    product_map[sku]["aliases"].add(a)

            # add subsets of full product name to aliases for more permissive matching
            product_map[sku]["aliases"].update(generate_subsets(product_name))

            # alias_num_threshold = 1000
            # num_aliases = len(product_map[sku]["aliases"])
            # if num_aliases > alias_num_threshold:
            #     print(f"{product_map[sku]["product_name"]} has {num_aliases} aliases")

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
            alias_norm = normalize_for_matching(alias)

            if alias_norm and alias_norm not in GENERIC_BIOTECH_TERMS:
                if alias_norm in index:
                    index[alias_norm].add(sku)
                    # dup += 1
                else:
                    index[alias_norm] = {sku}
                    # unique += 1

                # sum += 1
        
        # items += 1
        # if items % 1000 == 0:
        #     print(f"item {items} indexed")
    
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
    "as",
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
    "removed",
    "along",

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

    # miscellaneous
     "signal",
     "retention",
     "number",
     "wild-type"
}

GENERIC_NUMBERS = {str(i) for i in range(1, 1000)}
UNITS = {
    "ul", "µl", "ml", "l",
    "ug", "µg", "mg", "g",
    "ng", "pg",
    "um", "µm", "mm", "cm",
    "nm",
    "uM", "mM", "M",
    "set", "sets",
    "vial", "vials",
    "reaction", "reactions",
    "chamber", "chambers",
    "plate", "plates",
    "well", "wells",
    "tube", "tubes",
    "pack", "packs",
    "kit", "kits"
}
PUNCTUATION = [
    ".", ",", "?", "!", ":", ";",
    "'", "\"",
    "(", ")", "[", "]", "{", "}",
    "-", "—", "–", "_",
    "/", "\\",
    "|",
    "@", "#", "$", "%", "&", "*",
    "+", "=",
    "<", ">",
    "^", "`", "~"
]
BAD_ALIAS_FILTER = ["green", "2.0", "sp", "fragments", "out", "culture", "sema5a", "expressing", "gfp", "sera", 
                    "va", "two", "nes", "promoter", "sensitivity", "open", "frame", "see", "universal", "psi", 
                    "transfer", "fluc", "mutation", "provided", "negative", "lentivirus", "which", "forward", 
                    "dual", "target", "li", "terminus", "deletion", "this", "also", "gel", "day", "tx", "1.5", 
                    "another", "cat", "restriction", "array", "mixed", "predicted", "injury", "isolated", "vitro", 
                    "clone", "000", "small", "detected", "per", "positive", "essential", "all", "one", "that", 
                    "nonspecific", "il", "produced", "short", "product", "normal", "active", "2020", "2.5", 
                    "blocking", "id", "overexpressed", "full", "tag", "ha", "coding", "sequence", "targeting", 
                    "strand", "mature", "scrambled", "reverse", "tu", "expressed", "wild", "type", "da", "mutant", 
                    "resistant", "str", "down", "pez", "six", "three", "map", "nuclei", "template", "right", "wt", 
                    "fhit", "concentration", "against", "full-length", "containing", "binding", "platelets",
                    "maintenance", "glucose", "independent", "high", "sodium", "no", "post", "supernatant",
                    "selection", "germ", "required", "cross", "fused", "only", "vessel", "ca", "fragment", "mut",
                    "variants", "end"]

GENERIC_BIOTECH_TERMS.update(GENERIC_NUMBERS)
GENERIC_BIOTECH_TERMS.update(UNITS)
GENERIC_BIOTECH_TERMS.update(PUNCTUATION)
GENERIC_BIOTECH_TERMS.update(BAD_ALIAS_FILTER)


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

    # quick sanity stats
    alias_lengths = [len(v["aliases"]) for v in product_map.values()]
    print("\n--- STATS ---")
    print(f"Avg aliases per product: {sum(alias_lengths)/len(alias_lengths):.2f}")
    print(f"Max aliases per product: {max(alias_lengths)}")

    # show first n products
    n = 1
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
    # n = 5
    print(f"\n--- FIRST {n} ALIASES ---")
    for i, (alias, sku) in enumerate(alias_index.items()):
        if i >= n:
            break
        print(f"{alias}  ->  {sku}")

    # # SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (20 RT reactions)
    # product_name = "SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (20 RT reactions)"
    
    # product_name = normalize_for_matching(product_name)
    # print(product_name)

    # for alias in generate_subsets(product_name):
    #     sku = alias_index.get(alias.lower(), "")
    #     print(alias+":", sku)


    alias = "SureScript"
    alias = normalize_for_matching(alias)
    sku = alias_index.get(alias, "")
    print(alias + ":", sku)

if __name__ == "__main__":
    test()