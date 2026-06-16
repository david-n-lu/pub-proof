import json
import re
from numpy import full
import requests
import xml.etree.ElementTree as ET

from corpus.xml_parser import parse_pmc_article
from corpus.sentence_extractor import get_sentences_with_manufacturer


EUROPE_PMC_XML = "https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"


# ----------------------------
# XML → full text
# ----------------------------
def fetch_xml(pmcid: str) -> str:
    url = EUROPE_PMC_XML.format(pmcid=pmcid)
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.text


def xml_to_text(xml_text: str) -> str:
    root = ET.fromstring(xml_text)
    return " ".join(t.strip() for t in root.itertext() if t and t.strip())


# ----------------------------
# sentence splitter
# ----------------------------
def split_sentences(text: str):
    return re.split(r'(?<=[.!?])\s+', text)


def normalize(text: str):
    return re.sub(r'\s+', ' ', text.lower())


# ----------------------------
# core extractor
# ----------------------------
def extract_manufacturer_sentences(full_text: str, pmcid: str, manufacturer: str = "GeneCopoeia"):
    sentences = split_sentences(full_text)

    m = normalize(manufacturer)

    results = []

    for s in sentences:
        if m in normalize(s):
            results.append({
                "pmcid": pmcid,
                "manufacturer": manufacturer,
                "sentence": s.strip()
            })

    return results


# ----------------------------
# JSONL writer
# ----------------------------
def save_jsonl(path, records):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def flush(path, records):
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


# ----------------------------
# MAIN PIPELINE
# ----------------------------
def build_manufacturer_sentence_corpus(
    input_path: str,    # .jsonl
    output_path: str,   # .jsonl
    manufacturer: str = "GeneCopoeia",
    max_docs: int | None = None,
    batch_size=100,
    clear_output=True,
    start_line=0,
):
    """
    Build a sentence-level corpus of ONLY sentences that mention a manufacturer.

    Steps:
    1. Read Europe PMC JSONL (pmcid list)
    2. Fetch full-text XML
    3. Convert to text
    4. Extract manufacturer sentences
    5. Save as JSONL
    """

    # clear file ONCE
    if clear_output:
        open(output_path, "w", encoding="utf-8").close()

    buffer = []

    with open(input_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):

            if i+1 < start_line:
                continue

            if max_docs and i+1 > max_docs:
                break

            record = json.loads(line)
            pmcid = record.get("pmcid")

            xml_result = None
            full_text = None

            if pmcid:
                xml_result = parse_pmc_article(pmcid)
                full_text = xml_result["full_text"]

            sentences = []

            if full_text:
                sentences = get_sentences_with_manufacturer(full_text = full_text, manufacturer = manufacturer)

            seen = set()

            for s in sentences:
                if s not in seen:
                    seen.add(s)

                    new_record = record.copy()
                    new_record["sentence"] = s

                    buffer.append(new_record)

            # buffer.extend(sentences)

            print(f"[PROCESSED] {i+1} | {pmcid}")
            print(f"[RESULT] {pmcid} → {len(sentences)} sentences")

            # flush every BATCH_SIZE papers
            if (i+1) % batch_size == 0:
                flush(output_path, buffer)
                buffer = []  # reset
                print(f"[FLUSH] saved batch at {i+1}")

    
    # final flush
    if buffer:
        flush(output_path, buffer)
        print("[FINAL FLUSH]")

    # save_jsonl(output_path, all_results)
    # print(f"\nSaved {len(all_results)} sentences → {output_path}")

# ----------------------------
# quick test
# ----------------------------
if __name__ == "__main__":
    # build_manufacturer_sentence_corpus(
    #     input_path="data/europe_pmc/genecopoeia.jsonl",
    #     output_path="data/europe_pmc/genecopoeia_sentences.jsonl",
    #     manufacturer="GeneCopoeia",
    #     max_docs=100,
    #     batch_size = 100,
    #     clear_output = True,
    #     start_line = 0
    # )

    # start_line = 1000
    # start_line = 1101
    # start_line = 1701
    # start_line = 2001
    # start_line = 2301
    # start_line = 101
    # start_line = 1301
    # start_line = 3300
    # start_line = 4101
    # start_line = 5201
    # start_line = 7401
    # start_line = 8501
    # start_line = 8601
    # start_line = 8801
    # start_line = 8901

    # start_line = 101
    # start_line = 201
    # start_line = 901
    # start_line = 1401
    # start_line = 2601
    # start_line = 3401
    # start_line = 6701

    # start_line = 101
    # start_line = 2901

    # start_line = 101
    # start_line = 901
    # start_line = 2401
    # start_line = 3501
    # start_line = 4201
    start_line = 5201

    build_manufacturer_sentence_corpus(
        input_path="data/europe_pmc/genecopoeia.jsonl",
        output_path="data/europe_pmc/genecopoeia_sentences.jsonl",
        manufacturer="GeneCopoeia",
        max_docs=None,
        batch_size = 100,
        clear_output = False,
        start_line = start_line
    )
    