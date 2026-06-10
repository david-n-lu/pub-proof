import re
import json


def get_sentences_with_manufacturer(full_text: str, manufacturer: str, window: int = 200):
    """
    Extract sentences from full text that contain a manufacturer mention.

    Steps:
    1. Split full text into sentences
    2. Normalize text for matching
    3. Filter sentences containing manufacturer
    4. If a sentence is long, truncate around the leftmost and rightmost occurrence
    of the manufacturer with a ±window character context.
    """

    # --- sentence splitter (MVP-level) ---
    sentences = re.split(r'(?<=[.!?])\s+', full_text)

    # --- normalization helper ---
    def normalize(text: str) -> str:
        return re.sub(r'\s+', ' ', text.lower())

    m = normalize(manufacturer)

    # --- filter sentences ---
    results = []
    for s in sentences:
        s_norm = normalize(s)

        if m not in s_norm:
            continue

        # find all occurrences of manufacturer
        matches = [m.start() for m in re.finditer(re.escape(m), s_norm)]

        if not matches:
            continue

        left = matches[0]
        right = matches[-1] + len(m)

        start = max(0, left - window)
        end = min(len(s), right + window)

        snippet = s[start:end].strip()

        results.append(snippet)

    return results


def test():
    from corpus.xml_parser import parse_pmc_article
    pmcid = "PMC12450569"

    result = parse_pmc_article(pmcid)

    sentences = get_sentences_with_manufacturer(full_text = result["full_text"], manufacturer = "GeneCopoeia")

    for s in sentences:
        print(s)

# test()