# from core.europe_pmc import fetch_europe_pmc_full_text


# # pmcid = "PMC8170267"
# pmcid = "PMC3288107"
# full_text = fetch_europe_pmc_full_text(pmcid)
# print(full_text)


import requests

url = "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12450569/fullTextXML"
r = requests.get(url)

print("STATUS:", r.status_code)
print("TEXT LENGTH:", len(r.text))
# print("RAW:", repr(r.text[:200]))

xml_text = r.text
print(xml_text)  # preview