from pathlib import Path
import pandas as pd


def get_product_names(csv_dir, column_name, top_n = 10):
    csv_dir = Path(csv_dir)

    csv_files = list(csv_dir.glob("*.csv"))

    products = {}

    for file_path in csv_files:
        df = pd.read_csv(file_path, encoding='utf-8-sig', low_memory=False)

        for _, row in df.iterrows():
            entry = row.get(column_name)

            if not entry or pd.isna(entry):
                continue
            
            if entry not in products:
                products[entry] = 0
            
            products[entry] += 1

    print(f"{len(products)} product names")

    products = dict(sorted(products.items(), key=lambda item: item[1], reverse=True))

    for key, value in list(products.items())[:top_n]:
        print(f"{key}: {value}")


if __name__ == "__main__":
    csv_dir = "data/raw_products"

    column_name = "Product Name"
    
    get_product_names(csv_dir, column_name)
