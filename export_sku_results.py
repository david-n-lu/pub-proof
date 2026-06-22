"""
export_sku_results.py

Filters sentences from corpus that have known manufacturer skus

Exports results in citation format below:
Liu, B., et al. (2026). Estrogen upregulates NR4A1 to counter TGF beta induced pulmonary fibrosis therapeutic insights for IPF. iScience DOI: \\
10.1016/j.isci.2026.114756 [Lentifect™ Lentiviral particles expressing Mouse Nr4a1 and scrambled control, Cat. No. LPP-Mm03063-Lv201-100, \\
LPP-MSH197809-LVRU6GP-500, LP146-100; RNAzol® RT RNA Isolation Reagent, Cat. No. QP020; SureScript™ First-Strand cDNA Synthesis Kit, Cat. \\
No. QP056; BlazeTaq™ SYBR Green qPCR Mix 2.0 (with ROX), Cat. No. QP031]
"""


import csv
import json
import re
from matching.product_map import build_product_map
from matching.sku_matcher import find_sku


def format_list_csv(list, delimiter = "|"):
    return delimiter.join(list)

def get_citation(record: dict) -> str:
    """
    Format a Europe PMC metadata dictionary into a citation string.
    """

    # --- Authors ---
    authors = record.get("authors", "")

    # Optional: convert "A, B, C, D" → "A, et al." if long
    if authors and "," in authors:
        first_author = authors.split(",")[0].strip()
        authors = f"{first_author}, et al."

    # --- Core fields ---
    title = record.get("title", "").strip()
    journal = record.get("journal_iso")
    year = record.get("year")

    # --- DOI handling ---
    doi = record.get("doi", "")
    if isinstance(doi, list):
        doi = doi[0] if doi else ""

    # --- Build citation ---
    citation = f"{authors} ({year}). {title}. {journal}"
    citation = citation.replace("..", ".")

    if doi:
        citation += f" DOI: {doi}"

    return citation

def format_products(skus, products):
    """
    Takes ordered SKUs and matching ordered product names and formats them into:

    Product Name, Cat. No. SKU1, SKU2; Product Name, Cat. No. SKU3...

    Assumes skus and products are aligned with each other
    """

    parts = []

    for i in range(len(skus)):
        product = products[i]
        sku = skus[i]
        processed_product = shorten_product_name(product)
        parts.append(f"{processed_product}, Cat. No. {sku.upper()}")

    return f"[{'; '.join(parts)}]"

def shorten_product_name(product_name):
    short = []
    EDITIONS = ["1.0", "2.0", "3.0","4.0", "5.0", "6.0", "7.0", "8.0", "9.0"]
    EXCLUDE = ["for"]
    UNITS = [
    # volume
    "L", "mL", "uL", "nL", "pL",

    # mass
    "g", "mg", "ug", "ng", "pg",

    # concentration
    "M", "mM", "uM", "nM", "pM",
    
    "rxns"]
    DONT_CAPITALIZE = [
        "cdna",
        "qpcr",
        "pcr",
        "rt-pcr",
        "rtpcr",
        "qpcr",
        "rt-qpcr",
        "dna",
        "rna",
        "mrna",
        "trna",
        "rrna",
        "mirna",
        "and",
    ]

    def is_float(value):
        try:
            float(value)
            return True
        except ValueError:
            return False
    

    for w in product_name.split():
        w_norm = w.lower()

        # no 20, 20ml allowed
        # 2.0, 3.0 allowed

        if is_float(w_norm) or any(is_float(w_norm.replace(u.lower(),"").replace("(","").replace(")","")) for u in UNITS):
            if w_norm not in EDITIONS:
                break
            
        if w_norm in EXCLUDE:
            break
        
        if w_norm not in DONT_CAPITALIZE:
            w = w[0].upper() + w[1:]
        
        w = w.replace(",","").replace("*","")

        # miRNA Scrambled Control-MR03 Lentiviral Particles(25 Μl X
        # gets rid of (25 Ml X if product name poorly formatted
        
        w_original = w
        w = re.sub(r"\(\d.*$", "", w)

        short.append(w)

        # gets rid of (25 Ml X if product name poorly formatted
        if not w_original == w:
            break

    short = " ".join(short)

    # print(product_name)
    # print(short)

    return short


def run_pipeline(manufacturer: str, sentence_corpus_path: str, product_map_path: str, output_csv_path: str):
    product_map = build_product_map(product_map_path)
    print("Built product map")

    # results = []
    results = {} # pmcid: record
    
    sentences_processed = 0

    with open(sentence_corpus_path, "r", encoding="utf-8") as f:

        # sentence_index = 0

        for line in f:
            record = json.loads(line)
            pmcid = record.get("pmcid") # always exists because of manufacturer_corpus.py filtering
            sentence = record.get("sentence", "")
            
            skus = find_sku(sentence=sentence, skus=product_map, manufacturer=manufacturer)

            result = record.copy()
            # result["idx"] = sentence_index
            # sentence_index += 1

            if not skus:
                continue

            # skus = list({s["sku"] for s in skus})
            # products = [product_map.get(sku).get("product_name") for sku in skus]

            if not pmcid in results:
                results[pmcid] = result
                results[pmcid]["product_name"] = []
                results[pmcid]["sku"] = []
                results[pmcid]["sentences"] = []
            
            # used list to keep in order seen in text
            # list is small so don't need set
            for sku in [s["sku"] for s in skus]:
                if sku in results[pmcid]["sku"]:
                    continue
                
                product = product_map.get(sku).get("product_name")

                results[pmcid]["product_name"].append(product)
                results[pmcid]["sku"].append(sku)
            results[pmcid]["sentences"].append(sentence)

            # results[pmcid]["product_name"].extend(products)
            # results[pmcid]["sku"].extend(skus)

            # result["product_name"] = format_list_csv(products)
            # result["sku"] = format_list_csv(skus)
            # result["citation"] = get_citation(record) + " " + format_products(skus, products)

            # results.append(result)

            sentences_processed += 1

            # print(f"SKU: {skus}")
            # print(f"Processed sentence with SKU: {sentence}")
            print(f"Number of sentences processed: {sentences_processed}")
            print("-"*60)


    with open(output_csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)

        writer.writerow([
            "manufacturer",
            "sku",
            "product_name",
            "citation",
            "url",
            "sentence",
        ])

        check_product_names = {}

        # for r in results:

        for pmcid, r in results.items():
            id = r.get("pmcid").replace("PMC","")
            skus = r.get("sku","")
            products = r.get("product_name","")
            citation = get_citation(r) + " " + format_products(skus, products)
            sentences = r.get("sentences")

            for p in products:
                check_product_names[p] = shorten_product_name(p)

            writer.writerow([
                manufacturer,
                # r.get("sku",""),
                format_list_csv(skus),
                # r.get("product_name"),
                format_list_csv(products),
                citation,
                f"https://europepmc.org/article/PMC/{id}",
                # r.get("sentence"),
                " ".join(sentences),
            ])
        
        for long, short in check_product_names.items():
            print(f"Original:  {long}")
            print(f"Shortened: {short}")


if __name__ == "__main__":
    manufacturer = "GeneCopoeia"
    sentence_corpus_path = "data/europe_pmc/genecopoeia_sentences.jsonl"
    product_map_path = "data/raw_products"
    output_csv_path = "data/europe_pmc/matcher_results_with_sku.csv"

    run_pipeline(manufacturer=manufacturer,
                 sentence_corpus_path=sentence_corpus_path,
                 product_map_path=product_map_path,
                 output_csv_path=output_csv_path)