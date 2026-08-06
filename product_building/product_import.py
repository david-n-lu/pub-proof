from collections import Counter
from pathlib import Path

from numpy import save
import pandas as pd
import msgpack
import json
import re

from matching.normalization import normalize_for_matching


from annotator.manual_search import create_df


from product_building.product_map import (
    build_product_map,
    build_alias_map,
    build_shortened_sku_map,
)


def get_csv_files(products_dir):
    return sorted(Path(products_dir).glob("*.csv"))


def get_column_counts(products_dir):
    """
    Returns:
        {
            column_name: number_of_csv_files_using_it
        }
    """

    counts = Counter()

    for csv_file in Path(products_dir).glob("*.csv"):
        try:
            columns = pd.read_csv(
                csv_file,
                nrows=0
            ).columns

            counts.update(columns)

        except Exception as e:
            print(f"Skipping {csv_file}: {e}")

    return counts


def find_best_column(columns, keywords):
    """
    Finds the column with the most keyword matches.
    """
    best_column = None
    best_score = 0

    for column in columns:
        name = column.lower()

        score = sum(
            1
            for keyword in keywords
            if keyword in name
        )

        if score > best_score:
            best_score = score
            best_column = column

    return best_column


def guess_product_columns(column_counts):
    """
    Returns likely columns:
    {
        "sku": "...",
        "product_name": "...",
        "description": "..."
    }
    """

    columns = list(column_counts.keys())

    return {
        "sku": find_best_column(
            columns,
            [
                "manufacturer sku",
                "sku",
                "catalog",
                "catalog number",
                "cat",
                "part id",
                "product id",
                "item number",
            ],
        ),

        "product_name": find_best_column(
            columns,
            [
                "product name",
                "product",
                "name",
                "title",
                "item name",
            ],
        ),

        "description": find_best_column(
            columns,
            [
                "description",
                "desc",
                "summary",
                "details",
                "information",
            ],
        ),
    }



def create_product_index_cache(
    products_dir,
    cache_path,
    sku_column,
    product_name_column,
    description_column,
    progress_callback=None,
    config_path = None,
):

    if config_path:
        progress_callback("Retrieving trademark names...", 0)

        save_trademark_names(products_dir, config_path)

    cache_path = Path(cache_path)

    # Create cache folder if missing
    cache_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if progress_callback:
        progress_callback("Building product map...", 1)

    product_map = build_product_map(
        products_dir,
        sku_column,
        product_name_column,
        description_column,
    )

    if progress_callback:
        progress_callback("Building alias map...", 2)

    alias_map = build_alias_map(
        product_map
    )

    if progress_callback:
        progress_callback("Building shortened SKU map...", 3)

    shortened_sku_map = build_shortened_sku_map(
        product_map
    )

    if progress_callback:
        progress_callback("Saving cache...", 4)

    cache = {
        "product_map": product_map,
        "alias_map": alias_map,
        "shortened_sku_map": shortened_sku_map,
    }

    with open(cache_path, "wb") as f:
        msgpack.pack(
            cache,
            f,
            use_bin_type=True
        )

    if progress_callback:
        progress_callback("Done!", 5)


def load_product_index_cache(cache_path):

    cache_path = Path(cache_path)

    if not cache_path.exists():
        return None

    with open(cache_path, "rb") as f:
        cache = msgpack.unpack(
            f,
            raw=False
        )

    return cache



trademark_symbols = ["™", "®"]
excluded_trademarks = ["SYBR®"]

def save_trademark_names(products_dir, config_path):
    """
    Adds trademark names data structrure to config .json

    Assumes config exists
    """

    with open(
        config_path,
        "r",
        encoding="utf-8"
    ) as f:
        config = json.load(f)


    product_col = config["product_columns"]["product_name"]

    df = create_df(products_dir)
    
    pattern = rf"(\S+(?:{'|'.join(map(re.escape, trademark_symbols))}))"

    trademarks = df[product_col].str.extract(pattern, expand=False)

    trademarks = set(trademarks.dropna())

    filtered_trademarks = []

    for trademark in trademarks:
        for exclude in excluded_trademarks:
            if normalize_for_matching(trademark) != normalize_for_matching(exclude):
                filtered_trademarks.append(trademark)

    print(f"{len(filtered_trademarks)} trademarks: {filtered_trademarks}")

    config["trademark_names"] = filtered_trademarks

    print(filtered_trademarks)

    with open(
        config_path,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            config,
            f,
            indent=4
        )


def load_trademark_names(config_path):

    with open(
            config_path,
            "r",
            encoding="utf-8"
        ) as f:
            config = json.load(f)

    trademark_names = config.get("trademark_names", [])

    print(trademark_names)

    return trademark_names




if __name__ == "__main__":
    # create_product_index_cache(
    #     products_dir = "data/raw_products",
    #     cache_path = "tests/cache/product_index.msgpack",
    #     sku_column = "Part ID",
    #     product_name_column = "Product Name",
    #     description_column = "Description",
    # )

    # print("created_cache")

    print("start load")

    cache = load_product_index_cache("tests/cache/product_index.msgpack")

    print("end load")

    product_map = cache["product_map"]
    alias_map = cache["alias_map"]
    shortened_sku_map = cache["shortened_sku_map"]

    print(len(product_map))
    print(len(alias_map))
    print(len(shortened_sku_map))