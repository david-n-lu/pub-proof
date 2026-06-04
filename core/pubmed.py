"""
PubMed / PMC retrieval layer.

Responsibilities:
- Search PubMed for PMIDs
- Convert PMID → PMCID
- Fetch PMC full-text XML

Does NOT:
- parse XML
- extract text
- run NLP
"""


import requests


def search_pubmed(
    query,
    max_results=20
):
    """
    Search PubMed and return a list of PMIDs.
    """

    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": max_results
    }

    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json()["esearchresult"]["idlist"]

    except Exception as e:
        print(f"[PubMed search error] {e}")
        return []



def pmid_to_pmcid(pmid: str):
    """
    Convert PMID to PMCID using NCBI ID converter.
    """

    url = "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"

    params = {
        "format": "json",
        "ids": pmid
    }

    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()

        records = r.json().get("records", [])
        if not records:
            return None

        return records[0].get("pmcid")

    except Exception as e:
        print(f"[PMID→PMCID error] {e}")
        return None



def fetch_pmc_xml_from_pmcid(pmcid: str):
    """
    Fetch raw PMC XML using PMCID.
    """

    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    params = {
        "db": "pmc",
        "id": pmcid,
        "retmode": "xml"
    }

    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.text

    except Exception as e:
        print(f"[PMC fetch error] {e}")
        return None


def fetch_pubmed_xml(pmid: str):
    """
    Fetch raw PMC XML from a PMID.

    Flow:
    PMID → PMCID → PMC XML (raw)

    Returns:
        Raw XML string or None if unavailable.
    """

    pmcid = pmid_to_pmcid(pmid)

    if not pmcid:
        print(f"No PMCID found for PMID {pmid}")
        return None

    return fetch_pmc_xml_from_pmcid(pmcid)
