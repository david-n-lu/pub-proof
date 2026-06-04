"""
core/io.py

PubProof I/O layer.

This module handles all structured data ingestion for the PubProof pipeline,
including:
- loading product input CSVs for evidence retrieval
- loading product alias mappings
- constructing normalized product maps used across matching and evidence extraction

Design principle:
This module is responsible only for I/O + lightweight validation.
No matching, API calls, or business logic should live here.
"""

from typing import Dict, List, Any
import pandas as pd
from core.schema import CANONICAL_FIELDS
from core.text_normalization import normalize_biotech_text, fix_product_name

# ----------------------------
# Input: Evidence Search CSV
# ----------------------------

def load_evidence_input(csv_path: str) -> List[Dict[str, str]]:
    """
    Load input products used for PubMed / Europe PMC evidence search.

    Expected columns:
        - sku
        - product_name

    Returns:
        List of dicts:
        [
            {"sku": "...", "product_name": "..."},
            ...
        ]
    """

    df = pd.read_csv(csv_path, encoding="cp1252")

    required_cols = {"sku", "product_name"}
    missing = required_cols - set(df.columns)

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = df[["sku", "product_name"]].dropna()
    df["product_name"] = df["product_name"].apply(fix_product_name)


    def tokenize(sku: str, product_name: str) -> List[str]:
        """
        Creates token list from sku + product_name.
        Normalized, split on whitespace.
        """
        sku_tokens = normalize_biotech_text(sku).split()
        name_tokens = normalize_biotech_text(product_name).split()
        return sku_tokens + name_tokens

    df["tokens"] = df.apply(
        lambda row: tokenize(row["sku"], row["product_name"]),
        axis=1
    )

    return df.to_dict(orient="records")


# ----------------------------
# Product Map Builder
# ----------------------------


def get_product_map(aliases_csv_path: str = "data/cleaned_products/product_aliases.csv"):
    df = pd.read_csv(aliases_csv_path, encoding="cp1252", dtype=str).fillna("")
    
    product_map = build_product_alias_map(df)

    return product_map


def build_product_alias_map(df):
    """

    Builds a canonical → alias-set mapping for product entity resolution.

    Key idea:
    - Uses CANONICAL_FIELDS to decide what to include
    - Automatically excludes 'manufacturer'
    - Produces a unified set of searchable terms per product

    Output structure:
        {
            product_name_clean: {
                product_name
                alias_1,
                alias_2,
                ...
                sku,
                bio_targets
            }
        }

    Expected input:
        df with at least:
        - product_name_clean
        - aliases (optional, pipe-delimited string)

    Returns:
        dict[str, set[str]]: canonical name → set of normalized aliases
    """
    
    key_name = "sku"
    df["smallest"] = df[key_name].str.split(" ").apply(lambda x: min(x, key=len))
    keys = df["smallest"].tolist()

    value_cols = list(CANONICAL_FIELDS)
    exclude_cols = ["manufacturer"]

    value_cols = [item for item in value_cols if item not in exclude_cols]
    values = (df[value_cols].astype(str).apply(' '.join, axis=1)).tolist()
    values = [list(set(string.split())) for string in values]

    exclude_values = ["human", "rat", "mouse", "rabbit"]
    exclude_values = set(exclude_values)
    values = [[item for item in sublist if item not in exclude_values] for sublist in values]

    # print(len(keys))
    # print(len(values))

    product_map = dict(zip(keys, values))

    return product_map