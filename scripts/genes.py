from urllib.parse import _ResultMixinStr

import pandas as pd

df = pd.read_csv("data/cleaned_products/all_genes.csv", encoding="utf-8-sig", low_memory=False)

print(f"Length of file: {len(df)}")
print(f"Num Unique Accession Numbers: {len(df['Accession Number'].unique())}")

mask = df['Accession Number'].isna()
accession_missing = df[mask]
accession_present = df[~mask]

print(f"Num Missing Accession Numbers: {len(accession_missing)}")

# print(accession_missing.head(5))
# print(accession_missing.tail(5))

merged = pd.merge(accession_missing, accession_present[['Gene']], on='Gene', how='left', indicator=True)
unique_accession_missing = merged[merged['_merge'] == 'left_only'].drop(columns='_merge')

unique_accession_present = accession_present.drop_duplicates()

print(len(unique_accession_missing))
print(len(unique_accession_present))

# print(unique_accession_missing)
# print(unique_accession_present)

unique = pd.concat([unique_accession_missing, unique_accession_present], ignore_index=True).reset_index(drop=True)

print(len(unique))
print(unique)

unique.to_csv('data/cleaned_products/genes.csv', encoding='utf-8', index=False)