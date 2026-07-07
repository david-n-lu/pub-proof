"""
mention_extractor.py

Finds product names in sentences without SKUs.

Matches words in a sentence to the words in a product name

Utilizes Ollama AI model to find a product name in a sentence
"""

from numpy import False_

from matching.normalization import normalize_for_matching, shorten_product_name

SUBSTITUTIONS = {
    "rt qpcr": "qrt-pcr",
    "rt-qpcr": "qrt-pcr",

}
EDITIONS = ["1.0", "2.0", "3.0","4.0", "5.0", "6.0", "7.0", "8.0", "9.0"]


def get_word_variations(word):
    """
    Returns list of variations of a word for better matching

    1. Original word
    2. Singular form (if plural): kits --> kit
    3. Trademark suffix removed (if present): BlazeTaqTM --> BlazeTaq
    """

    words = []
    words.append(word)
    
    if len(word) >= 1 and word[-1] == "s":
        words.append(word[:-1])
    else:
        words.append(word + "s")
    
    if len(word) >= 2 and word[-2:] == "tm":
        words.append(word[:-2])
    
    return words


def score_phrase(phrase: str, product_name: str):

    phrase_words = set()
    phrase_words.update(phrase.split())

    substitutions = set()
    for original, sub in SUBSTITUTIONS.items():
        if phrase.find(original) != -1:
            substitutions.add(sub)
            substitutions.add(original)

    short = shorten_product_name(product_name)

    # product name starts with a number
    # use full product name if short didn't work
    if short == "":
        short = product_name

    product_words = short.split()

    count = 0
    bonus = 0

    for word in product_words:
        word = normalize_for_matching(word)
        
        variations = get_word_variations(word)

        found = False
        for w in variations:
            if w in phrase_words or w in substitutions:
                count += 1

                found = True
                break
        
        if found:
            continue
        
        # less penalty if edition wasn't found in phrase
        if word in EDITIONS:
            bonus += 0.01
    
    # return round(count / len(phrase_words), 2)
    # return round(count / len(words), 2)

    # rank by number of words shared between phrase in sentence and product_name
    # tie breaker: ratio of shared words to total words in product_name
    # - more "efficient" product_name's win
    ratio = round(count / len(product_words), 2)
    if ratio == 1.0:
        ratio -= 0.01
    return count + ratio + bonus



def get_product_data_from_phrase(phrase, product_map, alias_map, n = 10):
    """
    Gets products with the highest score and their skus
    - Reveals editions of the same general product
    - Reveals bad phrases if multiple products with the same score
    """
    
    skus = extract_best_product_mention(phrase, alias_map, n = n)

    products = []
    scores = []

    for sku in skus:
        product = product_map.get(sku,{}).get("product_name","")

        score = score_phrase(phrase, product)

        products.append(product)
        scores.append(score)

    best_skus = []
    best_products = []
    best_score = max(scores) if scores else 0
    best_scores = []

    group_by_short = {}

    # get products with same score for phrase
    # 1. get editions
    # 2. see quality of phrase: multiple products --> result not good
    for i in range(len(scores)):
        if scores[i] == best_score:
            best_skus.append(skus[i])
            best_products.append(products[i])
            best_scores.append(scores[i])

    return best_skus, best_products, best_scores



def extract_product_mention(phrase: str, alias_map):
    """
    Checks if word is in alias map and tracks products that alias can refer to

    Gathers all products sentence's words possibly refered to
    """

    words = normalize_for_matching(phrase).split()

    statistics = {}

    for word in words:

        if word not in alias_map:
            continue

        skus = alias_map.get(word,{})

        for sku in skus:
            if sku not in statistics:
                statistics[sku] = 0
            
            statistics[sku] += 1
    
    # sort by skus with most words pointing to it
    statistics = dict(sorted(statistics.items(), key=lambda item: item[1], reverse = True))

    return statistics

