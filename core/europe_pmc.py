"""
Search Europe PMC for articles mentioning a specific product
- input: product_name, catalog_number, manufacturer
- output: articles mentioning the product
"""

import requests
from core.utils import extract_full_text_from_xml

def search_europe_pmc(manufacturer, product_name, catalog_number = "", page_size=25):
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

    terms = []

    if manufacturer:
        terms.append(f'"{manufacturer}"')

    if product_name:
        terms.append(f'"{product_name}"')

    if catalog_number:
        terms.append(f'"{catalog_number}"')

    if not terms:
        raise ValueError("No search terms provided.")

    query = " AND ".join(terms)

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

import requests
