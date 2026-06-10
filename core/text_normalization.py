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

    Intended for:
    - alias generation
    - deduplication
    - fuzzy matching

    Removes catalog metadata, reaction counts, versions, and
    other non-essential product descriptors while preserving
    meaningful product terminology.
    """
    if not text:
        return ""

    text = fix_mojibake(str(text)).lower()

    # normalize symbols
    text = re.sub(r"[™®©]", "", text)
    text = re.sub(r"[\u2010-\u2015]", "-", text)  # unicode dashes → hyphen
    text = text.replace("µl", "ul").replace("μl", "ul")

    # remove mojibake artifacts
    text = text.replace("�", "").replace("*", "")

    # remove catalog / lot metadata
    text = re.sub(r"\((?:old\s*)?cat\s*#\s*[^)]+\)", " ", text, flags=re.I)
    text = re.sub(r"\(cat\s*#\s*[^)]+\)", " ", text, flags=re.I)
    text = re.sub(r"\(lot\s*[^)]+\)", " ", text, flags=re.I)

    # remove remaining parenthetical metadata
    text = re.sub(r"\([^)]*\)", " ", text)

    # remove standalone numeric metadata
    text = re.sub(r"\b\d+(?:\.\d+)?\b", " ", text)

    # keep only letters, numbers, spaces, and hyphens
    text = re.sub(r"[^a-z0-9\s-]", " ", text)

    # collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def safe_filename(text: str, max_len: int = 180) -> str:
    """
    Convert normalized product name into Windows-safe filename.
    """

    text = heavy_normalize(text)

    # remove mojibake leftovers (important for your case)
    text = text.replace("�", "")

    # replace illegal Windows filename characters
    text = re.sub(r'[<>:"/\\|?*]', "", text)

    # replace spaces with underscores
    text = re.sub(r"\s+", "_", text)

    # collapse underscores
    text = re.sub(r"_+", "_", text).strip("_")

    # trim length (Windows path limit protection)
    return text[:max_len]