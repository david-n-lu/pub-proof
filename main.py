"""
Biotech Literature Mining MVP

Purpose:
    Identify scientific publications that mention a biotech product and
    extract supporting evidence from the literature.

Why:
    Biotech companies often use publication citations to demonstrate product
    credibility. This tool automates the process of finding papers that
    reference a product by name, SKU/catalog number, or manufacturer.

Pipeline:
    1. Product Input
    2. PubMed Search
    3. PMC Full-Text Retrieval
    4. Product Mention Detection
    5. Evidence Extraction
    6. Results Output
"""


from core.pubmed import fetch_pmc_full_text
from core.pubmed import search_pubmed
from core.pubmed import get_pubmed_abstract
from core.europe_pmc import search_europe_pmc
from core.europe_pmc import fetch_europe_pmc_full_text
from core.europe_pmc import get_europe_pmc_abstract
from matcher import build_product_alias_map, find_manufacturer_contexts
from matcher import find_product_manufacturer_evidence

import pandas as pd


def get_number_of_results(pmids, europe_pmc_results):
    print(f"Number of PubMed results: {len(pmids)}")
    print(f"Number of Europe PMC results: {len(europe_pmc_results)}")


def get_abstracts(pmids, europe_pmc_results):
    # Fetch abstract for each PMID and print it
    for pmid in pmids:
        print("Abstract for PMID:", pmid)
        abstract = get_pubmed_abstract(pmid)
        print(abstract)
        print("---")

    # Fetch abstract for each Europe PMC result and print it
    for r in europe_pmc_results:
        pmid = r.get("pmid")
        if not pmid:
            continue

        print("Abstract for PMCID:", pmid)
        abstract = get_europe_pmc_abstract(pmid)
        print(abstract)
        print("---")


def get_full_texts(pmids, europe_pmc_results):
    # Fetch full text for each PMID and print it
    for pmid in pmids:
        print("Full text for PMID:", pmid)
        full_text = fetch_pmc_full_text(pmid)
        print(full_text)

    # Fetch full text for each Europe PMC result and print it
    for r in europe_pmc_results:
        pmcid = r.get("pmcid")
        if not pmcid:
            continue

        # debugging
        print("isOpenAccess:", r.get("isOpenAccess"))
        print("inPMC:", r.get("inPMC"))

        print("has fullTextUrlList:", bool(r.get("fullTextUrlList")))
        print("has fullTextXml:", bool(r.get("fullTextXml")))

        # printing
        print("Full text for PMCID:", pmcid)
        full_text = fetch_europe_pmc_full_text(pmcid)
        print(full_text)