def extract_best_product_mention(phrase: str, alias_map, n = 1):
    statistics = extract_product_mention(phrase, alias_map)

    if n:
        return list(statistics.keys())[:n]
    return list(statistics.keys())


def get_phrases(sentence: str, alias_map, penalty=3.0):
    # gets indices of all relevant manufacturer words
    relevant_indexes = get_keyword_indexes(sentence, alias_map)

    # groups relevant words based on how close they are
    # returns list of list of indexes
    clusters = dp_segmentation(relevant_indexes, penalty=penalty)

    # takes cluster indexes and makes phrases
    phrases = {}
    for cluster in clusters:
        phrase = []
        for index in cluster:
            phrase.append(relevant_indexes[index])
        
        phrase = " ".join(phrase)

        # print(phrase)

        if cluster:
            phrases[phrase] = [cluster[0], cluster[-1]]

    return phrases

def get_best_phrases(sentence: str, alias_map, manufacturer: str = "GeneCopoeia", penalty=3.0, n = 10):
    phrases_dict = get_phrases(sentence, alias_map, penalty=penalty)

    # keep all phrases, in chronilogically order
    if n == None:
        return list(phrases_dict.keys())

    words = normalize_for_matching(sentence).split()
    manufacturer = normalize_for_matching(manufacturer)
    manufacturer_indexes = [i for i, x in enumerate(words) if manufacturer in x]

    closest = {}

    for phrase, indexes in phrases_dict.items():
        start = indexes[0]
        end = indexes[1]
        
        # phrase before manufacturer
        left_proximity = min([abs(end-index) for index in manufacturer_indexes])
        # phrase after manufacturer
        right_proximity = min([abs(start-index) for index in manufacturer_indexes])

        proximity = min(left_proximity, right_proximity)

        closest[phrase] = proximity

    closest = dict(sorted(closest.items(), key=lambda item: item[1]))
    closest = list(closest.keys())
    longest = sorted(phrases_dict.keys(), key=len, reverse=True)

    # n longest and n closest
    best = set()
    best.update(longest[:n])
    best.update(closest[:n])
    best = list(best)

    return best


def get_keyword_indexes(sentence: str, alias_map):
    """
    if word is in alias map, add it to indexes
    """

    if len(sentence) > 0 and sentence[-1] == ".":
        sentence = sentence[:-1]

    words = normalize_for_matching(sentence).split()

    # 9: synthesis
    # 10: kit
    indexes = {}

    for i, word in enumerate(words):

        for w in get_word_variations(word):
            if w in alias_map:
                indexes[i] = w
                break
        
        if i in indexes:
            continue
        
        # works for LT001 and LT001-02
        # Endofectin-Max
        for w in word.split("-"):
            # skus is a set or dictionary
            if w in alias_map:
                if i in indexes:
                    indexes[i] += "-" + w
                else:
                    indexes[i] = w

    return indexes


def get_indexes_from_dict(indexes_dict):
    return list(indexes_dict.keys())


def build_prefix_sums(numbers):
    """
    Precompute prefix sums and prefix squared sums.
    This lets us compute variance of any segment in O(1).
    """
    prefix_sum = [0]
    prefix_squared_sum = [0]

    for value in numbers:
        prefix_sum.append(prefix_sum[-1] + value)
        prefix_squared_sum.append(prefix_squared_sum[-1] + value * value)

    return prefix_sum, prefix_squared_sum


def segment_variance(start_index, end_index, prefix_sum, prefix_squared_sum):
    """
    Compute variance of numbers[start_index:end_index] in O(1).
    """
    length = end_index - start_index

    segment_sum = prefix_sum[end_index] - prefix_sum[start_index]
    segment_squared_sum = prefix_squared_sum[end_index] - prefix_squared_sum[start_index]

    mean = segment_sum / length
    mean_of_squares = segment_squared_sum / length

    variance = mean_of_squares - (mean * mean)
    return variance


