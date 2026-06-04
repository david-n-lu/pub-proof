import re
from typing import List, Dict


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def split_into_sentences(text: str) -> List[str]:
    """
    Lightweight sentence splitter for PubMed / PMC text
    """

    if not text:
        return []

    # normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # split on sentence boundaries
    sentences = _SENTENCE_SPLIT_RE.split(text)

    return [
        s.strip()
        for s in sentences
        if s.strip()
    ]


def extract_sentences(sections: List[Dict]) -> List[Dict]:
    """
    Convert section blocks into sentence-level contexts.

    Input:
    [
        {
            "section": "methods",
            "text": "Sentence one. Sentence two."
        }
    ]

    Output:
    [
        {
            "section": "methods",
            "context": "Sentence one."
        },
        {
            "section": "methods",
            "context": "Sentence two."
        }
    ]
    """

    output = []

    for section in sections:
        section_name = section.get("section", "unknown")
        text = section.get("text", "")

        for sentence in split_into_sentences(text):
            output.append({
                "section": section_name,
                "context": sentence
            })

    return output