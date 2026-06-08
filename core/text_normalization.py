import re

# ----------------------------
# Biotech normalization
# ----------------------------
def normalize_biotech_text(text: str) -> str:
    text = str(text).lower()

    # fix encoding issues first
    text = fix_mojibake(text)

    # remove trademark symbols
    text = text.replace("™", "")
    text = text.replace("®", "")
    text = text.replace("©", "")

    # normalize µ variants
    text = text.replace("µl", "ul")
    text = text.replace("μl", "ul")

    # remove other unwanted symbols
    text = text.replace("?", "")

    # collapse whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()

def fix_mojibake(text: str) -> str:
    if not isinstance(text, str):
        return text
    try:
        return text.encode("latin1").decode("utf-8")
    except Exception:
        return text


def fix_product_name(text: str) -> str:
    return text.replace("?", "")


def lightweight_normalize(text: str) -> str:
    """
    Lightweight normalization for biotech text matching.
    Keep it conservative to avoid destroying signal.
    """
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"[^a-z0-9\s\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize(text: str) -> str:
    text = str(text).lower()

    # fix encoding issues first
    text = fix_mojibake(text)

    # remove trademark symbols
    text = text.replace("™", "")
    text = text.replace("®", "")
    text = text.replace("©", "")

    # normalize µ variants
    text = text.replace("µl", "ul")
    text = text.replace("μl", "ul")

    # remove other unwanted symbols
    text = text.replace("?", "")

    # collapse whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def heavy_normalize(text: str) -> str:
    """
    Heavy normalization for biotech product name matching.

    Goals:
    - remove catalog / SKU noise
    - remove counts, versions, metadata
    - normalize symbols

    Output is for aliasing / deduping, not search.
    """
    if not text:
        return ""

    text = str(text)

    # fix encoding issues first (must exist in your codebase)
    text = fix_mojibake(text)

    text = text.lower()

    # normalize trademark / special symbols
    text = text.replace("™", "").replace("®", "").replace("©", "")
    text = text.replace("*", "")

    # normalize micro symbols
    text = text.replace("µl", "ul").replace("μl", "ul")

    # remove catalog / SKU metadata
    text = re.sub(r"\((?:old\s*)?cat\s*#\s*[^)]+\)", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\(lot\s*[^)]+\)", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\(cat\s*#\s*[^)]+\)", " ", text, flags=re.IGNORECASE)

    # remove all parenthetical content (reactions, counts, etc.)
    text = re.sub(r"\([^)]*\)", " ", text)

    # remove standalone numbers and decimals (2, 2.0, 600)
    text = re.sub(r"\b\d+(\.\d+)?\b", " ", text)

    # normalize punctuation → spaces (but keep hyphens for product lines)
    text = re.sub(r"[^a-z0-9\s\-]", " ", text)

    # collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text