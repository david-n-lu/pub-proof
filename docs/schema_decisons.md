.csv HEADERS TO USE IN core/schema.py:
1. product_name: Human-readable name of the product.
    - example: Anti-CD4 Antibody
2. aliases: Alternative names, synonyms, shorthand forms, or vendor-specific naming.
    - example: CD4 Ab, anti CD4, α-CD4 antibody, anti-human CD4
3. sku: Catalog number(s) / SKU identifiers.
    - example: AB1234, 123-45
4. manufacturer: Company that produces the product.
    - example: GeneCopoeia
5. bio_targets: Biological entities the product interacts with (genes, proteins, markers, receptors).
    - example: CD4, T-cell receptor, IL-6



🔴 Tier 1 (CRITICAL for matcher.py)
    product name
    aliases
    SKU
    manufacturer
    gene/protein identifiers

🟡 Tier 2 (useful context boost)
    species
    isotype
    clonality
    target species
    subcategory

⚪ Tier 3 (ignore for matching)
    pricing
    images
    compliance codes
    logistics


✔️ RELEVANT headers:

    🧪 Product identity
        Product Name
        Alias
        Alias Names
        Symbol
        Description
    🏭 Manufacturer / identifiers
        Manufacturer
        Manufacturer SKU
        Part ID
        Part ID.1
        crispr_product_id
    🧬 Biology / target mapping
        Gene Name
        Gene ID
        Gene Species
        Species
        Species Reactivity
        Target Species
        Uniprot
        NCBI Accession
        Acession Number
    🧫 Product classification
        Category
        Subcategory
        Array format
        Clonality
        Isotype
        Conjugate
        Host
        Expression System
        Vector
        Promoter
        Selection Marker
        Recombinant
    📏 Physical / assay metadata
        Size
        Size1
        Size2
        Length(bp)
        ORF LEN
        Purity
        Storage condition
        Shipping condition
    🧾 Product linking / web / documentation
        Product URL
        Datasheet URL
        MSDS page
        User manual page
        Image URL
    💰 Pricing (optional but useful for enrichment)
        List Price
        List Price (USD)
        List price (academic)
        List price (industry)
        List Price1 (USD)
        List Price2 (USD)
        Discount Percentage

❌ IRRELEVANT headers:

    📊 Presentation / UI only
        Image Caption
        Image Caption (duplicate variants)
        Image URL spacing variants (only useful for UI, not matching)
    📦 Business logistics (usually not needed for NLP matching)
        Lead Time
        Lead Times
    🧾 Compliance / classification standards (rarely used in text matching)
        UNSPSC
        Harmonized Code
        HarmonizedCode
    🧬 Over-specific or redundant fields
        Tag
        Category (duplicate vs Subcategory already exists sometimes)
        List price (duplicate variants beyond normalization)