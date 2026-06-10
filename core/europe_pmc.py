"""
Europe PMC retrieval layer.

Responsibilities:
- Search Europe PMC
- Fetch full-text XML

Does NOT:
- extract text
- parse XML
- run NLP
"""

import requests


def search_europe_pmc(
    query,
    page_size=25
):
    """
    Search Europe PMC and return article metadata results.
    """

    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

    params = {
        "query": query,
        "format": "json",
        "pageSize": page_size
    }

    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json().get("resultList", {}).get("result", [])

    except Exception as e:
        print(f"[Europe PMC search error] {e}")
        return []
    

def get_europe_pmc_abstract(ext_id: str):
    """
    Fetch abstract text from Europe PMC using external ID.
    """

    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

    params = {
        "query": f"EXT_ID:{ext_id}",
        "format": "json",
        "resultType": "core"
    }

    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()

        results = r.json().get("resultList", {}).get("result", [])
        if not results:
            return None

        return results[0].get("abstractText")

    except Exception as e:
        print(f"[Europe PMC abstract error] {e}")
        return None


def fetch_europe_pmc_xml(pmcid: str):
    """
    Fetch raw full-text XML from Europe PMC using PMCID.

    This function only retrieves raw XML and does NOT parse or extract text.
    """

    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"

    try:
        r = requests.get(url, timeout=30)

        if r.status_code != 200:
            return None

        return r.text

    except Exception as e:
        print(f"[Europe PMC XML fetch error] {e}")
        return None


"""
Search Europe PMC for articles mentioning a specific product
- input: product_name, catalog_number, manufacturer
- output: articles mentioning the product
"""

import requests
from core.xml_to_text import extract_full_text_from_xml

def search_europe_pmc(query, page_size=25):
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


    params = {
        "query": query,
        "format": "json",
        "pageSize": page_size
    }

    r = requests.get(url, params=params)
    r.raise_for_status()

    data = r.json()
    return data["resultList"]["result"]


def get_europe_pmc_abstract(pmid: str):
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

    params = {
        "query": f"EXT_ID:{pmid}",
        "format": "json",
        "resultType": "core"
    }

    try:
        response = requests.get(url, params = params, timeout=30)
        response.raise_for_status()

    except Exception as e:
        print(type(e))
        print(e)

    data = response.json()

    results = data.get("resultList", {}).get("result", [])

    if not results:
        return None

    return results[0].get("abstractText")


def fetch_europe_pmc_full_text(pmcid):
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"

    response = requests.get(url)
    
    if response.status_code != 200:
        return None

    return extract_full_text_from_xml(response.text)


def fetch_europe_pmc_xml(pmcid):
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"

    response = requests.get(url)
    
    if response.status_code != 200:
        return None

    return response.text