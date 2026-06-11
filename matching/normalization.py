# normalization.py

import re

UNICODE_NORMALIZATION = {
    "–": "-",
    "—": "-",
    "−": "-",
    "×": "x",
    "µ": "u",
    "™": "",
    "®": "",
    "’": "'",
    "´": "'",
}


def normalize_unicode(text: str) -> str:
    """
    Normalize common Unicode characters found in biotech catalogs.
    """
    if not text:
        return ""

    text = str(text)

    for old, new in UNICODE_NORMALIZATION.items():
        text = text.replace(old, new)

    return text


def normalize_whitespace(text: str) -> str:
    """
    Collapse whitespace and normalize line endings.
    """
    if not text:
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize(
    text: str,
    keep_chars: str = "-.",
) -> str:
    """
    General-purpose normalization for product names and aliases.

    Keeps:
        - letters
        - digits
        - whitespace
        - characters in keep_chars

    Replaces everything else with spaces.
    """
    if not text:
        return ""

    text = normalize_unicode(text)

    escaped = re.escape(keep_chars)

    text = re.sub(
        rf"[^\w\s{escaped}]",
        " ",
        text,
    )

    text = normalize_whitespace(text)

    return text


def normalize_for_matching(text: str) -> str:
    """
    Aggressive normalization for alias matching.
    """
    text = normalize(text)

    return text.casefold()