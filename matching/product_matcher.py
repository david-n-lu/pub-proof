"""
product_matcher.py

Finds products given phrases whose words are in the product map

Gets best product candidates based on phrase
- Tries trademark names
- Tries special characters aiming to capture bioidentifiers
- Tries phrase tokens that aren't general and only point to a few products

"""


from typing import List

from matching.legacy.mention_extractor import score_phrase
from matching.normalization import normalize, normalize_for_matching, shorten_product_name


def get_product_candidates(
    phrase: str, 
    product_map: dict, 
    alias_map: dict,
    trademark_names = None,
    genes: set = None,
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

    if trademark_names:
        trademark_names_norm = {normalize_for_matching(trademark) for trademark in trademark_names}
    else:
        trademark_names_norm = []

    # ========================================
    # get tokens of high priority
    # - gene names and accession numbers
    # - trademark names
    #
    # if no genes dataset available: track "special words"
    # - special words that have capital letters or numbers
    # ========================================

    gene_tokens = set()
    trademarks = set()
    special_words = set()
    special_words_limit = 100   # max skus special words can refer to
    trademark_limit = 100       # max skus trademark names can refer to
    gene_limit = 100            # max skus gene tokens can refer to

    for token in tokens:

        token_norm = normalize_for_matching(token)


        if genes and is_gene(token_norm, genes) and token_norm in alias_map:

            if len(alias_map.get(token_norm)) <= gene_limit:
                gene_tokens.add(token_norm)
                print(f"Gene ACCEPTED: {token_norm}")
            else:
                print(f"Gene DENIED: {token_norm}")


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



    # ========================================
    # get skus whose product name contains the highest priority token(s)
    # token priority is as follows: gene name, trademark, special word
    #
    # if not high priority tokens, use tokens with the least SKUs pointing to them
    # - all tokens below a certain threshold
    # ========================================

    skus = set()
    type = "general"

    if gene_tokens:

        for gene in gene_tokens:
            skus.update(alias_map.get(gene))

        type = "gene"

    elif trademarks:

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


    # ========================================
    # score SKUs based on how similar their shortened products names are to the phrase
    # ========================================

    return rank_products(
        phrase_tokens = tokens,
        skus = skus,
        product_map= product_map,
        type = type,
    )



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



def is_gene(word, genes):
    return word in genes
    


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

    if type == "gene":
        gene_phrase_tokens = get_gene_phrases(phrase_tokens)

    scores = {}

    for sku in skus:
        full_product = product_map.get(sku).get("product_name")

        if type == "gene":
            score = get_gene_match_score(full_product, gene_phrase_tokens)
        else:
            score = get_string_match_score(full_product, phrase_tokens)

        score = min(max(score, 0), 0.99)

        score = round(score, 2)

        scores[sku] = score

    highest_score = max(scores.values()) if scores else 0

    best_skus = [
        {
            "sku": sku, 
            "score": score, 
            "type": type,
            "phrase": " ".join(phrase_tokens)
        }
        for sku, score in scores.items() if score >= highest_score
    ]


    # sort by product name length (shorter is better cause of ncbi accession numbers)
    if type == "gene":
        best_skus.sort(key=lambda product: len(product_map.get(product["sku"]).get("product_name")))

    return best_skus


def get_string_match_score(product, phrase_tokens):
    """
    Computes ratio of shared tokens between product and phrase to total tokens in product name
    """
    product_tokens = get_product_tokens(product)

    num_shared_tokens = set(product_tokens) & set(phrase_tokens)

    score = len(num_shared_tokens) / len(product_tokens)

    return score


def get_product_tokens(product):
    shortened_product = shorten_product_name(product)
    return [normalize_for_matching(token) for token in shortened_product.split()]


def get_gene_match_score(product, gene_phrase_tokens):

    for phrase_tokens in gene_phrase_tokens:

        product_tokens = get_product_tokens(product)

        num_shared_tokens = len(set(product_tokens) & set(phrase_tokens))

        # if product name actual one of the gene products gene_phrase_tokens tracked

        if num_shared_tokens == len(phrase_tokens):

            print(f"Product Tokens: {product_tokens}")
            print(f"Phrase Tokens: {phrase_tokens}")
            print(f"Num Shared Tokens: {num_shared_tokens}")

            return 0.95 - 0.15 * len(gene_phrase_tokens)  # original phrase more ambiguous if it points to multiple gene products

    return 0


def get_gene_phrases(phrase_tokens: List[str]) -> List[List[str]]:
    """
    Transforms ambiguous phrase tokens into more specific gene product phrases based on GENECOPOEIA_GENE_PRODUCTS_MAP
    """

    phrase_tokens = [sub_token for token in phrase_tokens for sub_token in token.split("-")]

    product_counts = {}

    for token in phrase_tokens:
        if token in GENECOPOEIA_GENE_PRODUCTS_MAP:
            for general_product in GENECOPOEIA_GENE_PRODUCTS_MAP[token]:
                product_counts[general_product] = product_counts.get(general_product, 0) + 1

    max_count = max(product_counts.values()) if product_counts else 0

    all_phrase_tokens = []

    for general_product, count in product_counts.items():

        if count == max_count:

            # print(f"GENE PHRASE: {general_product}")

            phrase_tokens = normalize_for_matching(general_product).split()

            all_phrase_tokens.append(phrase_tokens)

    return all_phrase_tokens



GENECOPOEIA_GENE_PRODUCTS_MAP = {
    # Broad Catch-Alls (Keep ranked by typical literary usage)
    "plasmid": [
        "OmicsLink™ Expression-Ready ORF cDNA Clones",
        "OmicsLink™ shRNA Clone",
        "miTarget™ 3′ UTR miRNA Target Clones",
        "GLuc-ON™ Promoter Reporter Clones",
        "GeneHero™ CRISPR-Cas9 sgRNA",
    ],
    "clone": [
        "OmicsLink™ Expression-Ready ORF cDNA Clones",
        "OmicsLink™ shRNA Clone",
        "miTarget™ 3′ UTR miRNA Target Clones",
        "GLuc-ON™ Promoter Reporter Clones",
    ],
    
    # CRISPR / Gene Editing
    "sgrna": ["GeneHero™ CRISPR-Cas9 sgRNA"],
    "crispr": ["GeneHero™ CRISPR-Cas9 sgRNA"],
    "cas9": ["GeneHero™ CRISPR-Cas9 sgRNA"],
    "grna": ["GeneHero™ CRISPR-Cas9 sgRNA"],  # Added generic term
    
    # RNA Interference & Knockdown
    "shrna": ["OmicsLink™ shRNA Clone"],
    "knockdown": ["OmicsLink™ shRNA Clone"],  # Added functional term
    "silencing": ["OmicsLink™ shRNA Clone"],  # Added functional term
    
    # MicroRNA (Targets vs. Precursors)
    "mirna": [
        "miTarget™ 3′ UTR miRNA Target Clones", 
        "MiExpress™ Precursor miRNA Clone"
    ], # Fixed collision
    "3'": ["miTarget™ 3′ UTR miRNA Target Clones"],
    "3": ["miTarget™ 3′ UTR miRNA Target Clones"],
    "utr": ["miTarget™ 3′ UTR miRNA Target Clones"],
    "target": ["miTarget™ 3′ UTR miRNA Target Clones"],
    "precursor": ["MiExpress™ Precursor miRNA Clone"],
    "mir": ["MiExpress™ Precursor miRNA Clone"],
    
    # Promoters & Reporters
    "promoter": ["GLuc-ON™ Promoter Reporter Clones"],
    "reporter": [
        "GLuc-ON™ Promoter Reporter Clones", 
        "miTarget™ 3′ UTR miRNA Target Clones"
    ], # Fixed missing mapping
    "luciferase": [
        "GLuc-ON™ Promoter Reporter Clones", 
        "miTarget™ 3′ UTR miRNA Target Clones"
    ], # Added platform-specific term
    "gluc": [
        "GLuc-ON™ Promoter Reporter Clones", 
        "miTarget™ 3′ UTR miRNA Target Clones"
    ], # Added platform-specific term
    
    # Protein Expression / ORF
    "orf": ["OmicsLink™ Expression-Ready ORF cDNA Clones"],
    "open": ["OmicsLink™ Expression-Ready ORF cDNA Clones"],
    "reading": ["OmicsLink™ Expression-Ready ORF cDNA Clones"],
    "frame": ["OmicsLink™ Expression-Ready ORF cDNA Clones"],
    "cdna": ["OmicsLink™ Expression-Ready ORF cDNA Clones"],
    "overexpression": ["OmicsLink™ Expression-Ready ORF cDNA Clones"], # Added functional term
    
    # Proteins & Antibodies
    "mab": ["rabbit mab"],
    "antibody": ["rabbit mab"],    # Added generic term
    "monoclonal": ["rabbit mab"],  # Added generic term
    "recombinant": ["Human Recombinant Protein"],
    "purified": ["Human Recombinant Protein"], # Added generic term
    "protein": ["Human Recombinant Protein"] # Added generic term
}

