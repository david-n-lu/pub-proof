"""
inspect_headers.py

Utility script for inspecting raw biotech product CSV files.

Purpose:
    Reads all CSV files in data/raw_products/ and prints their column headers
    to help define a standardized schema for cleaning data.

Use case:
    - Identify inconsistent vendor column names (e.g., "Catalog #", "SKU")
    - Map raw CSV headers → canonical schema:
        - product_name, sku, manufacturer, aliases
    - Assists in building clean_products.py pipeline

Output:
    Prints each filename and its column headers.

This is a debugging / schema-discovery tool and is not part of production pipeline.
"""

import pandas as pd
from pathlib import Path

RAW_PRODUCTS_DIR = Path("data/raw_products")


def inspect_all_csv_headers():
    """
    Inspect column headers for all CSV files in raw_products directory.

    This helps identify inconsistent naming conventions across vendors
    before building a unified product schema.
    """

    csv_files = list(RAW_PRODUCTS_DIR.glob("*.csv"))

    headers = set()

    if not csv_files:
        print("No CSV files found in:", RAW_PRODUCTS_DIR)
        return headers

    for file in csv_files:
        print(f"{file.name}:")

        try:
            df = pd.read_csv(file, nrows=5, encoding="cp1252")  # small sample only
            df = df.dropna(axis=1, how="all")
            columns = [
                col for col in df.columns
                if not str(col).startswith("Unnamed")
            ]
            headers.update(columns)
            # print(columns)

            # print("\nSample rows:")
            # print(df.head(2).to_string(index=False))

        except Exception as e:
            print(f"Error reading {file.name}: {e}")

        print("-" * 60)
    
    return headers


headers = inspect_all_csv_headers()
print(headers)
print("Total unique headers found across all files:", len(headers))