# PubProof

PubProof is a lightweight biotech literature mining tool that finds publication evidence for commercial life science products.

Given a manufacturer and product catalog, PubProof searches biomedical literature, downloads full-text articles, extracts relevant sentences, and identifies evidence that a product was used in a published study.

## How It Works
1. Load product inputs
2. Build product map
3. Query PubMed + Europe PMC
4. Fetch article XML
5. Parse article sections
6. Extract sentences
7. Match product identifiers
8. Export evidence

## Matching Strategy

PubProof focuses on one product at a time.

For each product, the matcher searches for:

Product name
SKU / catalog number
Known aliases

### Example:

Product:
Lenti-Pac HIV Expression Packaging Kit

SKU:
LT001

Aliases:
- LT001
- Lenti-Pac
- HIV

To reduce false positives, matching is performed only on sentences that contain the target manufacturer.

### Example:

Lentivirus was produced in HEK293 FT cells following the 
Lenti-Pac™ HIV Expression Packaging Kit protocol (LT001, GeneCopoeia).

This is stronger evidence than a generic reference to a packaging kit with no manufacturer mentioned.

## Evidence Scoring

Aliases can have different confidence weights.

### Example:

{
    "Lenti-Pac HIV Expression Packaging Kit": 10,
    "LT001": 10,
    "Lenti-Pac": 7,
    "HIV Expression Packaging Kit": 5
}
{
    "lt001': 10.0,
    "lenti-pac hiv expression packaging kit": 2.5,
    "lenti-pac hiv": 1.5,
    "lenti-pac": 0.5
    "hiv": 0.5,
}


When multiple aliases appear in the same sentence, PubProof sums their weights.

### Example:

Lentivirus was produced in HEK293 FT cells following the 
Lenti-Pac™ HIV Expression Packaging Kit protocol (LT001, GeneCopoeia).

Matches:

- LT001
- Lenti-Pac HIV Expression Packaging Kit

Score:

10 + 2.5 = 12.5

This rewards evidence containing multiple independent identifiers instead of only using the highest-scoring match.

## Data Sources

PubProof currently searches:

PubMed + PubMed Central (PMC)
Europe PMC

PMC and Europe PMC are used to retrieve open-access full-text articles when available.

## Output

A CSV file is generated for each product with the columns:

manufacturer
product_name
sku
source
url
score
section
text
aliases

### Example row:

manufacturer	product_name	sku	source	score
GeneCopoeia	Lenti-Pac HIV Expression Packaging Kit	LT001	EuropePMC	12.5

## Project Structure
core/
├── build_product_map.py
├── europe_pmc.py
├── io.py
├── matcher.py
├── pubmed.py
├── query_building.py
├── sentence_extractor.py
├── text_normalization.py
└── xml_parser.py

main.py

## Goal

Find publication evidence that links commercial biotech products to scientific literature and export that evidence in a structured format.