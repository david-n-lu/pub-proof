import re
import pandas as pd
from pathlib import Path
from collections import Counter

def extract_delimiters(text):
    if pd.isna(text):
        return ""

    text = str(text)

    # Remove letters, numbers, and whitespace
    delimiters = re.sub(r"[A-Za-z0-9\s]", "", text)

    return delimiters


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


if __name__ == "__main__":
    df = load_folder_csvs("data/raw_products")

    delimiter_counts = Counter()

    for col in df.columns:
        for value in df[col]:
            delimiter_counts.update(extract_delimiters(value))

    print(delimiter_counts.most_common())