def dp_segmentation(indexes_dict, penalty=3.0):
    """
    Split numbers into optimal clusters using DP.

    penalty controls how many clusters you prefer:
    - higher penalty → fewer clusters
    - lower penalty → more clusters
    """

    numbers = get_indexes_from_dict(indexes_dict)

    n = len(numbers)

    prefix_sum, prefix_squared_sum = build_prefix_sums(numbers)

    # dp[i] = best cost for first i numbers
    dp = [float("inf")] * (n + 1)
    back_pointer = [-1] * (n + 1)

    dp[0] = 0

    # try every possible ending position
    for end in range(1, n + 1):

        for start in range(0, end):

            cost_variance = segment_variance(
                start,
                end,
                prefix_sum,
                prefix_squared_sum
            )

            cost = dp[start] + cost_variance + penalty

            if cost < dp[end]:
                dp[end] = cost
                back_pointer[end] = start

    # reconstruct clusters
    clusters = []
    index = n

    while index > 0:
        start = back_pointer[index]

        clusters.append(numbers[start:index])

        index = start

    clusters.reverse()

    return clusters














import requests
import json

def extract_ollama(sentence, manufacturer = "GeneCopoeia", model = "llama3"):
#     prompt = f"""
# You are a parser. Output only valid JSON array of GeneCopoeia product names. No extra text.

# Extract all products from {manufacturer} in this sentence: {sentence}

# Return ONLY the product
# """
    # prompt = f"""
    # Extract products ONLY from {manufacturer} in this sentence: {sentence}.

    # Extract FULL product names.

    # Extract catalog numbers. Make sure they are not genes or other biomedical terms.

    # Do NOT extract the manufacturer {manufacturer}.

    # IGNORE products from other manufacturers.

    # Return ONLY minified JSON list (single line). No whitespace formatting, no backticks, no other text.

    # Do NOT return a JSON dictionary.

    # Do NOT group identifiers and product names. Separate them in the list
    # """

    prompt = f"""
Find biotech products from {manufacturer} in this sentence: {sentence}

Include full readable names and catalog numbers (if it exists). Do not include {manufacturer} or countries.

Return ONLY minified JSON list (single line) like:
["full product name 1 (cat1)", "full product name 2"]

Do not include the catalog number if it does not exist

If a product belongs to another company, don't include.

Return only the extracted product names. Do not include explanations, introductions, bullets, or phrases like "Here are the biotech products".
"""

    r = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0
            }
        }
    )

    output = r.json()["response"]

    start = output.find("[")
    end = output.rfind("]")

    # Verify both brackets exist before slicing
    if start != -1 and end != -1:
        output = output[start : end + 1]

    # print(output)

    try:
        output = json.loads(output)
        return output
    except:
        return output


def extract_ollama_batch(sentences, manufacturer = "GeneCopoeia", model = "llama3"):
    prompt = "For each of these sentences below:\n"

    for i, sentence in enumerate(sentences):
        prompt += f"{i}: {sentence}\n"

#     prompt += f"""
# Extract products ONLY from {manufacturer} in the sentences.
# IGNORE products from other manufacturers.

# Extract FULL product names.
# Extract catalog numbers separately. Make sure they are not genes or other biomedical terms.
# Do NOT extract the manufacturer {manufacturer} itself.

# Put each sentence's results in a list
# Do NOT group catalog numbers and product names. Separate them in the list

# At the end:
# Return ONLY a JSON list of dictionaries
# Each dictionary has a "products" key with a list of products and a "index" key with the index of the sentence
# No whitespace formatting, no backticks, no other text.
# """
#     prompt += f"""Extract products ONLY from {manufacturer} in the sentences.
# A "product" MUST be a commercially sold, branded biotech item such as kits, antibodies, proteins, or named reagents.

# DO NOT extract:
# - generic laboratory reagents (primers, buffers, salts, enzymes unless branded)
# - experimental components
# - functional molecules without branding (e.g., oligo(dT) primers, RNase inhibitor)

