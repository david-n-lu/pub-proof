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
│   ├── pubmed.py
│   ├── schema.py
│   └── utils.py
│
├── data/
│   ├── raw_products/
│   ├── cleaned_products/
│   └── evidence/
│
├── docs/
│   └── schema_decisions.md
│
├── scripts/
│   ├── clean_products.py
│   ├── inspect_headers.py
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

### Execute the main pipeline: python main.py

This will:

Query PubMed and Europe PMC

Match products to aliases

Extract supporting evidence

Save structured outputs to:
data/evidence/

### Matching assumptions and field semantics

PubProof relies on a few important assumptions about how product fields are used across the pipeline.

### product_name is used for literature search (PubMed + Europe PMC)

When querying:

PubMed
Europe PMC

the system uses product_name (or its normalized alias) as the primary search term.

### Important constraint:

The pipeline works best when product_name is a subset of the full product name as it appears in real-world usage.

For example:

Full product name:
"Lenti-Pac™️ HIV Expression Packaging Kit"

Good product_name:
"Lenti-Pac HIV"

This improves recall in literature searches, since publications often abbreviate or partially refer to products.

If product_name is too specific or overly branded, retrieval performance may degrade.

### sku is a unique identifier (not used for search)

The sku field is not used for PubMed or Europe PMC queries.

Instead, it serves as a stable product identifier for downstream processing and export.

### use sku in this function to best find aliases: main.py → export_evidence_to_csv()
### to change, change key_name in: matcher.py → build_product_alias_map()

### Output format

Each evidence record includes:

manufacturer
sku
evidence
source
publication_id
publication_url

Example:

{
    "manufacturer": GeneCopoeia,
    "sku": qp001,
    "evidence": The real-time PCR reactions were prepared using All-in-One™ qPCR Mix (GeneCopoeia, Rockville, USA) and All-in-One™ qPCR Primers (GeneCopoeia, Rockville, USA) according to the manufacturer's instructions.,
    "match_type": qPCR primers,
    "source": PMCID,
    "publication_id": PMC3288107,
    "publication_url": https://europepmc.org/article/PMC/3288107
}

## Data Sources

* PubMed
* Europe PMC

## License

MIT License
