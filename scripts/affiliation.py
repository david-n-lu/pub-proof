import requests

def get_author_affiliations(pmcid):
    # Europe PMC RESTful API URL for article profile details
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

    params = {
        "query": f"PMCID:{pmcid}",
        "resultType": "core",
        "format": "json",
        "pageSize": 1,
    }

    r = requests.get(url, params=params)
    r.raise_for_status()

    data = r.json()

    result = data["resultList"]["result"][0]

    # print(result.keys())
    # for key, value in result.items():
    #     print(key+":", value)

    print(result["affiliation"])
    print(result["authorList"])


# Example usage with a PubMed Central ID
get_author_affiliations("PMC13237798")