"""
citation.py

End-to-end academic citation pipeline:

Europe PMC (PMID/PMCID) → DOI → Crossref metadata → APA 7 citation

Design goals:
- Minimal dependencies (only requests)
- Clear separation of concerns
- Easy to plug into larger biotech / literature pipelines
"""

import requests
import re
import html
from matching.normalization import shorten_product_name


# ============================================================
# GeneCopoeia Citation Format given Europe PMC 
# ============================================================
"""
Creates citations like:
Liu, B., et al. (2026). Estrogen upregulates NR4A1 to counter TGF beta induced pulmonary fibrosis therapeutic insights for IPF. iScience DOI: \\
10.1016/j.isci.2026.114756 [Lentifect™ Lentiviral particles expressing Mouse Nr4a1 and scrambled control, Cat. No. LPP-Mm03063-Lv201-100, \\
LPP-MSH197809-LVRU6GP-500, LP146-100; RNAzol® RT RNA Isolation Reagent, Cat. No. QP020; SureScript™ First-Strand cDNA Synthesis Kit, Cat. \\
No. QP056; BlazeTaq™ SYBR Green qPCR Mix 2.0 (with ROX), Cat. No. QP031]
"""

def get_citation_from_url(url, skus, products):
    """
    Creates a citation from url of publication

    SLOW
    """

    pmcid = url.rstrip("/").split("/")[-1]

    try:
        record = requests.get(
            f"https://www.ebi.ac.uk/europepmc/webservices/rest/article/PMC/PMC{pmcid}?resultType=core&format=json"
        )

        record.raise_for_status()

        record = record.json().get("result", [])

        truncated_record = {
            "pmcid": record.get("pmcid"),
            "doi": record.get("doi"),
            "title": record.get("title"),
            "journal_iso": record.get("journalInfo", {}).get("journal", {}).get("isoabbreviation"),
            "authors": record.get("authorString"),
            "year": (record.get("firstPublicationDate") or "")[:4],
        }

        # print(truncated_record)

        return get_citation(truncated_record, skus, products)

    except Exception as e:
        print(e)


def get_citation(record, skus, products):
    return get_publication_citation(record) + " " + format_products(skus, products);


def get_publication_citation(record: dict) -> str:
    """
    Format a Europe PMC metadata dictionary into a citation string.
    """

    # --- Authors ---
    authors = record.get("authors", "")

    # Optional: convert "A, B, C, D" → "A, et al." if long
    if authors and "," in authors:
        first_author = authors.split(",")[0].strip()
        authors = f"{first_author}, et al."

    # --- Core fields ---
    title = record.get("title", "").strip()
    title = clean_title(title)
    journal = record.get("journal_iso")
    year = record.get("year")

    # --- DOI handling ---
    doi = record.get("doi", "")
    if isinstance(doi, list):
        doi = doi[0] if doi else ""

    # --- Build citation ---
    citation = f"{authors} ({year}). {title}. {journal}"
    citation = citation.replace("..", ".")

    if doi:
        citation += f" DOI: {doi}"

    return citation


def clean_title(title: str) -> str:
    # convert escaped HTML like &lt;sup&gt;
    title = html.unescape(title)

    # remove actual HTML tags like <sup>, </i>, etc.
    title = re.sub(r"<[^>]+>", "", title)

    return title


def format_products(skus, products):
    """
    Takes ordered SKUs and matching ordered product names and formats them into:

    Product Name, Cat. No. SKU1, SKU2; Product Name, Cat. No. SKU3...

    Assumes skus and products are aligned with each other
    """

    parts = []

    for i in range(len(skus)):
        product = products[i]
        sku = skus[i]
        processed_product = shorten_product_name(product)
        parts.append(f"{processed_product}, Cat. No. {sku.upper()}")

    return f"[{'; '.join(parts)}]"



# ============================================================
# 1. Europe PMC → DOI extraction
# ============================================================
def get_doi_from_europe_pmc(identifier: str) -> str | None:
    """
    Fetch a DOI from Europe PMC using PMCID

    Europe PMC stores article metadata, including DOI when available.

    Args:
        identifier (number str): PMCID

    Returns:
        str | None: DOI string if found, otherwise None
    """

    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

    # Query Europe PMC by external identifier
    params = {
        "query": f"PMC:{identifier}",
        "format": "json"
    }

    # Request metadata
    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()

    data = response.json()

    # Extract result list safely
    results = data.get("resultList", {}).get("result", [])

    if not results:
        return None

    # DOI is directly stored in result metadata
    return results[0].get("doi")


# ============================================================
# 2. Crossref metadata fetch
# ============================================================
def get_crossref_metadata(doi: str) -> dict:
    """
    Fetch full bibliographic metadata from Crossref using DOI.

    Crossref provides structured publication data:
    - title
    - authors
    - journal (container-title)
    - year
    - volume/issue/pages
    - DOI

    Args:
        doi (str): Digital Object Identifier

    Returns:
        dict: Crossref metadata JSON
    """

    url = f"https://api.crossref.org/works/{doi}"

    response = requests.get(url, timeout=20)

    if response.status_code == 404:
        return None  # fallback trigger
    
    response.raise_for_status()

    return response.json()["message"]


# ============================================================
# 3. APA formatting
# ============================================================
def format_apa(metadata: dict) -> str:
    """
    Convert Crossref metadata into APA 7th edition citation.

    Args:
        metadata (dict): Crossref 'message' object

    Returns:
        str: formatted APA citation
    """

    # -----------------------------
    # Author formatting
    # -----------------------------
    authors = metadata.get("author", [])

    # Format: Lastname Firstname
    formatted_authors = [
        f"{a.get('family','')} {a.get('given','')}".strip()
        for a in authors
    ]

    # APA rule: max 3 authors before et al.
    if len(formatted_authors) > 3:
        author_str = ", ".join(formatted_authors[:3]) + ", et al."
    else:
        author_str = ", ".join(formatted_authors)

    # -----------------------------
    # Article metadata
    # -----------------------------
    title = metadata.get("title", [""])[0]
    journal = metadata.get("container-title", [""])[0]

    # Extract year safely from nested structure
    year = metadata.get("issued", {}).get("date-parts", [[None]])[0][0]

    doi = metadata.get("DOI", "")

    # -----------------------------
    # APA format assembly
    # -----------------------------
    return (
        f"{author_str} ({year}). "
        f"{title}. "
        f"{journal}. "
        f"https://doi.org/{doi}"
    )


# ============================================================
# 4. Full pipeline helper
# ============================================================
def cite_from_europe_pmc(identifier: str) -> str | None:
    """
    End-to-end citation pipeline:

    Europe PMC ID → DOI → Crossref → APA citation

    Args:
        identifier (str): PMID / PMCID / EXT_ID

    Returns:
        str | None: APA citation or None if DOI not found
    """

    # Step 1: get DOI from Europe PMC
    doi = get_doi_from_europe_pmc(identifier)

    if not doi:
        return None

    # Step 2: fetch metadata from Crossref
    metadata = get_crossref_metadata(doi)

    if not metadata:
        return None

    # Step 3: format APA citation
    return format_apa(metadata)


# ============================================================
# Optional: quick test
# ============================================================

def test():
    test_id = "12309011"  # replace with real PMID/PMCID
    citation = cite_from_europe_pmc(test_id)

    print("APA Citation:\n")
    print(citation)


if __name__ == "__main__":
    test()