"""
Search PubMed PMIDs that mention a specific product
- input: product_name, catalog_number, manufacturer
- output: PMIDs

Find full text articles that mention a specific product on PMC given a PMID
- input: PMID
- throughput: PMCID
- throughput: PMC XML
- output: full text articles that mention the product
"""

import requests
from core.query_building import build_search_query
from core.xml_to_text import extract_abstract_from_xml, extract_full_text_from_xml
from core.query_building import build_search_query

def search_pubmed(manufacturer, product_name = None, catalog_number = None, terms = None, max_results=20):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

    query = build_search_query(manufacturer, product_name, catalog_number, terms)

    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": max_results
    }

    try:
        response = requests.get(url, params = params, timeout=30)
        response.raise_for_status()

    except Exception as e:
        print(type(e))
        print(e)

    data = response.json()

    return data["esearchresult"]["idlist"]


def get_pubmed_abstract(pmid):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    params = {
        "db": "pubmed",
        "id": pmid,
        "retmode": "xml"
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    return extract_abstract_from_xml(response.text)


def pmid_to_pmcid(pmid):
    url = "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"

    params = {
        "format": "json",
        "ids": pmid
    }

    r = requests.get(url, params=params)
    r.raise_for_status()

    data = r.json()

    records = data.get("records", [])
    if not records:
        return None

    return records[0].get("pmcid")


def fetch_pmc_full_text_pmcid(pmcid):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    params = {
        "db": "pmc",
        "id": pmcid,
        "retmode": "xml"
    }

    r = requests.get(url, params=params)
    r.raise_for_status()

    return r.text


def fetch_pmc_full_text(pmid):
    pmcid = pmid_to_pmcid(pmid)
    if not pmcid:
        print(f"No PMCID found for PMID {pmid}")
        return None

    full_text = fetch_pmc_full_text_pmcid(pmcid)
    full_text = extract_full_text_from_xml(full_text)
    return full_text