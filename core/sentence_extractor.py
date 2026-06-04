"""
Sentence extraction layer for biomedical text.

Converts structured XML sections into sentence-level records
used by downstream matching (Aho–Corasick + scoring).

Input:
    [
        {"section": str, "text": str}
    ]

Output:
    [
        {"section": str, "context": str}
    ]
"""


import re
from typing import List, Dict


_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")

def split_into_sentences(text: str) -> List[str]:
    """
    Split raw text into sentences using lightweight regex rules.

    This avoids heavy NLP libraries and works well for biomedical abstracts
    and PMC full-text sections where sentence punctuation is mostly reliable.

    Returns:
        List of cleaned sentence strings.
    """

    if not text:
        return []

    text = re.sub(r"\s+", " ", text).strip()

    return [
        s.strip()
        for s in _SENT_SPLIT.split(text)
        if s.strip()
    ]


def extract_sentences(
    sections: List[Dict],
    manufacturer: str = None
) -> List[Dict]:
    """
    Convert XML sections into sentence-level records.

    If manufacturer is provided, only keep sentences that contain it
    (light pre-filter for downstream matcher efficiency and precision).

    Each sentence retains its originating section label.

    Returns:
        List of dicts:
        {
            "section": str,
            "context": str
        }
    """

    sentences = []

    if manufacturer:
        manufacturer_norm = manufacturer.lower()

    for sec in sections:
        section = sec.get("section", "unknown")
        text = sec.get("text", "")

        if not text:
            continue

        for sent in split_into_sentences(text):

            # ----------------------------
            # Optional manufacturer filter
            # ----------------------------
            if manufacturer:
                if manufacturer_norm not in sent.lower():
                    continue

            sentences.append({
                "section": section,
                "context": sent
            })

    return sentences