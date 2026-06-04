"""
XML parsing layer for PubMed and Europe PMC (JATS format).

Converts raw XML into structured sections:
[
    {
        "section": str,
        "text": str
    }
]

Does NOT:
- split sentences
- normalize text
- run NLP or matching
"""


from lxml import etree
from typing import List, Dict


def parse_article_xml(xml_text: str) -> list[dict]:
    """
    Detect XML type and route to correct parser.

    Supports:
    - PubMedArticle (abstract-level XML)
    - article (PMC / Europe PMC full text JATS XML)

    Returns:
        List of section dictionaries with raw extracted text.
    """

    root = etree.fromstring(xml_text.encode("utf-8"))

    tag = etree.QName(root).localname

    # -----------------------------
    # PubMed direct article
    # -----------------------------
    if tag == "PubmedArticle":
        return parse_pubmed_xml(root)

    # -----------------------------
    # PMC / Europe PMC single article
    # -----------------------------
    if tag == "article":
        return parse_pmc_xml(root)

    # -----------------------------
    # PMC / Europe PMC wrapper (IMPORTANT FIX)
    # -----------------------------
    if tag in {"pmc-articleset", "pmc-articleSet", "articleSet"}:
        articles = root.xpath(".//article")

        sections = []
        for article in articles:
            sections.extend(parse_pmc_xml(article))

        return sections

    raise ValueError(f"Unsupported XML format: {tag}")


def parse_pubmed_xml(root) -> List[Dict]:
    """
    Extract title + abstract sections from PubMed XML.

    PubMed XML is shallow (no full text), so we only extract:
    - ArticleTitle
    - AbstractText
    """

    sections = []

    for node in root.xpath(".//ArticleTitle"):
        text = clean(node)
        if text:
            sections.append({"section": "title", "text": text})

    for node in root.xpath(".//AbstractText"):
        text = clean(node)
        if text:
            sections.append({"section": "abstract", "text": text})

    return sections


def parse_pmc_xml(root) -> List[Dict]:
    """
    Extract structured full-text sections from JATS XML.

    Each <sec> block is treated as a section.
    Section titles are normalized to lowercase.
    """

    sections = []

    for sec in root.xpath(".//body//sec"):
        title = sec.find("title")

        section_name = (
            clean(title).lower()
            if title is not None
            else "unknown"
        )

        text = clean(sec)

        if text:
            sections.append({
                "section": section_name,
                "text": text
            })

    return sections


def clean(node) -> str:
    """
    Extract and normalize all text from an XML node.

    Flattens nested tags, removes extra whitespace,
    and returns a clean single string for downstream processing.
    """

    if node is None:
        return ""

    return " ".join(
        t.strip()
        for t in node.itertext()
        if t and t.strip()
    ).strip()

