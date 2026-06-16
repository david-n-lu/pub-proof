import re

ABBREVIATIONS = [
    # references / figures
    "fig", "figure", "figs",
    "ref", "refs",
    "eq", "equation", "eqs",
    "sec", "section",
    "chap", "chapter",
    "supp", "suppl",

    # publication metadata
    "vol", "no", "pp", "p",
    "ed", "eds",

    # people / titles
    "dr", "mr", "mrs", "ms", "prof",

    # companies
    "inc", "corp", "co", "ltd", "llc",

    # common latin abbreviations
    # "e.g", "i.e", "etc", "et al", "cf", "vs",
    "etc", "et al", "cf", "vs",

    # catalog / product references
    "cat", "lot",

    # addresses / misc
    "st", "ave", "dept",
]

def protect_abbreviations(text: str):
    for abbr in ABBREVIATIONS:
        # matches "cat." or "fig." etc
        pattern = r"\b" + re.escape(abbr) + r"\."
        text = re.sub(pattern, abbr + "<DOT>", text, flags=re.IGNORECASE)
    return text


def restore_abbreviations(text: str):
    return text.replace("<DOT>", ".")

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
    full_text = protect_abbreviations(full_text)
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

    results = [restore_abbreviations(s) for s in results]
    return results


def test():
    from corpus.xml_parser import parse_pmc_article
    pmcid = "PMC12450569"

    result = parse_pmc_article(pmcid)

    sentences = get_sentences_with_manufacturer(full_text = result["full_text"], manufacturer = "GeneCopoeia")

    for s in sentences:
        print(s)

# test()