# Find and print evidence of manufacturer product mentioned in the abstracts and full texts
def find_manufacturer_in_publications(manufacturer, context_radius = 1, 
                                  pmids=None, europe_pmc_results=None):

    for pmid in pmids:
        print("Evidence for PMID:", pmid, f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/")

        abstract = get_pubmed_abstract(pmid)
        if abstract:
            print("Abstract evidence:")
            print(find_manufacturer_contexts(abstract, manufacturer, n=context_radius))
            print("---")
        else:
            print("No abstract found.")
            print("---")
        
        full_text = fetch_pmc_full_text(pmid)
        if full_text:
            print("Full text evidence:")
            print(find_manufacturer_contexts(full_text, manufacturer, n=context_radius))
            print("===")
        else:
            print("No full text found.")
            print("===")


    for r in europe_pmc_results:
        pmcid = r.get("pmcid")
        if not pmcid:
            continue

        print("Evidence for PMCID:", pmcid, f"https://europepmc.org/article/PMC/{pmcid.replace("PMC", "")}")

        abstract = get_europe_pmc_abstract(pmcid)
        if abstract:
            print("Abstract evidence:")
            print(find_manufacturer_contexts(abstract, manufacturer, n=context_radius))
            print("---")
        else:
            print("No abstract found.")
            print("---")

        full_text = fetch_europe_pmc_full_text(pmcid)
        if full_text:
            print("Full text evidence:")
            print(find_manufacturer_contexts(full_text, manufacturer, n=context_radius))
            print("===")
        else:
            print("No full text found.")
            print("===")


# Find and print evidence of manufacturer product mentioned in the abstracts and full texts
def find_evidence_in_publications(manufacturer, product_name, product_map, context_radius = 1, 
                                  pmids=None, europe_pmc_results=None):

    for pmid in pmids:
        print("Evidence for PMID:", pmid, f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/")

        # abstract = get_pubmed_abstract(pmid)
        # if abstract:
        #     print("Abstract evidence:")
        #     print(find_product_manufacturer_evidence(abstract, product_name, product_map, manufacturer, n=context_radius))
        #     print("---")
        # else:
        #     print("No abstract found.")
        #     print("---")
        
        full_text = fetch_pmc_full_text(pmid)
        if full_text:
            print("Full text evidence:")
            print(find_product_manufacturer_evidence(full_text, product_name, product_map, manufacturer, n=context_radius))
            print("===")
        else:
            print("No full text found.")
            print("===")
        print("")


    for r in europe_pmc_results:
        pmcid = r.get("pmcid")
        if not pmcid:
            continue

        print("Evidence for PMCID:", pmcid, f"https://europepmc.org/article/PMC/{pmcid.replace("PMC", "")}")

        # abstract = get_europe_pmc_abstract(pmcid)
        # if abstract:
        #     print("Abstract evidence:")
        #     print(find_product_manufacturer_evidence(abstract, product_name, product_map, manufacturer, n=context_radius))
        #     print("---")
        # else:
        #     print("No abstract found.")
        #     print("---")

        full_text = fetch_europe_pmc_full_text(pmcid)
        if full_text:
            print("Full text evidence:")
            print(find_product_manufacturer_evidence(full_text, product_name, product_map, manufacturer, n=context_radius))
            print("===")
        else:
            print("No full text found.")
            print("===")
        print("")



import pandas as pd


def export_evidence_to_csv(
    manufacturer,
    product_identifier,
    product_map,
    context_radius=1,
    pmids=None,
    europe_pmc_results=None,
    output_path="data/evidence/evidence.csv"
):
    """
    Collects product-manufacturer evidence from PubMed and Europe PMC
    and exports the results to a CSV file.

    Output schema:
        manufacturer
        product
        matched_alias
        evidence
        match_type
        source
        publication_id
        publication_url

    Parameters:
        manufacturer (str):
            Manufacturer name.

        product_name (str):
            Canonical product name being investigated.

        product_map (dict):
            Alias lookup generated by build_product_alias_map().

        context_radius (int):
            Context window size passed to matcher.

        pmids (list[str] | None):
            PubMed IDs.

        europe_pmc_results (list[dict] | None):
            Europe PMC search results.

        output_path (str):
            CSV destination path.
    """

    pmids = pmids or []
    europe_pmc_results = europe_pmc_results or []

    records = []

    # ----------------------------
    # PubMed evidence
    # ----------------------------
    for pmid in pmids:

        full_text = fetch_pmc_full_text(pmid)

        if not full_text:
            continue

        matches = find_product_manufacturer_evidence(
            full_text,
            product_identifier,
            product_map,
            manufacturer,
            n=context_radius
        )

        for match in matches:

            records.append({
                "manufacturer": manufacturer,
                "sku": product_identifier,
                "evidence": match,
                "match_type": "alias",
                "source": "PMID",
                "publication_id": pmid,
                "publication_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            })

    # ----------------------------
    # Europe PMC evidence
    # ----------------------------
    for result in europe_pmc_results:

        pmcid = result.get("pmcid")

        if not pmcid:
            continue

        full_text = fetch_europe_pmc_full_text(pmcid)

        if not full_text:
            continue

        matches = find_product_manufacturer_evidence(
            full_text,
            product_identifier,
            product_map,
            manufacturer,
            n=context_radius
        )

        for match in matches:

            records.append({
                "manufacturer": manufacturer,
                "sku": product_identifier,
                "evidence": match,
                "match_type": "alias",
                "source": "PMCID",
                "publication_id": pmcid,
                "publication_url": (
                    f"https://europepmc.org/article/PMC/"
                    f"{pmcid.replace('PMC', '')}"
                )
            })

    # ----------------------------
    # Export
    # ----------------------------
    df = pd.DataFrame(records)

    safe_name = product_identifier.lower().replace(" ", "_")
    output_path = f"data/evidence/{safe_name}_evidence.csv"

    df.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"Saved {len(df)} evidence records to {output_path}")

    return df



# ----------------------------
# CODE EXECUTION STARTS HERE
# ----------------------------
manufacturer = "GeneCopoeia"

# size of evidence: number of sentences that can surround manufacturer
context_radius = 1

# ----------------------------
# BUILD PRODUCT MAP
# ----------------------------
df = pd.read_csv("data/cleaned_products/product_aliases.csv", encoding="utf-8", dtype=str).fillna("")
product_map = build_product_alias_map(df)

# sample skus and product_names
skus = [
    "QP001",        # All-in-One™ qPCR primers
    "LT001",        # Lenti-Pac™️ HIV Expression Packaging Kit
    "EF013",        # EndoFectin™️ Max Transfection Reagent
    "MP004",        # MycoGuard™️ Mycoplasma PCR Detection Kit 2.0
    "EF017",        #EndoFectin™️ HepG2 Transfection Reagent
    "BI001",        #Biotechnology Reagent/Kit
    "LP341-100",    #Lentifect™️ Purified Lentiviral Particles
    "QP116",        #Luc-Pair™️ Duo-Luciferase Assay Kit
    "ER011",        #EZRecombinase™ LR II Enzyme Mix (-20℃)
    "CC001"         #GCI-5α Chemically Competent E.coli Cells, (10 tubes)
]

# # product names too specific
# product_names = [
#     "All-in-One™️ qPCR primers"
#     "Lenti-Pac™️ HIV Expression Packaging Kit",
#     "EndoFectin™️ Max Transfection Reagent",
#     "MycoGuard™️ Mycoplasma PCR Detection Kit 2.0",
#     "EndoFectin™️ HepG2 Transfection Reagent",
#     "Biotechnology Reagent/Kit",
#     "Lentifect™️ Purified Lentiviral Particles",
#     "Luc-Pair™️ Duo-Luciferase Assay Kit",
#     "EZRecombinase™ LR II Enzyme Mix (-20℃)",
#     "GCI-5α Chemically Competent E.coli Cells, (10 tubes)"
# ]

# truncated product names for better search queries
product_names = [
    "qPCR primers",
    "Lenti-Pac HIV",
    "EndoFectin",
    "Mycoplasma PCR Detection",
    "EndoFectin HepG2",
    "Biotechnology",
    "Lentifect",
    "Duo-Luciferase",
    "EZRecombinase",
    "GCI-5α"
]


for i in range(len(skus)):
    sku = skus[i]
    product_name = product_names[i]

    print("========================================")
    print("product_name:", product_name)
    print("sku:", sku)
    print("aliases:", product_map[sku.lower()])

    # Search PubMed for PMIDs mentioning the product
    pmids = search_pubmed(manufacturer, product_name)
    # Search Europe PMC for articles mentioning the product
    europe_pmc_results = search_europe_pmc(manufacturer, product_name)
    get_number_of_results(pmids, europe_pmc_results)

    export_evidence_to_csv(
        manufacturer,
        sku,
        product_map,
        context_radius=1,
        pmids=pmids,
        europe_pmc_results=europe_pmc_results,
        output_path="data/evidence/evidence.csv"
    )
    print("")