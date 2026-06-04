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