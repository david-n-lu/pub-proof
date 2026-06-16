import requests

pmcid = "PMC12450569"  # Replace with your PMCID

url = (
    "https://www.ebi.ac.uk/europepmc/webservices/rest/"
    f"search?query=PMCID:{pmcid}&format=json"
)

response = requests.get(url)
response.raise_for_status()

data = response.json()

results = data.get("resultList", {}).get("result", [])

if not results:
    print("No results found.")
else:
    record = results[0]
    print("Keys:")
    for key in sorted(record.keys()):
        print(f"{key}: {record.get(key)}")