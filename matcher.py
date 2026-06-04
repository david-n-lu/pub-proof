"""
matcher.py

Searches text for manufacturer's product

Gets context where manufacturer is mentioned
Gets evidence of product name mentioned in same context as manufacturer
Gets evidence of product name alternative names mentioned in same context as manufacturer
- requires "product_name_clean" and "aliases" columns in clean_products.csv
"""

import pandas as pd
import re
from core.text_normalization import normalize_biotech_text
from core.schema import CANONICAL_FIELDS


# def find_string_context(text, string, n = 1):
#     if n < 1 or n % 2 == 0:
#         raise ValueError("n must be odd and >= 1")

#     # Simple sentence splitter for MVP
#     sentences = re.split(r'(?<=[.!?])\s+', text)

#     radius = n // 2
#     contexts = []

#     for i, sentence in enumerate(sentences):
#         if string.lower() in sentence.lower():
#             start = max(0, i - radius)
#             end = min(len(sentences), i + radius + 1)

#             contexts.append({
#                 "sentence_index": i,
#                 "context": " ".join(sentences[start:end])
#             })

#     return contexts

def find_string_context(text, string, n=1, character_radius=200):
    """
    Finds context windows surrounding occurrences of a target string.

    Workflow:
    1. Split text into sentences
    2. Find sentences containing the target string
    3. Expand to an n-sentence context window
    4. Trim the context to a fixed character radius around the
       leftmost and rightmost string matches

    This produces compact evidence snippets that retain nearby
    information while removing unrelated text.

    Parameters:
        text (str):
            Full document or article text.

        string (str):
            Search term (case-insensitive).

        n (int):
            Number of sentences in the context window.
            Must be odd and >= 1.

        character_radius (int):
            Number of characters to preserve on each side of the
            matched region.

    Returns:
        list[dict]:
            Each dictionary contains:
            - sentence_index
            - context
    """

    # ----------------------------
    # 1. Validate context window size
    # ----------------------------
    if n < 1 or n % 2 == 0:
        raise ValueError("n must be odd and >= 1")

    # ----------------------------
    # 2. Split document into sentences
    # ----------------------------
    # Simple sentence splitter for MVP.
    # Can be upgraded later with spaCy, NLTK, etc.
    sentences = re.split(r'(?<=[.!?])\s+', text)

    radius = n // 2
    contexts = []

    # ----------------------------
    # 3. Find matching sentences
    # ----------------------------
    for i, sentence in enumerate(sentences):

        if string.lower() not in sentence.lower():
            continue

        # ----------------------------
        # 4. Build sentence-level context window
        # ----------------------------
        start_idx = max(0, i - radius)
        end_idx = min(len(sentences), i + radius + 1)

        context_text = " ".join(sentences[start_idx:end_idx])

        if character_radius > 0:
            # ----------------------------
            # 5. Find first and last occurrences within context
            # ----------------------------
            leftmost = context_text.lower().find(string.lower())
            rightmost = context_text.lower().rfind(string.lower())

            # print("leftmost:", leftmost, "rightmost", rightmost)

            # ----------------------------
            # 6. Trim around leftmost and
            #    rightmost occurrences
            # ----------------------------
            if leftmost and rightmost:
                
                left_bound = max(0, 
                                 leftmost - character_radius)
                right_bound = min( len(context_text), 
                                  len(string) + rightmost + character_radius)
                
                # print("left_bound:", left_bound, "right_bound", right_bound)
                
                context_text = context_text[left_bound:right_bound]

        # ----------------------------
        # 7. Store evidence snippet
        # ----------------------------
        contexts.append({
            "sentence_index": i,
            "context": context_text
        })

    return contexts


def find_manufacturer_contexts(text, manufacturer, n = 1):
    return find_string_context(text, manufacturer, n)

def find_product_name_contexts(text, product_name, n = 1):
    return find_string_context(text, product_name, n)

def find_catalog_number_contexts(text, catalog_number, n = 1):
    return find_string_context(text, catalog_number, n)



def build_product_alias_map(df):
    """

    Builds a canonical → alias-set mapping for product entity resolution.

    Key idea:
    - Uses CANONICAL_FIELDS to decide what to include
    - Automatically excludes 'manufacturer'
    - Produces a unified set of searchable terms per product

    Output structure:
        {
            product_name_clean: {
                product_name
                alias_1,
                alias_2,
                ...
                sku,
                bio_targets
            }
        }

    Expected input:
        df with at least:
        - product_name_clean
        - aliases (optional, pipe-delimited string)

    Returns:
        dict[str, set[str]]: canonical name → set of normalized aliases
    """
    
    key_name = "sku"
    df["smallest"] = df[key_name].str.split(" ").apply(lambda x: min(x, key=len))
    keys = df["smallest"].tolist()

    value_cols = list(CANONICAL_FIELDS)
    exclude_cols = ["manufacturer"]

    value_cols = [item for item in value_cols if item not in exclude_cols]
    values = (df[value_cols].astype(str).apply(' '.join, axis=1)).tolist()
    values = [list(set(string.split())) for string in values]

    exclude_values = ["human", "rat", "mouse", "rabbit"]
    exclude_values = set(exclude_values)
    values = [[item for item in sublist if item not in exclude_values] for sublist in values]

    # print(len(keys))
    # print(len(values))

    product_map = dict(zip(keys, values))

    return product_map


def find_product_manufacturer_evidence(
    text,
    sku,
    product_map,
    manufacturer,
    n=1
):
    """
    Finds evidence sentences linking a specific product to a manufacturer.

    Parameters:
        text (str):
            Full article text

        product_name (str):
            Canonical product name to search for.
            Must exist as a key in product_map.

        product_map (dict):
            Output of build_product_alias_map()

        manufacturer (str):
            Manufacturer name used to anchor context search

        n (int):
            Context window size passed to find_manufacturer_contexts()

    Returns:
        list[str]:
            Sentences containing both the manufacturer and
            at least one alias of the specified product.
    """

    # ----------------------------
    # 1. Retrieve aliases for product
    # ----------------------------
    sku = normalize_biotech_text(sku)
    alias_set = product_map.get(sku)

    if not alias_set:
        return []

    # ----------------------------
    # 2. Find manufacturer contexts
    # ----------------------------
    manufacturer_contexts = find_manufacturer_contexts(
        text,
        manufacturer,
        n
    )

    evidence = []

    for context in manufacturer_contexts:
        context_text = context["context"]
        context_normalized = normalize_biotech_text(context_text)

        # print(context_normalized)

        # ----------------------------
        # 3. Check all aliases
        # ----------------------------
        for alias in alias_set:
            alias_normalized = normalize_biotech_text(alias)

            if re.search(
                r"\b" + re.escape(alias_normalized) + r"\b",
                context_normalized
            ):
                evidence.append(context_text.strip())

                # only need one alias hit
                break

    return evidence

