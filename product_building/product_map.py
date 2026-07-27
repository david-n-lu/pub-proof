from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, Set
from matching.normalization import normalize, normalize_for_matching, get_shortened_sku
from collections import defaultdict



# SKU_COL = "Part ID"
# PRODUCT_COL = "Product Name"
# DESCRIPTION_COL = "Description"
# USE_COLS = [SKU_COL, PRODUCT_COL, DESCRIPTION_COL]

# use "Description" instead of "Product Name" for these column names
# AMBIGUOUS_PRODUCT_NAMES = {
#     "OmicsLink™ shRNA Clone",
#     "miTarget™ 3′ UTR miRNA Target Clones",
#     "GeneHero™ CRISPR-Cas9 sgRNA",
#     "GLuc-ON™ Promoter Reporter Clones",
#     "OmicsLink™ Expression-Ready ORF cDNA Clones",
#     "MiExpress™ Precursor miRNA Clone",
# }


def build_product_map(
        csv_dir: str | Path,
        SKU_COL: str,
        PRODUCT_COL: str,
        DESCRIPTION_COL: str,
    ) -> Dict[str, dict]:
    """
    Builds a product_map that maps unique SKUs to
    1. shortened SKU
    2. product name
    """

    csv_dir = Path(csv_dir)

    product_map = {}

    csv_files = list(csv_dir.glob("*.csv"))

    for file_path in csv_files:

        df = pd.read_csv(
            file_path,
            encoding = "utf-8-sig",
            usecols = [SKU_COL, PRODUCT_COL, DESCRIPTION_COL],
            dtype = str,
        )
        df = df.dropna(how="all")
        df = df.fillna("")

        # print(f"Read {file_path} with {len(df)} lines")


        df["sku"] = df[SKU_COL].map(normalize_for_matching)
        df = df.drop_duplicates("sku", keep="first")

        # print("Created original_sku column")

        df["shortened_sku"] = df["sku"].map(get_shortened_sku)

        # print("Got shortened skus")


        # get ambiguous names
        THRESHOLD = 1000
        
        counts = df[PRODUCT_COL].value_counts()
        ambiguous_names = counts[counts > THRESHOLD].index.tolist()

        # print(ambiguous_names)
        # print("Got ambiguous names")


        # add additional info if product_name is ambiguous
        df["original_product_name"] = df[PRODUCT_COL].astype(str)

        df["product_name"] = np.where(
            df["original_product_name"].isin(ambiguous_names)
            & (df[DESCRIPTION_COL].str.strip() != ""),
            
            df["original_product_name"].astype(str) + ": " + df[DESCRIPTION_COL].astype(str).str.rstrip("."),

            df["original_product_name"],
        )

        # print("Got product names")        


        # create product_map
        df = df.drop_duplicates("sku", keep="first")

        # Zip the arrays directly into a dictionary structure
        curr_product_map = {
            sku: {
                "shortened_sku": s_sku,
                "product_name": p_name,
                "original_product_name": o_name,
            }
            for sku, s_sku, p_name, o_name in zip(
                df["sku"],
                df["shortened_sku"],
                df["product_name"],
                df["original_product_name"],
            )
        }

        # print("Created curr_product_map")

        product_map.update(curr_product_map)
    
    add_old_skus(product_map)

    # print("Added Old SKUs")

    return product_map


def add_old_skus(product_map: Dict[str, dict]):
    """
    Adds new entries to products with "old cat" mentioned in the product name
    """
    new_entries = {}

    # Loop through your master map
    for data in product_map.values():
        product_name = data["product_name"]
        product_name_norm = normalize_for_matching(product_name)
        
        # Search for "old cat" in the product name
        if "old cat" in product_name_norm:
            old_sku = product_name_norm.split("old cat")[-1].strip()
            
            # 3. Queue the new entry
            new_entries[old_sku] = {
                "shortened_sku": get_shortened_sku(old_sku),
                "product_name": product_name,
                "original_product_name": data["original_product_name"]
            }

    product_map.update(new_entries)



