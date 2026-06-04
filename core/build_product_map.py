from pathlib import Path
import pandas as pd
import re
from collections import defaultdict
from typing import Dict, Set


sku_columns = ["Manufacturer SKU", "Part ID", "Part ID.1", "crispr_product_id"]
alias_columns = ["Alias", "Alias Names", "Symbol"]
product_name_column = "Product Name"

def normalize(text: str) -> str:
    if not text:
        return ""

    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


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
                    sku = normalize(val)
                    break

            
            product_name = row.get(product_name_column)

            if not sku or not product_name:
                continue

            sku = normalize(sku)
            product_name = normalize(product_name)

            aliases = set()

            for col in alias_columns:
                val = row.get(col)

                if pd.notna(val):
                    val = normalize(str(val))

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

            # always include product name as alias (important)
            product_map[sku]["aliases"].add(product_name)

            for a in aliases:
                if a:
                    product_map[sku]["aliases"].add(a)

    return product_map


def build_alias_index(product_map: Dict[str, dict]) -> Dict[str, str]:
    """
    alias → sku
    """

    index = {}

    for sku, data in product_map.items():
        for alias in data["aliases"]:
            alias_norm = normalize(alias)

            if alias_norm:
                index[alias_norm] = sku

    return index