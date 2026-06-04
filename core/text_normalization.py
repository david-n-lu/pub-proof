"""
core/text_normalization.py

Text normalization and cleaning utilities for biotech product data ingestion.

This module contains reusable functions for:
- Fixing encoding issues (mojibake, e.g. "â„¢" → "™")
- Normalizing product-related text fields across heterogeneous vendor CSVs
- Extracting canonical product names from noisy catalog strings
- Preparing structured fields for downstream matching and entity resolution

Key responsibilities:
- Repair malformed Unicode caused by inconsistent CSV encodings
- Standardize product names, aliases, and manufacturer strings
- Remove non-informative metadata (e.g. packaging sizes, reaction counts)
- Produce matcher-friendly representations of product data

Design principle:
This module operates at the "text normalization layer" of the pipeline.
It should NOT perform:
- File I/O or CSV loading/saving
- Schema mapping or database operations
- Matching/scoring logic

Those responsibilities belong to:
- scripts/clean_products.py (pipeline orchestration)
- core/schema.py (data structure definitions)
- core/matcher.py (entity matching logic)

All functions in this module are designed to be deterministic, stateless,
and reusable across different data sources (CSV, PubMed, EuropePMC, etc.).
"""

import re
import pandas as pd

from core.schema import CANONICAL_FIELDS


# ----------------------------
# 1. MOJIBAKE FIX
# ----------------------------
def fix_mojibake(text: str):
    if not isinstance(text, str):
        return text
    try:
        return text.encode("latin1").decode("utf-8")
    except Exception:
        return text


# ----------------------------
# 2. CORE PRODUCT NAME EXTRACTION
# ----------------------------
def extract_core_product_name(text: str) -> str:
    text = str(text)

    # remove trailing parenthetical noise
    text = re.sub(r"\s*\([^)]*\)\s*$", "", text)

    # remove trailing descriptors after comma
    text = re.sub(r",.*$", "", text)

    # normalize whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ----------------------------
# 3. BIOTECH NORMALIZATION
# ----------------------------
def normalize_biotech_text(text: str) -> str:
    text = str(text).lower()

    # fix encoding issues first
    text = fix_mojibake(text)

    # remove trademark symbols (safe for matching)
    text = text.replace("™", "")
    text = text.replace("®", "")
    text = text.replace("©", "")

    # normalize µ variants (very common in biotech)
    text = text.replace("µl", "ul")
    text = text.replace("μl", "ul")

    # collapse whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()
