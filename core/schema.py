"""
core/schema.py

Defines the canonical biotech product schema and provides
enforcement utilities to guarantee consistent structure across
all vendor CSV inputs.

This prevents downstream failures in matcher.py caused by:
- inconsistent column names
- DataFrame-in-cell issues (e.g., aliases becoming DataFrames)
- mixed string/list types
"""

# =============================
# CANONICAL SCHEMA KEYS
# =============================

CANONICAL_FIELDS = [
    "product_name",
    "aliases",
    "sku",
    "manufacturer",
    "bio_targets"
]

# =============================
# CANONICAL NAMES TO KEEP
# =============================

CANONICAL_TO_KEEP = [
    "product_name",
    "aliases",
    "sku",
    "manufacturer",
    "bio_targets",
    "product_type",
    "application"
]

# =============================
# COLUMN MAPPING (RAW → CANONICAL)
# =============================

COLUMN_MAP = {
    # core identity
    "Product Name": "product_name",
    "Alias": "aliases",
    "Alias Names": "aliases",
    "Symbol": "aliases",

    "Manufacturer": "manufacturer",
    "Manufacturer SKU": "sku",
    "Part ID": "sku",
    "Part ID.1": "sku",
    "crispr_product_id": "sku",

    # biological context
    "Gene Name": "bio_targets",
    "Gene ID": "bio_targets",
    "Uniprot": "bio_targets",
    "NCBI Accession": "bio_targets",
    "Acession Number": "bio_targets",
    "Gene Species": "bio_targets",
    "Species": "bio_targets",
    "Species Reactivity": "bio_targets",
    "Target Species": "bio_targets",

    # product type / classification
    "Category": "product_type",
    "category": "product_type",
    "Subcategory": "product_type",
    "Clonality": "product_type",
    "Isotype": "product_type",
    "Conjugate": "product_type",
    "Host": "product_type",
    "Expression System": "product_type",
    "Recombinant": "product_type",
    "Vector": "product_type",
    "Promoter": "product_type",
    "Selection Marker": "product_type",

    # experimental context
    "Application": "application",
    "Immunogen": "application",

    # physical / metadata (optional keepers)
    "Size": "size",
    "Size1": "size",
    "Size2": "size",
    "Length(bp)": "size",
    "ORF LEN": "size",

    "Storage condition": "storage",
    "Shipping condition": "shipping",

    # links (optional but useful)
    "Product URL": "product_url",
    "Datasheet URL": "datasheet_url",
    "MSDS page": "msds_url",
    "User manual page": "manual_url",
    "Image URL": "image_url",
}

# print(len(COLUMN_MAP.keys()))