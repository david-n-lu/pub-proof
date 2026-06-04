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


def extract_sentences(sections: List[Dict]) -> List[Dict]:
    """
    Convert XML sections into sentence-level records.

    Each sentence retains its originating section label for downstream
    scoring (e.g. methods > discussion weighting in matcher_v2).

    Returns:
        List of dicts:
        {
            "section": str,
            "context": str
        }
    """

    sentences = []

    for sec in sections:
        section = sec.get("section", "unknown")
        text = sec.get("text", "")

        if not text:
            continue

        for sent in split_into_sentences(text):
            sentences.append({
                "section": section,
                "context": sent
            })

    return sentences

