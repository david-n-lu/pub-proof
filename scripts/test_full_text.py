from core.europe_pmc import fetch_europe_pmc_full_text

# pmcid = "PMC8170267"
pmcid = "PMC3288107"
full_text = fetch_europe_pmc_full_text(pmcid)
print(full_text)