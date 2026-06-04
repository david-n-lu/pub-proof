"""
core/utils.py

General-purpose XML parsing and text extraction utilities for biomedical literature
and structured XML sources (e.g., PubMed, Europe PMC full-text records).

This module provides reusable helper functions for converting XML documents into
plain text representations suitable for downstream NLP, matching, and indexing.

Core functions:
- extract_xml_text(xml_text):
    Recursively extracts all text content from an XML document, flattening nested
    tags into a single plain-text string.

- extract_full_text_from_xml(xml_text):
    Extracts full-text content from Europe PMC / PMC-style XML documents.
    Intended for article-level ingestion where full-body text is available.

- extract_abstract_from_xml(xml_text):
    Extracts structured abstract sections from XML documents, preserving only
    abstract-level content for lightweight indexing and fast search.

Design notes:
- These functions prioritize completeness over formatting fidelity.
- Output is normalized to plain text (no XML tags preserved).
- They are intentionally conservative to avoid dropping text content.
- Not responsible for cleaning, normalization, or schema mapping.

Downstream responsibilities:
- core/text_normalization.py → text cleaning and normalization
- core/schema.py → canonical field mapping
- core/matcher.py → entity matching logic

Usage context:
These utilities are used across PubMed and Europe PMC ingestion pipelines
to standardize text extraction before normalization and product/entity matching.
"""

import xml.etree.ElementTree as ET


def extract_xml_text(node):
    """
    Shared helper function used by both abstract and full-text extraction.

    Why it exists:
    Biomedical XML (PMC / Europe PMC / PubMed) often splits meaningful text
    across nested tags like <b>, <i>, <td>, etc.

    Without recursive traversal, important signals can be partially or fully lost, like:
    - product names
    - manufacturer names
    - catalog numbers (SKU)

    Extracts:
    - node.text (text inside tags)
    - child nodes (recursively)
    - child.tail (text after tags)
    """

    parts = []

    if node.text and node.text.strip():
        parts.append(node.text.strip())

    for child in node:
        parts.append(extract_xml_text(child))

        if child.tail and child.tail.strip():
            parts.append(child.tail.strip())

    return " ".join(parts)


def extract_full_text_from_xml(xml_text: str) -> str:
    """
    Extract full text from XML.

    This function flattens the entire XML document into a single text string.

    Use case:
    - Searching for product usage in Methods / Results sections
    - Detecting manufacturer mentions in full papers
    - Extracting SKU / catalog number evidence

    Note:
    This does NOT preserve document structure (sections, tables, etc.).
    It prioritizes recall over formatting accuracy.
    """

    root = ET.fromstring(xml_text)
    return extract_xml_text(root)


def extract_abstract_from_xml(xml_text: str) -> str:
    """
    Extract abstract text from PubMed / PMC / Europe PMC XML.

    Abstracts are stored in <AbstractText> nodes, which may be split into
    multiple labeled sections (e.g., Background, Methods, Results).

    This function:
    - Finds all AbstractText nodes
    - Recursively extracts text within each node
    - Combines them into a single coherent string

    Use case:
    - Fast screening of papers
    - Early detection of product/manufacturer mentions
    - Fallback when full text is unavailable
    """

    root = ET.fromstring(xml_text)

    abstract_nodes = root.findall(".//AbstractText")

    parts = []
    for node in abstract_nodes:
        parts.append(extract_xml_text(node))

    return " ".join(parts)




# def xml_to_text(xml_text):
#     root = ET.fromstring(xml_text)

#     texts = []
#     for elem in root.iter():
#         if elem.text:
#             texts.append(elem.text)

#     return " ".join(texts)

# """
# Converts XML into a single plain-text string.

# Recursively extracts text while preserving:
# - nested tags (e.g., <b>, <i>, <td>)
# - inline text structure
# - tail text between XML nodes

# Note:
# This is a best-effort extraction and may not perfectly
# preserve original formatting or sentence boundaries.
# """
# def xml_to_text(xml_text):
#     root = ET.fromstring(xml_text)

#     def recurse(node):
#         parts = []

#         if node.text and node.text.strip():
#             parts.append(node.text.strip())

#         for child in node:
#             parts.append(recurse(child))

#             if child.tail and child.tail.strip():
#                 parts.append(child.tail.strip())

#         return " ".join(parts)

#     return recurse(root)


# def extract_abstract_from_xml(xml_text):
#     root = ET.fromstring(xml_text)

#     abstract_parts = []

#     for abstract_text in root.findall(".//AbstractText"):
#         if abstract_text.text:
#             abstract_parts.append(abstract_text.text)

#     return " ".join(abstract_parts)