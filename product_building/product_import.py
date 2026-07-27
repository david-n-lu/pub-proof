from collections import Counter
from pathlib import Path

import pandas as pd
import msgpack

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
):

    cache_path = Path(cache_path)

    # Create cache folder if missing
    cache_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if progress_callback:
        progress_callback("Building product map...", 0)

    product_map = build_product_map(
        products_dir,
        sku_column,
        product_name_column,
        description_column,
    )

    if progress_callback:
        progress_callback("Building alias map...", 1)

    alias_map = build_alias_map(
        product_map
    )

    if progress_callback:
        progress_callback("Building shortened SKU map...", 2)

    shortened_sku_map = build_shortened_sku_map(
        product_map
    )

    if progress_callback:
        progress_callback("Saving cache...", 3)

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
        progress_callback("Done!", 4)


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