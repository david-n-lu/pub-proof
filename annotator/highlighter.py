"""
highlight_sentence.py

Used to highlight tokens in sentence
- Manufacturer
- SKUs
- Tokens in product map

To be used in PySide6 QTextEdit
"""



from matching.normalization import normalize_for_matching
from matching.phrase_extractor import get_keyword_indexes
from matching.sku_matcher import find_sku
from html import escape
from product_building.product_map import (
    build_product_map,
    build_alias_map,
    build_shortened_sku_map,
)

import re


YELLOW_HIGHLIGHT = '<span style="background-color: yellow; color: black; font-weight: bold;">{}</span>'
GREEN_HIGHLIGHT = '<span style="background-color: lime; color: black; font-weight: bold;">{}</span>'
# YELLOW_HIGHLIGHT = "|{}|"   # testing
# GREEN_HIGHLIGHT = "|{}|"    # testing


def highlight_sentence(
        sentence: str, 
        manufacturer: str,
        alias_map: str,
        shortened_sku_map: str,):
    """
    Highlights Manufacturer, SKU, and other product map tokens in sentence
    """

    if sentence.endswith("."):
        words = sentence[:-1].split()
    else:
        words = sentence.split()
    
    highlighted_words = []

    for word in words:
        word_norm = normalize_for_matching(word)

        word = escape(word)

        if get_index(word, normalize_for_matching(manufacturer)) != -1:
            # print(f"manufacturer: {word}")

            word = highlight_word(word, manufacturer, GREEN_HIGHLIGHT)
        elif find_sku(
            sentence=word_norm,
            skus=shortened_sku_map,
            manufacturer=manufacturer,
        ):
            # print(f"sku: {word}")
            word = highlight_word(word, word_norm, GREEN_HIGHLIGHT)
        else:
            keyword = get_keyword(word_norm, alias_map)

            if keyword:


                if get_index(word, keyword) != -1:
                    # print(f"keyword: {keyword}")
                    word = highlight_word(word, keyword, YELLOW_HIGHLIGHT)

                else:
                    for k in keyword.split("-"):
                        # print(f"keyword: {k}")
                        word = highlight_word(word, k, YELLOW_HIGHLIGHT)
            
        highlighted_words.append(word)


    if sentence.endswith("."):
        return " ".join(highlighted_words) + "."

    return " ".join(highlighted_words)
    

DASH_RE = re.compile(r"[\u2010-\u2015\u2212\uFE58\uFE63\uFF0D]")
def get_index(phrase, word):
    """
    Case Insensitive
    """
    phrase = DASH_RE.sub("-", phrase)
    return phrase.lower().find(word.lower())


def highlight_word(phrase, word, highlight):
    """
    Highlight "word" part of "phrase"

    Ex: highlight LT001 (word) in LT001-2 (phrase)
    """

    start = get_index(phrase, word)
    end = start + len(word)

    phrase = phrase[:start] + highlight.format(phrase[start:end]) + phrase[end:]

    return phrase


def get_keyword(word: str, alias_map):
    """
    Get tokens in word that are in product map
    """

    indexes = get_keyword_indexes(
        word,
        alias_map
    )

    if indexes:
        return next(iter(indexes.values()))
    else:
        return None



if __name__ == "__main__":
    sentences = """First-strand cDNA synthesis was performed with 1 μg total RNA using the SureScript™ First-Strand cDNA Synthesis Kit (GeneCopoeia, USA), incorporating oligo(dT) primers and RNase inhibitor.
qRT‒PCR assays were conducted on a CFX96 Real-Time PCR System (Bio-Rad, USA) using BlazeTaq™ SYBR® Green qPCR Mix 2.0 (GeneCopoeia).
Plasmid construction and transfection The full-length human CENPI coding sequence was PCR-amplified from HepG2 cDNA and cloned into the pcDNA3.1(+)-FLAG expression vector (Genecopoeia/Genecfps) between the EcoRI and XhoI restriction sites.
HA-tagged ABCE1 expression vector was ordered from Genecopoeia DNA, pcDNA3.1 empty vector was ordered from Thermofisher.
Additionally, lentiviral vectors harbouring shKDM4B or the KDM4B sequence were used to infect cells to generate stable transfectants (GeneCopoeia, inc., Rockville, MD, USA).
Luciferase Assay The MiTarget miRNA 3′UTR Target Clone was purchased from GeneCopoeia (Rockville, MD, USA).
The full 3′UTR (2353 bp) of Tnrc6a (Accession: NM_144925.3 ) was cloned into the pEZX-MT06 plasmid (8642 bp; GeneCopoeia) using AsiSI, EcoRI, BsiWI, XhoI, and SpeI restriction sites, with ampicillin as the selection antibiotic.
Promoter-reporter plasmids were purchased from Genecopoeia (Rockville, MD, USA) and included the following: pABCA4-Gluc (HPRM30328-PG02), pGUCY2F-Gluc (HPRM43732-PG02), pRBP3-Gluc (HPRM44587-PG02), pRHO-Gluc (HPRM30507-PG02), pGRK1-Gluc (HRPM44605-PG02), pRS
qRT‐PCR was performed using the RT 2 SYBR Green qPCR Mastermix and Primer mix from GeneCopoeia (Rockville, MD, USA) to measure the expression of Nfe2l2.
2.6.6 Dual‐luciferase reporter assay The wild‐type (WT) or mutant (MUT) 3′UTR sequence of Keap1 was cloned into the pEZX vector (GeneCopoeia, Cat#zt531).
"""

    sentences = sentences.split("\n")


    product_map = build_product_map(
        "data/raw_products"
    )

    print("Built Product Map")

    alias_map = build_alias_map(
        product_map
    )

    print("Built Alias Map")

    # Maps shortened SKU -> original SKU(s)

    shortened_sku_map = build_shortened_sku_map(
        product_map
    )

    for sentence in sentences:
        highlighted = highlight_sentence(
            sentence,
            "GeneCopoeia",
            alias_map,
            shortened_sku_map,
        )
    
        print(highlighted)