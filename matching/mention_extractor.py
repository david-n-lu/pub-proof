import spacy

nlp = spacy.load("en_core_web_sm")


def extract_product_mention(sentence: str, manufacturer: str):
    """
    Uses spacy NLP to find product mention in a sentence

    Sentence already has manufacturer in it
    """

    doc = nlp(sentence)

    sent = next(doc.sents) if doc.has_annotation("SENT_START") else doc
    text = sent.text

    return [chunk.text for chunk in sent.noun_chunks]


    # best = None
    # best_dist = float("inf")

    # for chunk in sent.noun_chunks:
    #     chunk_text = chunk.text
    #     chunk_idx = lower_text.find(chunk_text.lower())

    #     if chunk_idx == -1:
    #         continue

    #     dist = abs(chunk_idx - manu_idx)

    #     # optional: slight preference for multi-word phrases
    #     if len(chunk_text.split()) == 1:
    #         dist += 5

    #     if dist < best_dist:
    #         best_dist = dist
    #         best = chunk_text

    # return best




import requests
import json

def extract_ollama(sentence, manufacturer = "GeneCopoeia", model = "llama3"):
#     prompt = f"""
# You are a parser. Output only valid JSON array of GeneCopoeia product names. No extra text.

# Extract all products from {manufacturer} in this sentence: {sentence}

# Return ONLY the product
# """
    prompt = f"""
    Extract products ONLY from {manufacturer} in this sentence: {sentence}.

    Extract FULL product names.

    Extract catalog numbers. Make sure they are not genes or other biomedical terms.

    Do NOT extract the manufacturer {manufacturer}.

    IGNORE products from other manufacturers.

    Return ONLY minified JSON list (single line). No whitespace formatting, no backticks, no other text.

    Do NOT return a JSON dictionary.

    Do NOT group identifiers and product names. Separate them in the list
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
    end = output.find("]")

    # Verify both brackets exist before slicing
    if start != -1 and end != -1:
        output = output[start : end + 1]
    
    output = output.replace("\n", "")

    print(output)

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