def build_alias_map(product_map: Dict[str, dict]) -> Dict[str, set]:
    """
    maps search aliases to SKUs

    aliases can be:
    1. SKU
    2. shortened SKU
    3. Product name
    4. Search tokens derived from words of product name

    an alias can map to multiple SKUs
    """

    STOP_WORDS = {
    "a", "an", "the",
    "and", "or", "but", "nor",
    "if", "then", "else", "when", "while",
    "for", "of", "in", "on", "at", "by", "with", "from", "to", "into", "onto", "over", "under",
    "is", "am", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did",
    "this", "that", "these", "those",
    "it", "its", "they", "them", "their", "we", "you", "he", "she", "him", "her",
    "as", "than", "too", "very", "cat"
    }
    STOP_NUMBERS = [str(i) for i in range(1000)]
    STOP_LETTERS = list("abcdefghijklmnopqrstuvwxyz")
    STOP_UNITS = ["l", "dl", "cl", "ml", "ul", "nl", "pl",
                "kg", "g", "mg", "ug", "ng", "pg", "fg",
                "km", "m", "cm", "mm", "um", "nm", "pm",]
    STOP_WORDS.update(STOP_NUMBERS)
    STOP_WORDS.update(STOP_LETTERS)
    STOP_WORDS.update(STOP_UNITS)

    alias_map = {}

    for sku, data in product_map.items():
        shortened_sku = data["shortened_sku"]
        product_name = data["product_name"]
        
        aliases = set()
        aliases.add(normalize_for_matching(sku))
        aliases.add(normalize_for_matching(shortened_sku))
        aliases.update(tokenize(product_name))

        for alias in aliases:
            if alias not in STOP_WORDS:
                if alias not in alias_map:
                    alias_map[alias] = set()
                
                alias_map[alias].add(sku)


    # turn sets into lists for msgpack serialization
    alias_map = {
        key: list(value)
        for key, value in alias_map.items()
    }

    return alias_map


def tokenize(product_name):
    """
    helper function used by build_alias_map()

    Builds aliases for a product by breaking product name into words

    Words included "-" will have each token additionally added: first-strand -> first-strand, first, and strand
    """
    product_name_norm = normalize_for_matching(product_name)
    
    tokens = set()

    for word in product_name_norm.split():
        tokens.add(word)
        if "-" in word:
            tokens.update(word.split("-"))

    return tokens


def build_shortened_sku_map(product_map):
    """
    Maps shortened SKUs to original SKUs

    Publications typically don't include the edition part of SKUs
    Searching with a shortened SKU helps find more products
    """
    shortened_sku_map = defaultdict(set)

    for sku, data in product_map.items():
        shortened_sku_map[data["shortened_sku"]].add(sku)
        shortened_sku_map[sku].add(sku)

    shortened_sku_map = dict(shortened_sku_map)

    # turn sets into lists for msgpack serialization
    shortened_sku_map = {
        key: list(value)
        for key, value in shortened_sku_map.items()
    }

    return shortened_sku_map



def test_shortend_sku():
    csv_dir = "data/raw_products"

    product_map = build_product_map(csv_dir)
    print("Built product map")

    print(len(product_map))

    alias_map = build_alias_map(product_map)
    print("Built alias map")

    print(len(alias_map))

    shortened_sku_map = build_shortened_sku_map(product_map)
    print("Built shortened sku map")

    print(len(shortened_sku_map))

    # sku = "EX-M0173"
    sku = "HCP364663-CG04-3-10"

    original_sku = shortened_sku_map.get(normalize_for_matching(sku), {})
    original_sku = next(iter(original_sku)) if original_sku else sku
    
    print(f"{sku}: {original_sku}")

    print(f"{sku}: {product_map.get(original_sku, None)}")

    alias = "UPP1"
    alias = normalize_for_matching(alias)
    print(f"{alias}: {alias_map.get(alias, None)}")


if __name__ == "__main__":
    test_shortend_sku()


