## Overview

This project extracts product-manufacturer evidence from biomedical literature (PubMed + EuropePMC).

It identifies whether scientific papers mention specific biotech products using:
- Product names
- Aliases (from product database)
- SKU / catalog numbers
- Manufacturer context

---

## Pipeline

1. Load product catalog (SKU, names, aliases)
2. Query PubMed and EuropePMC using manufacturer + product signals
3. Fetch full text XML (where available)
4. Parse XML into structured sections
5. Split sections into sentences with provenance tracking
6. Run Aho-Corasick-based alias matching over sentences
7. Score matches based on section + manufacturer context
8. Extract high-confidence evidence snippets
9. Export results with metadata (PMID / PMCID / source)

---

## Matching Strategy (Experimental)

This project uses an Aho-Corasick automaton for fast alias detection.

⚠️ Current limitations:
- High recall, but precision is noisy
- Alias quality heavily impacts performance
- Some false positives due to ambiguous or generic aliases

Future improvements planned:
- Weighted alias confidence scoring
- Context-aware filtering (manufacturer proximity, section weighting)
- Better entity disambiguation across products

---

## Output

Each evidence record contains:
- manufacturer
- product_name
- sku
- matched text (sentence-level evidence)
- score
- section (e.g., abstract, methods, results)
- source (PubMed / EuropePMC)
- publication URL (when available)
- document identifiers (PMID or PMCID)

---

## Notes

This is an experimental research pipeline and is actively being refined for precision and scalability.