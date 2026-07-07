from pathlib import Path
import pandas as pd


def build_col(csv_dir, column_name):
    csv_dir = Path(csv_dir)

    csv_files = list(csv_dir.glob("*.csv"))

    columns = []

    for file_path in csv_files:
        df = pd.read_csv(file_path, encoding='utf-8-sig', low_memory=False)

        for _, row in df.iterrows():
            entry = row.get(column_name)

            if entry and pd.notna(entry):
                columns.append(row.get(column_name))
    
    unique_cols = set()
    unique_cols.update(columns)

    print(f"{len(columns)} columns")
    print(f"{len(unique_cols)} unique columns")

    print_limit = 200
    if len(unique_cols) <= print_limit:
        print(unique_cols)

def get_col_counts(csv_dir):
    csv_dir = Path(csv_dir)

    csv_files = list(csv_dir.glob("*.csv"))

    column_stats = {}

    for file_path in csv_files:
        df = pd.read_csv(file_path, encoding='utf-8-sig', low_memory=False)

        columns = list(df.columns)
        for col in columns:
            if col not in column_stats:
                column_stats[col] = {
                    "count" : 0,
                    "values" : set(),
                    "datasets" : [],
                }
            
            column_stats[col]["datasets"].append(file_path)

        for _, row in df.iterrows():
            for col in columns:
                entry = row.get(col)
                
                if entry:
                    column_stats[col]["count"] += 1
                    column_stats[col]["values"].add(entry)

    for col, stats in column_stats.items():
        print(f"{col}: count = {stats["count"]}, num unique = {len(stats["values"])}, num files = {len(stats["datasets"])}")


if __name__ == "__main__":
    csv_dir = "data/raw_products"

    column_name = "Subcategory"
    
    # build_col(csv_dir, column_name)
    get_col_counts(csv_dir)

    build_col(csv_dir, "Subcategory")
    build_col(csv_dir, "Category")