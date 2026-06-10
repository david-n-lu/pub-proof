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