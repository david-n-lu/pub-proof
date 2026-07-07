from pathlib import Path
import pandas as pd
from matching.normalization import get_shortened_sku, normalize_for_matching

def get_product_names(csv_dir, column_name, top_n = 10):
    csv_dir = Path(csv_dir)

    csv_files = list(csv_dir.glob("*.csv"))

    products = set()

    for file_path in csv_files:
        df = pd.read_csv(file_path, encoding='utf-8-sig', low_memory=False)

        for _, row in df.iterrows():
            entry = row.get(column_name)

            if not entry or pd.isna(entry):
                continue
            
            products.add(entry)

    products = [p for p in products if "old cat" in normalize_for_matching(p)]

    print(f"Number of products with old SKUs: {len(products)}")

    replace = ["-025-c", "-100-c", "-100", "-200", "-15-10-h-50", "-15-10-b-50", "-15-10-i-50", "-15-10-m-50", "-15-10-a-50", "-50"
               "-025", "-15-10-d-50", "-400", "-15-10-o-50", "-a00", "-400-c", "-15-10-l-50", "-15-10-n-50", "-15-10-j-50",
               "-15-10-k-50", "-025", "-15-10-g-50", "-a00-c", "-1-a00", "-01-025-c", "-1-50-a00", "-15-10-c-50", "-200c"
               , "-01-100-c", "-050", "-8-100-c", "-200-c", "-09-100-c", "-02-100-c"]
    replace = sorted(replace, key=len, reverse = True)

    for product in products:
        product_norm = normalize_for_matching(product)
        sku = product_norm.split("old cat")[-1].strip()
        short = get_shortened_sku(sku)
        
        print(f"{short}: \t\t\t\t{sku}")


if __name__ == "__main__":
    csv_dir = "data/raw_products"

    column_name = "Product Name"
    
    get_product_names(csv_dir, column_name)