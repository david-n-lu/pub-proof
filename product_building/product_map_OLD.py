from pathlib import Path
import pandas as pd
from typing import Dict, Set
from matching.normalization import normalize, normalize_for_matching, get_shortened_sku
from collections import defaultdict


SKU_COLUMNS = ["Part ID", "Manufacturer SKU", "Part ID.1", "crispr_product_id"]
ALIAS_NAME_COLUMNS = ["Alias", "Alias Names", "Symbol"]
PRODUCT_NAME_COLUMNS = ["Product Name", "Description"]

# use "Description" instead of "Product Name" for these column names
ambiguous_product_names = {
    "OmicsLink™ shRNA Clone",
    "miTarget™ 3′ UTR miRNA Target Clones",
    "GeneHero™ CRISPR-Cas9 sgRNA",
    "GLuc-ON™ Promoter Reporter Clones",
    "OmicsLink™ Expression-Ready ORF cDNA Clones",
    "MiExpress™ Precursor miRNA Clone",
}
ambiguous_product_names_norm = [normalize_for_matching(name) for name in ambiguous_product_names]
non_ambiguous_column_name = "Description"


def tokenize(row):
    """
    helper function used by build_product_map()

    Builds aliases for a product by breaking product name into words

    Words included "-" will have each token additionally added: first-strand -> first-strand, first, and strand
    """
    s = normalize_for_matching(str(row["product_name"]))
    
    tokens = set()

    for w in s.split():
        tokens.add(w)
        if "-" in w:
            tokens.update(w.split("-"))

    # add SKU as a token too
    tokens.add(normalize_for_matching(str(row["shortened_sku"])))
    tokens.add(normalize_for_matching(str(row["sku"])))

    return tokens


def build_product_map(csv_dir: str | Path) -> Dict[str, dict]:
    """
    Builds a product_map that maps unique SKUs to
    1. shortened SKU
    2. product name
    3. search aliases
    """

    csv_dir = Path(csv_dir)

    product_map = {}

    csv_files = list(csv_dir.glob("*.csv"))

    for file_path in csv_files:

        df = pd.read_csv(file_path, encoding='utf-8-sig', low_memory=False)
        df = df.reindex(columns=SKU_COLUMNS + PRODUCT_NAME_COLUMNS)
        df = df.dropna(how="all")
        df = df.fillna("")

        # print("Read CSV")

        # create designated sku column
        # priority based on order in SKU_COLUMNS
        # if no SKU, goes to next highest priority

        df["sku"] = df[SKU_COLUMNS].replace("", pd.NA).bfill(axis=1).iloc[:, 0]
        df["sku"] = df["sku"].astype(str).apply(normalize_for_matching)
        df = df.drop_duplicates("sku", keep="first")


        # print("Created original_sku column")


        # primary lookup is through shortened sku
        # shortened_skus = get_redundant_strings_in_skus(list(df["original_sku"]))
        # df["sku"] = df["original_sku"].map(shortened_skus).fillna(df["original_sku"])
        df["shortened_sku"] = df["sku"].map(get_shortened_sku)

        # print("Got shortened sku")


        # get ambiguous names
        main_product_name_col = PRODUCT_NAME_COLUMNS[0]
        counts = df[main_product_name_col].value_counts()
        THRESHOLD = 100
        ambiguous_names = counts[counts > THRESHOLD].index.tolist()

        # print("Got ambiguous names")


        # add additional info if product_name is ambiguous
        df["original_product_name"] = df[main_product_name_col].astype(str)
        df["product_name"] = df[main_product_name_col].astype(str)

        desc_cols = PRODUCT_NAME_COLUMNS[1:] # additional info to be appended to product_name if applicable
        if ambiguous_names and desc_cols:
            mask = df["product_name"].isin(ambiguous_names)

            sub = df.loc[mask, desc_cols].replace("", pd.NA)

            desc = sub.iloc[:, 0]
            for c in sub.columns[1:]:
                desc = desc.fillna(sub[c])

            desc = desc.str.rstrip(".")

            df.loc[mask & desc.notna(), "product_name"] = (
                df.loc[mask, "original_product_name"] + ": " + desc
            )
        

        # print("Added description to ambiguous product names")


        # get aliases
        df["aliases"] = df.apply(tokenize, axis=1)


        # print("Got aliases")

        # duplicate entries for products with old skus
        normalized_names = df["product_name"].map(normalize_for_matching)
        mask = normalized_names.str.contains(r"old cat", na=False)

        if mask.any():
            duplicates = df.loc[mask].copy()

            extracted_skus = (
                normalized_names[mask]
                .str.split("old cat", n=1)
                .str[-1]
                .str.strip()
            )

            duplicates["sku"] = extracted_skus.values
            duplicates["shortened_sku"] = duplicates["sku"].map(get_shortened_sku)

            # sku_key = "sku"
            # sku_other = "shortened_sku"
            # print(duplicates[[sku_key, sku_other, "product_name"]].head(1))
            # print(len(duplicates))

            df = pd.concat([df, duplicates], ignore_index=True)

        # dupes = df[df[sku_key].duplicated(keep=False)][[sku_key, sku_other, "product_name"]]
        # print(dupes.sort_values("sku"))

        # create product_map
        sku_key = "sku"
        sku_other = "shortened_sku"

        curr_product_map = (
            df.drop_duplicates(sku_key, keep="first")
            .set_index(sku_key)[[sku_other, "product_name", "original_product_name", "aliases"]]
            .to_dict(orient="index")
        )

        # print("Created curr_product_map")

        product_map.update(curr_product_map)

    return product_map



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

    index = {}

    # items = 0
    # sum = 0
    # dup = 0
    # unique = 0

    for sku, data in product_map.items():
        for alias in data["aliases"]:
            alias_norm = normalize_for_matching(alias)

            # if alias_norm:
            # if alias_norm and alias_norm not in GENERIC_BIOTECH_TERMS:
            if alias_norm and alias_norm not in STOP_WORDS:
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
    sku = "lpp-cp-lvc9nu"

    original_sku = shortened_sku_map.get(normalize_for_matching(sku), {})
    original_sku = next(iter(original_sku)) if original_sku else sku
    
    print(f"{sku}: {original_sku}")

    print(f"{sku}: {product_map.get(original_sku, None)}")

    alias = "LPP"
    alias = normalize_for_matching(alias)
    print(f"{alias}: {alias_map.get(alias, None)}")


if __name__ == "__main__":
    test_shortend_sku()