# Only extract products explicitly associated with {manufacturer} in the sentence.
# IGNORE products from other manufacturers.

# Do NOT infer or expand products beyond what is explicitly written.

# Extract FULL product names.
# Extract catalog numbers separately. Make sure they are not genes or other biomedical terms.
# Do NOT extract the manufacturer {manufacturer} itself.

# Put each sentence's results in a list.
# Do NOT group catalog numbers and product names. Separate them in the list.

# At the end:
# Return ONLY a JSON list of dictionaries.
# Each dictionary has a "products" key with a list of products and an "index" key with the sentence index.
# No whitespace formatting, no backticks, no other text.
# """

#     prompt += f"""You are a biomedical text extraction system.

# Your ONLY task is to extract EXACT product names from the sentence.
# You must behave as a strict span extractor (copy-from-text only).

# ---------------------------
# CORE RULE
# ---------------------------
# Every extracted product MUST be an exact continuous substring of the sentence.
# Do NOT modify, normalize, shorten, or expand any text.

# If it is not explicitly written in the sentence, DO NOT output it.

# ---------------------------
# PRODUCT DEFINITION
# ---------------------------
# A valid product is ONLY:
# - a commercially sold, branded biotech product (kits, antibodies, proteins, vectors, named reagent products)
# - explicitly associated with {manufacturer}

# DO NOT extract:
# - generic laboratory reagents (e.g., oligo(dT) primers, buffers, salts, dyes)
# - enzymes unless explicitly branded as a {manufacturer} product
# - functional molecules without branding (e.g., RNase inhibitor)
# - inferred components of kits or protocols
# - anything not explicitly written as a product name

# ---------------------------
# MANUFACTURER RULE
# ---------------------------
# Only extract products from {manufacturer}.

# The sentence MUST contain {manufacturer} somewhere (including parentheses, brackets, or inline mentions).
# If {manufacturer} is not present, return an empty list.

# If ANY other manufacturer is present in the same sentence, DO NOT extract any non-{manufacturer} products.

# ---------------------------
# ANTI-INFERENCE RULES
# ---------------------------
# Do NOT:
# - infer missing product names
# - expand abbreviations
# - split or merge product names
# - guess components of kits
# - treat reagents used in experiments as products unless explicitly branded

# ---------------------------
# CATALOG NUMBERS
# ---------------------------
# Extract catalog numbers ONLY if explicitly present.
# Do NOT confuse catalog numbers with genes, sequences, or biological terms.

# Catalog numbers must be returned exactly as written.

# ---------------------------
# OUTPUT FORMAT
# ---------------------------
# Return ONLY a JSON list of dictionaries.

# Each dictionary must follow this format:
# {{
#   "index": int,
#   "products": [exact strings from sentence],
#   "catalog_numbers": [exact strings from sentence]
# }}

# Rules:
# - No markdown
# - No explanations
# - No extra keys
# - No formatting text
# - No whitespace commentary
# """

    prompt += f"""
Extract FULL product names and catalog numbers from {manufacturer}.

These products should be subsets of the sentence.

Do NOT extract the manufacturer {manufacturer} itself.

Try to find a product. There should almost always be a result.

Return ONLY a JSON list of dictionaries.

Each dictionary must follow this format:
{{
  "index": int,
  "products": [exact strings from sentence],
  "catalog_numbers": [exact strings from sentence]
}}

Include a dictionary for each sentence, even if no results were found
"""

    # print(prompt)

    r = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0
            }
        }
    )

    output = r.json()["response"]

    start = output.find("[")
    end = output.rfind("]")

    # Verify both brackets exist before slicing
    if start != -1 and end != -1:
        output = output[start : end + 1]
    
    output = output.replace("\n", "")

    # print(output)

    try:
        output = json.loads(output)
        return output
    except:
        return output