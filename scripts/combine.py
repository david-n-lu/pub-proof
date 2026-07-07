import pandas as pd
from pathlib import Path

csv_folder = "data/raw_products"

csv_folder = "data/raw_products"

dfs = []

for file in Path(csv_folder).glob("*.csv"):
    df = pd.read_csv(file, encoding="utf-8-sig", low_memory=False)
    df["Source File"] = file.name  # or file.stem to omit ".csv"
    dfs.append(df)

combined_df = pd.concat(dfs, ignore_index=True)

# Remove completely empty columns and rows
combined_df = combined_df.dropna(axis=1, how="all")
combined_df = combined_df.dropna(
    subset=combined_df.columns.drop("Source File"),
    how="all",
)

combined_df.to_csv(
    "data/cleaned_products/combined.csv",
    index=False,
    encoding="utf-8-sig",
)

print(f"Combined {len(combined_df)} rows into combined.csv")