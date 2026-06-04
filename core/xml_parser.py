from lxml import etree


def parse_article_xml(xml_text: str) -> list[dict]:
    """
    Detect article type and return normalized sections.

    Returns:
    [
        {
            "section": str,
            "text": str
        }
    ]
    """

    root = etree.fromstring(xml_text.encode("utf-8"))

    tag = etree.QName(root).localname

    if tag == "PubmedArticle":
        return parse_pubmed_xml(root)

    if tag == "article":
        return parse_pmc_xml(root)

    raise ValueError(f"Unsupported XML format: {tag}")


# =========================================================
# PubMed XML
# =========================================================

def parse_pubmed_xml(root) -> list[dict]:
    sections = []

    # Title
    for node in root.xpath(".//ArticleTitle"):
        text = clean_xml_text(node)

        if text:
            sections.append({
                "section": "title",
                "text": text
            })

    # Abstract
    for node in root.xpath(".//AbstractText"):
        text = clean_xml_text(node)

        if text:
            label = node.get("Label")

            sections.append({
                "section": (
                    f"abstract:{label.lower()}"
                    if label
                    else "abstract"
                ),
                "text": text
            })

    return sections


# =========================================================
# PMC / EuropePMC JATS XML
# =========================================================

def parse_pmc_xml(root) -> list[dict]:
    sections = []

    # Article title
    for node in root.xpath(".//article-title"):
        text = clean_xml_text(node)

        if text:
            sections.append({
                "section": "title",
                "text": text
            })

    # Abstract
    for node in root.xpath(".//abstract"):
        text = clean_xml_text(node)

        if text:
            sections.append({
                "section": "abstract",
                "text": text
            })

    # Body sections
    for sec in root.xpath(".//body//sec"):

        title_node = sec.find("title")

        if title_node is not None:
            section_name = clean_xml_text(title_node).lower()
        else:
            section_name = "unknown"

        text = clean_xml_text(sec)

        if text:
            sections.append({
                "section": section_name,
                "text": text
            })

    return sections


# =========================================================
# Helpers
# =========================================================

def clean_xml_text(node) -> str:
    """
    Flatten XML node into readable text.
    """

    text = " ".join(
        t.strip()
        for t in node.itertext()
        if t and t.strip()
    )

    return " ".join(text.split())