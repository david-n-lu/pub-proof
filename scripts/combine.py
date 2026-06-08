import pandas as pd
from pathlib import Path

csv_folder = "data/raw_products"

combined_df = pd.concat(
    [pd.read_csv(file, encoding='cp1252', low_memory=False) for file in Path(csv_folder).glob("*.csv")],
    ignore_index=True
)

combined_df.to_csv("data/cleaned_products/combined.csv", index=False, encoding = "utf-8-sig")

print(f"Combined {len(combined_df)} rows into combined.csv")