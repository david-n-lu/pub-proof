# normalization.py

from math import e
import re

UNICODE_NORMALIZATION = {
    "–": "-",
    "—": "-",
    "−": "-",
    "‐": "-",
    "‒": "-",
    "×": "x",
    "µ": "u",
    "μ": "u",
    "™": " ",
    "®": " ",
    "’": "'",
    "´": "'",
    "′": "'",
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



def shorten_product_name(product_name):
    short = []
    EDITIONS = ["1.0", "2.0", "3.0","4.0", "5.0", "6.0", "7.0", "8.0", "9.0"]
    EXCLUDE = ["for"]
    UNITS = [
    # volume
    "L", "mL", "uL", "nL", "pL",

    # mass
    "g", "mg", "ug", "ng", "pg",

    # concentration
    "M", "mM", "uM", "nM", "pM",
    
    "rxns"]
    DONT_CAPITALIZE = ["and"]

    # put spaces outside of parentheses
    product_name = re.sub(r'\(', ' (', product_name)
    product_name = re.sub(r'\)', ') ', product_name)
    product_name = re.sub(r'\s+', ' ', product_name).strip()

    # Format product names with descriptions attached
    # Before: miTarget™ 3′ UTR miRNA Target Clones: miRNA 3´UTR target expression clone for Human MYCN (NM_005378.5)
    # After: miTarget™ 3′ UTR miRNA Target Clones for Human MYCN (NM_005378.5)
    prepositions = ["for", "against", "targeting"]
    colon_index = product_name.find(":")
    preposition_index = -1
    if colon_index != -1:
        for p in prepositions:
            preposition_index = product_name.find(p)
            
            if preposition_index != -1:
                break
        
        if preposition_index != -1:
            product_name = product_name[:colon_index] + " " + product_name[preposition_index:]

            # OmicsLink™ ShRNA Clone: ShRNA Clone Set Against Human USF2 (NM_001321150.1)(Includes Free Control)
            # OmicsLink™ ShRNA Clone Against Human USF2 (NM_001321150.1)
            EXCLUDE = ["includes"]

    DONT_CAPITALIZE.extend(prepositions)

    def is_float(value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    words = product_name.split()

    for w in words:
        w_norm = w.lower()
        w_norm = re.sub(r"[()]", "", w_norm)

        # no 20, 20ml allowed
        # 2.0, 3.0 allowed

        if is_float(w_norm) or any(is_float(w_norm.replace(u.lower(),"")) for u in UNITS):
            if w_norm not in EDITIONS:
                break
            
        if w_norm in EXCLUDE:
            break
        
        if w_norm not in DONT_CAPITALIZE and \
        not any(char.isupper() for char in w) and \
        not any(char.isdigit() for char in w):
            w = w[0].upper() + w[1:]
        
        w = w.replace(",","").replace("*","")

        # miRNA Scrambled Control-MR03 Lentiviral Particles(25 Μl X
        # gets rid of (25 Ml X if product name poorly formatted
        
        w_original = w
        w = re.sub(r"\(\d.*$", "", w)

        short.append(w)

        # gets rid of (25 Ml X if product name poorly formatted
        if not w_original == w:
            break
    

    num_words = len(short)
    ratio = num_words / len(words)

    short = " ".join(short)

    # print(product_name)
    # print(short)

    min_num_words = 3
    min_ratio = 0.5

    if short:
        if num_words >= min_num_words or ratio >= min_ratio:
            return short
        # else:
        #     print(short)
        #     print(product_name)
    
    return product_name



AMBIGUOUS_SKU_TOKENS = {
    # editions/sizes
    "v1", "v2", "v3",
    "0025", "0050", "0100",
    "01", "02",
    "b", "10",
    "b1", "f1", "p1", 
    "025", "050", "100", "200", "400",
    "025", "100",
    "a1", "a6", "b1", "b6", "c1", "c6", "d1", "d6", "e1", "e6", "f1", "f6", "g1", "g6", "h1", "h6",
    "20", "25", "50", "100",
    
    # redundant: included in thousands of SKUs
    "cg04", "3", "10", "mt05", "lvru6gp", "pg04", "mr03", "10", "m35",


    # old sku tokens
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
    "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
    "a00", "200c",
    "1", "8", "01", "02", "08", "09", "10", "15"
}

def get_shortened_sku(sku):
    tokens = sku.split("-")

    index = len(tokens) - 1

    while (index >= 0 and tokens[index] in AMBIGUOUS_SKU_TOKENS):
        index -= 1
    
    if index < len(tokens) - 1 and index >= 0:
        return "-".join(tokens[:index + 1])

    return sku




def get_redundant_strings_in_skus(skus, THRESHOLD = 2, IGNORE_PREFIX = True):
    """
    Gets rid of longest common suffixes given a list of skus

    If a suffix appeared in at least THRESHOLD skus, remove it.
    IGNORE_PREFIX determines whether a common prefix is ignored

    Example:
    Chops "-CG04-3-10" from "HCP389717-CG04-3-10", "HCP389718-CG04-3-10", "HCP352138-CG04-3-10"
    Doesn't Chop "mab" from "mAb-00009", "mAb-00010", "mAb-00011"
    """

    # -----------------------------
    # 1. Get common strings found among list of skus. Can ignore prefixes
    # -----------------------------
    string_counts = {}

    for sku in skus:
        strings = sku.split("-")

        if not strings:
            continue

        if IGNORE_PREFIX:
            strings = strings[1:]
        
        for string in strings:
            if not string in string_counts:
                string_counts[string] = 0
            string_counts[string] += 1

    remove_list = {key for key, value in string_counts.items() if value >= THRESHOLD}
    
    print({k: v for k, v in string_counts.items() if v >= THRESHOLD})

    # -----------------------------
    # 2. Map original skus to shortened skus
    # -----------------------------
    shortened_skus = {}

    for sku in skus:
        short = []

        for string in sku.split("-"):
            if string not in remove_list:
                short.append(string)
        
        short = "-".join(short)
        shortened_skus[sku] = short
    
    return shortened_skus




if __name__ == "__main__":
    skus = [
        "hcp349056-cg04-3-10",
        "hcp349067-cg04-3-10",
        "hcp349272-cg04-3-10",
        "hcp349273-cg04-3-10",
        "hcp349274-cg04-3-10",
        "hcp351317-cg04-3-10",
        "hcp351318-cg04-3-10",
        "hcp367363-cg04-3-10",
        "hcp320691-cg04-3-10",
        "hcp200001-cg04-3-10",
    ]

    # print(get_redundant_strings_in_skus(skus))

    for s in skus:
        print(f"{get_shortened_sku(s)}: {s}")
    

