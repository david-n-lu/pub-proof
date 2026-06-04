# PubProof

PubProof is a publication-based product validation tool for biotechnology companies.

The project searches scientific literature (PubMed and Europe PMC) to identify evidence that a manufacturer's products are referenced in peer-reviewed publications.

## Features

* Product name normalization and cleaning
* Alias and synonym matching
* PubMed search integration
* Europe PMC search integration
* Full-text evidence extraction
* Structured evidence output
* CSV export for downstream analysis

## Project Structure

```text
PubProof/
├── core/
│   ├── database.py
│   ├── europe_pmc.py
│   ├── io.py
│   ├── pubmed.py
│   ├── query_building
│   ├── schema.py
│   ├── text_normalization.py
│   └── xml_to_text.py
│
├── data/
│   ├── raw_products/
│   ├── cleaned_products/
│   └── evidence/
│   ├── PRODUCT_INPUT.csv
│
├── docs/
│   └── schema_decisions.md
│
├── scripts/
│   ├── clean_products.py
│   ├── inspect_headers.py
│   ├── README.md
│   └── test_full_text.py
│
├── LICENSE
├── main.py
├── matcher.py
├── README.md
└── requirements.txt
```

## Installation

```bash
git clone <repository-url>
cd PubProof

python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Data

Raw product files are not included in this repository.

Place manufacturer product CSV files into:

```text
data/raw_products/
```

Example:

```text
data/raw_products/
├── company_a.csv
├── company_b.csv
└── company_c.csv
```

## Workflow

Workflow

PubProof requires an initial schema mapping step to standardize heterogeneous product CSV formats.

### 1. Inspect raw CSV headers

First, examine the structure of incoming product files:

python scripts/inspect_headers.py

This will print column headers for each file in:

data/raw_products/

Use this step to understand how each manufacturer structures their product data (column naming varies across sources).

### 2. Define schema mapping and canonical structure

PubProof uses a three-level schema system to normalize heterogeneous product CSVs. These layers progressively constrain the data from flexible input → standardized storage → strict matching format.

They are defined in core/schema.py.

### COLUMN_MAP (least restrictive)

This defines how raw CSV columns are interpreted.

It maps user-provided / vendor-specific column names into meaningful semantic fields.

Example:

COLUMN_MAP = {
    
    "Product Name": "product_name",
    "Alias": "aliases",
    "Alias Names": "aliases",
    "Symbol": "aliases",

    "Manufacturer": "manufacturer",
    "Manufacturer SKU": "sku",
    "Part ID": "sku",
    "Part ID.1": "sku",
    "crispr_product_id": "sku",

    "Gene Name": "bio_targets",
    "Gene ID": "bio_targets",
    "Uniprot": "bio_targets",
    "NCBI Accession": "bio_targets",
    "Acession Number": "bio_targets",
    "Gene Species": "bio_targets",
    "Species": "bio_targets",
    "Species Reactivity": "bio_targets",
    "Target Species": "bio_targets"
}

This layer is flexible and depends on how each raw dataset is structured.

### CANONICAL_TO_KEEP (intermediate restriction)

After cleaning, only a subset of standardized fields is retained in clean_products.csv.

This defines what is stored for downstream processing.

Example:

CANONICAL_TO_KEEP = [
    "product_name",
    "aliases",
    "sku",
    "manufacturer",
    "bio_targets"
]

Fields not included here are dropped during the cleaning step.

Output is written to: 

data/cleaned_products/

### CANONICAL_FIELDS (most restrictive)

This defines the strict schema expected by the matching system in matcher.py.

All downstream logic assumes these fields exist and are consistent.

Example:

CANONICAL_FIELDS = [
    "product_name",
    "aliases",
    "sku"
]

This ensures that product matching and alias resolution operate on a stable schema.

Key idea

COLUMN_MAP adapts to messy external data

CANONICAL_TO_KEEP defines what you persist

CANONICAL_FIELDS defines what matcher.py can rely on

### 3. Clean product data

After updating the schema mapping:

python scripts/clean_products.py

This will:

Normalize column names
Standardize product entries
Output cleaned datasets to:
data/cleaned_products/

### 4. Run evidence matching

### Add a sample of the products to find evidence for in data/

example: genecopoeia_pipeline_test.csv

### Edit 3 variables in main.py

1. manufacturer: name of your company

2. INPUT_DIR: .csv file of the products to find evidence for

3. ALIASES_DIR: .csv file of product aliases for all your products

example:

1. manufacturer = "GeneCopoeia"

2. INPUT_DIR = "data/genecopoeia_pipeline_test.csv"

3. ALIASES_DIR = "data/cleaned_products/product_aliases.csv"

### Execute the main pipeline: python main.py

This will:

Query PubMed and Europe PMC

Match products to aliases

Extract supporting evidence

Save structured outputs to:
data/evidence/


### Output format

Each evidence record includes:

manufacturer
product_name
sku
evidence
source
publication_id
publication_url

Example:

{
    
    manufacturer: GeneCopoeia,
    product_name: All-in-One™ qPCR Primers
    sku: qp001,
    evidence: Validated All-in-One™ qPCR primers for Kaiso, PXR, NF-κB, HER2, ABCB1 (P-gp), HIF1A, and ACTB (β-actin) were obtained from GeneCopoeia and confirmed for specificity and efficiency.,
    source: PMCID,
    publication_id: PMC12719565,
    publication_url: https://europepmc.org/article/PMC/12719565
}

## Data Sources

* PubMed
* Europe PMC

## License

MIT License
