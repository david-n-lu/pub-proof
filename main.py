"""
Biotech Literature Mining MVP

Pipeline:
1. Load product inputs
2. Build product map (alias index)
3. Query PubMed + Europe PMC
4. Fetch full text XML
5. Parse XML → sections
6. Sentence extraction
7. Aho-Corasick matching (matcher_v2)
8. Evidence export
"""

from math import prod

from core.io import load_evidence_input
from matching.product_map import build_product_map, build_alias_index

from core.pubmed import search_pubmed, fetch_pubmed_xml
from core.europe_pmc import search_europe_pmc, fetch_europe_pmc_xml

from core.query_building import build_query

from core.xml_parser import parse_article_xml
from core.sentence_extractor import extract_sentences

from core.matcher import find_product_manufacturer_evidence

from core.text_normalization import normalize, heavy_normalize, safe_filename

from core.citation import cite_from_europe_pmc

import pandas as pd


def export_evidence_to_csv(product_identifier, evidence, output_folder="data/evidence/"):
    # ----------------------------
    # Export
    # ----------------------------
    df = pd.DataFrame(evidence)

    safe_name = safe_filename(product_identifier)
    output_path = f"{output_folder}{safe_name}_evidence.csv"

    df.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"Saved {len(df)} evidence records to {output_path}")

    return df


def run_pipeline(
    input_path="data/genecopoeia_pipeline_test_23.csv",
    alias_path="data/genecopoeia_pipeline_test_raw_products", #data/raw_products",
    output_folder="data/genecopoeia_pipeline_test_evidence/", #"data/evidence/",
    manufacturer="GeneCopoeia",
    max_results=50
):
    
    # 1. Load inputs
    inputs = load_evidence_input(input_path)
    print("Loaded product inputs")

    # 2. Build product map + automaton
    product_map = build_product_map(alias_path)
    print("Built product map")

    # 3. Process each product
    for item in inputs:

        sku = item["sku"]
        product_name = item["product_name"]
        tokens = item["tokens"]

        # ----------------------------
        # Build query (centralized logic now)
        # ----------------------------
        query = build_query(
            manufacturer=manufacturer,
            product_name=product_name,
            sku=sku,
            tokens=tokens
        )
        
        # 4. PubMed and Europe PMC search
        pubmed_ids = search_pubmed(query, max_results)
        europe_ids = search_europe_pmc(query, max_results)

        print(f"Queried literature for {product_name}")

        sentences = []

        # 5. Fetch + parse PubMed
        for pmid in pubmed_ids:

            xml = fetch_pubmed_xml(pmid)
            if not xml:
                continue

            sections = parse_article_xml(xml)
            
            sent = extract_sentences(sections, manufacturer)

            for s in sent:
                s["id"] = pmid
                s["source"] = "PubMed"

            sentences.extend(sent)

        print(f"PubMed parsed | sentences_total = {len(sentences)}")
        
        # 6. Fetch + parse Europe PMC
        for result in europe_ids:

            pmcid = result.get("pmcid")
            if not pmcid:
                continue

            xml = fetch_europe_pmc_xml(pmcid)
            if not xml:
                continue

            sections = parse_article_xml(xml)
            
            sent = extract_sentences(sections, manufacturer)

            for s in sent:
                s["id"] = pmcid
                s["source"] = "EuropePMC"

            sentences.extend(sent)

        print(f"EuropePMC parsed | sentences_total = {len(sentences)}")
        
        # 7. Run matcher_v2

        # print(product_map[normalize(sku)]["aliases"])

        evidence = find_product_manufacturer_evidence(
            sentences=sentences,
            manufacturer=manufacturer,
            sku = sku,
            aliases = product_map[normalize(sku)]["aliases"],
            min_score=2
        )

        print(f"Matcher complete | evidence_found = {len(evidence)}")

        records = []

        # 8. Attach metadata + store
        for e in evidence:

            source = e["source"]
            id = e["id"]

            url = None
            citation = None
            
            if source == "PubMed":
                url = f"https://pubmed.ncbi.nlm.nih.gov/{id}/"

            elif source == "EuropePMC":
                id = id.replace('PMC', '')
                url = f"https://europepmc.org/article/PMC/{id}"
                citation = cite_from_europe_pmc(id)


            records.append({
            "manufacturer": manufacturer,
            "product_name": product_name,
            "sku": sku,

            "source": e["source"],
            "url": url,
            "citation": citation,
            
            
            "score": e["score"],
            # "section": e["hits"]["section"],
            "text": e["hits"]["text"],
            "aliases": e["hits"]["aliases"],
            })

        
        print(f"Records built for {manufacturer} | {product_name} | num_records = {len(records)}")
        
        df = export_evidence_to_csv(
            product_identifier=product_name + " " + sku,
            evidence=records,
            output_folder=output_folder
        )

        print("-" * 60)

        # print(f"Exported {len(df)} records")


if __name__ == "__main__":
    run_pipeline()