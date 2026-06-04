"""
clean_products.py

ETL pipeline for biotech product normalization.

Pipeline:
    raw CSVs → standardized schema → matcher-ready dataset

Relies on:
    core.schema.enforce_canonical_schema
"""

import re
import pandas as pd
from pathlib import Path
from core.schema import CANONICAL_TO_KEEP

from core.schema import COLUMN_MAP

RAW_DIR = "data/raw_products"
OUT_FILE = "data/cleaned_products/product_aliases.csv"

# ----------------------------
# Biotech normalization
# ----------------------------
def normalize_biotech_text(text: str) -> str:
    text = str(text).lower()

    # fix encoding issues first
    text = fix_mojibake(text)

    # remove trademark symbols
    text = text.replace("™", "")
    text = text.replace("®", "")
    text = text.replace("©", "")

    # normalize µ variants
    text = text.replace("µl", "ul")
    text = text.replace("μl", "ul")

    # collapse whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()

def fix_mojibake(text: str) -> str:
    if not isinstance(text, str):
        return text
    try:
        return text.encode("latin1").decode("utf-8")
    except Exception:
        return text


# ----------------------------
# punctuation cleanup per token
# ----------------------------
PUNCT_STRIP = re.compile(r"^[^\w]+|[^\w]+$")  # only strips edges

def clean_and_split(text: str) -> str:
    """
    1. normalize text
    2. split by spaces
    3. strip punctuation only from token edges
    4. recombine
    """

    if text is None:
        return ""

    text = normalize_biotech_text(text)

    tokens = text.split()

    cleaned_tokens = []
    for t in tokens:
        t = PUNCT_STRIP.sub("", t)  # remove leading/trailing punctuation only
        if t and t.strip():
            cleaned_tokens.append(t)

    return " ".join(cleaned_tokens).strip()


# ----------------------------
# load + merge all CSVs
# ----------------------------
def load_folder_csvs(folder_path: str) -> pd.DataFrame:
    folder = Path(folder_path)

    csv_files = list(folder.glob("*.csv"))

    dfs = []
    for file in csv_files:
        df = pd.read_csv(file, encoding="cp1252")
        df["__source_file"] = file.name
        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)


# ----------------------------
# process dataframe
# ----------------------------
def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()

    for col in df.columns:
        if "url" in col:
            out[col] = df[col].astype(str).str.strip()
        else:
            out[col] = df[col].apply(clean_and_split)

    return out

# ----------------------------
# filter columns
# ----------------------------
def select_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """
    1. Create new df with ONLY requested target columns
    2. Aggregate raw columns based on COLUMN_MAP
    3. Combine multiple raw fields into single output field per row
    """

    inverted_map = {
        target: [raw_col for raw_col, val in COLUMN_MAP.items() if val == target]
        for target in columns
    }

    print(inverted_map)

    new_df = pd.DataFrame(index=df.index)

    for target, raw_cols in inverted_map.items():
        new_df[target] = df[raw_cols].agg(' '.join, axis=1)
        new_df[target] = new_df[target].str.strip()

        # get rid of duplicates in string
        new_df[target] = new_df[target].apply(
            lambda x: " ".join( set( str(x).split() ) )
            )

    return new_df

# ----------------------------
# export
# ----------------------------
def export_clean_csv(df: pd.DataFrame, output_path=OUT_FILE):
    df.to_csv(output_path, index=False, encoding="utf-8")


# ----------------------------
# main pipeline
# ----------------------------
def run(folder_path: str = RAW_DIR, output_path=OUT_FILE):
    raw_df = load_folder_csvs(folder_path)
    raw_df = raw_df.fillna("")
    print(raw_df.head(5))
    print(raw_df.columns)
    export_clean_csv(raw_df, "data/cleaned_products/combined.csv")

    cleaned_df = process_dataframe(raw_df)
    print(cleaned_df.head(5))

    filtered_df = select_columns(cleaned_df, CANONICAL_TO_KEEP)
    print(filtered_df.head(5))

    export_clean_csv(filtered_df, output_path)
    return cleaned_df

run()