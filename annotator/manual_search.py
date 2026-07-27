import pandas as pd
from pathlib import Path


def create_df(csv_dir):
    dfs = []

    for file in Path(csv_dir).glob("*.csv"):
        df = pd.read_csv(file, encoding="utf-8-sig", low_memory=False, dtype = str,)
        df["Source File"] = file.name
        dfs.append(df)

    if not dfs:
        return pd.DataFrame()

    combined_df = pd.concat(dfs, ignore_index=True)
    combined_df.fillna("", inplace=True)

    return combined_df



def search(df, keyword, column):
    if column not in df.columns:
        return df.iloc[0:0]

    results = df[
        df[column].str.contains(
            keyword,
            case=False,
            na=False,
            regex=False
        )
    ]

    return results



def search_all(df, keyword):
    results = df[
        df.apply(
            lambda s: s.str.contains(
                keyword,
                case=False,
                na=False,
                regex=False,
            )
        ).any(axis=1)
    ]

    return results
