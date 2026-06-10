import requests
import xml.etree.ElementTree as ET

EUROPE_PMC_XML = "https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"


def fetch_xml(pmcid: str) -> str:
    url = EUROPE_PMC_XML.format(pmcid=pmcid)
    r = requests.get(url, timeout=30)

    if r.status_code != 200:
        return None

    r.raise_for_status()
    return r.text

def extract_sections(xml_text: str):
    root = ET.fromstring(xml_text)

    sections = {}

    for sec in root.findall(".//sec"):
        title = sec.find("title")
        title_text = title.text.lower() if title is not None else "unknown"

        paragraphs = [
            " ".join(p.itertext())
            for p in sec.findall(".//p")
        ]

        text = " ".join(paragraphs).strip()

        if text:
            sections[title_text] = text

    return sections


def xml_to_text(xml_str: str) -> str:
    if not xml_str:
        return None

    root = ET.fromstring(xml_str)

    text = " ".join(root.itertext())

    # normalize whitespace
    text = " ".join(text.split())

    return text


def parse_pmc_article(pmcid: str):
    xml_text = fetch_xml(pmcid)
    # sections = extract_sections(xml_text)

    return {
        "pmcid": pmcid,
        # "sections": sections,
        "full_text": xml_to_text(xml_text),
        "raw_xml": xml_text,
    }


def test():
    pmcid = "PMC12450569"

    result = parse_pmc_article(pmcid)

    print(result["pmcid"])
    print(result["full_text"])
    # print(result["raw_xml"])

# test()