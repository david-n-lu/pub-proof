"""
product_matcher.py

Finds products given phrases whose words are in the product map

Gets best product candidates based on phrase
- Tries trademark names
- Tries special characters aiming to capture bioidentifiers
- Tries phrase tokens that aren't general and only point to a few products

"""


from matching.normalization import normalize, normalize_for_matching, shorten_product_name


def get_product_candidates(
    phrase: str, 
    product_map: dict, 
    alias_map: dict,
):
    """
    Gets best product candidates for a phrase
    
    Step 1: Filters products to look for following this criteria

    1.  Only products with trademark name if trademark names exist in phrase
    2.  Only products with special word defined by is_special() (bioidentifiers)
        Special words need to be unique enough and have less than 10-100 skus it refers to
    3.  All products that contain at least one token in the phrase
    
    Step 2: Finds best product matches among filtered SKU list through matcher()
    """

    tokens = normalize(phrase).split()

    trademarks = set()
    special_words = set()
    special_words_limit = 100   # max skus special words can refer to
    trademark_limit = 100       # max skus trademark names can refer to

    for token in tokens:
        token_norm = normalize_for_matching(token)

        if token_norm in trademark_names_norm:
            
            if len(alias_map.get(token_norm)) <= trademark_limit:
                trademarks.add(token_norm)
            else:
                print(f"Trademark DENIED: {token}, {len(alias_map.get(token_norm))}")
        
        if is_special(token):
            
            if token_norm in alias_map and len(alias_map.get(token_norm)) <= special_words_limit:
                print(f"Special ACCEPTED: {token_norm}")
                special_words.add(token_norm)

            else:
                print(f"Special DENIED: {token_norm}")

    skus = set()
    type = "general"

    if trademarks:
        for trademark in trademarks:
            skus.update(alias_map.get(trademark))
        type = "trademark"

    elif special_words:
        for special in special_words:
            skus.update(alias_map.get(special))
        type = "special word"

    else:

        token_limit = 100   # max skus token can refer to

        # only add token if it isn't too ambiguous
        for token in tokens:

            if token in alias_map:
                if len(alias_map.get(token)) <= token_limit:
                    skus.update(alias_map.get(token))
                continue

            for t in token.split("-"):
                if t in alias_map and len(alias_map.get(t)) <= token_limit:
                    skus.update(alias_map.get(t))

    return rank_products(
        phrase_tokens = tokens,
        skus = skus,
        product_map= product_map,
        type = type,
    )
    



trademark_names = {
    "OmicsArray™",
    "Luc-Pair™",
    "EndoFectin™",
    "CRISPR-Fectin™",
    "Fast-Fusion™",
    "CoolCutter™",
    "ExoSure™",
    "ExoCt™",
    "SuperCut™",
    "IndelCheck™",
    "Smart-Join™",
    "Genome-TALER™",
    "GeneHero™",
    "VividFISH™",
    "Lenti-Pac™",
    "Lentifect™",
    "AAVPrime™",
    "EZRecombinase™",
    "CytoCt™",
    "All-in-One™",
    "SureScript™",
    "BlazeTaq™",
    "ExProfile™",
    "miProfile™",
    "miTarget™",
    "OmicsLink™",
    "GLuc-ON™",
    "MiExpress™",
    "OmicsLink™",
    "RNAzol®",
    "AccelerRT®",
    "UltraHiPF®",
    "NileHiFi®",
    "Secrete-Pair™",
}
trademark_names_norm = {normalize_for_matching(trademark_name) for trademark_name in trademark_names}


def is_special(word):
    """
    Checks if a word contains numbers or 2+ capital letters

    Examples:
    cDNA
    LT001
    qPCR
    ABCE1
    """
    
    letters = 0
    numbers = 0
    capital = 0

    for c in word:
        if c.isalpha():
            letters += 1
            if c.isupper():
                capital += 1
                    

        if c.isdigit():
            numbers += 1
    
    return capital >= 2 or numbers and letters



def rank_products(
    phrase_tokens: list,
    skus: list,
    product_map: dict,
    type: str,
):
    """
    Finds best matching product given 
    1. Phrase tokens
    2. Filtered list of products (SKUs)

    Best matching product determined by ratio between:
    - number of sharing tokens between shortened product name and phrase
    - number of tokens in shortened product name

    Returns skus with the best matching product names in this format:
    [
        {"sku": "LT001", best_ratio: 0.8}
        {"sku": "LT002", best_ratio: 0.8}
    ]
    """

    best_ratio = 0
    best_skus = set()

    for sku in skus:
        full_product = product_map.get(sku).get("product_name")

        product = shorten_product_name(full_product)
        product_tokens = [normalize_for_matching(token) for token in product.split()]


        shared = set(product_tokens) & set(phrase_tokens)

        ratio = round(len(shared) / len(product_tokens), 2)

        if ratio > best_ratio:
            best_skus = set()
            best_ratio = ratio
        if ratio >= best_ratio:
            best_skus.add(sku)

    return [
        {
            "sku": sku, 
            "score": min(0.99, best_ratio), 
            "type": type,
            "phrase": " ".join(phrase_tokens)
        }
        
        for sku in best_skus
    ]

