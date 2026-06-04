"""
core/query_builder.py

Shared query construction logic for PubMed and Europe PMC searches.

Builds boolean search queries from product metadata (manufacturer,
product_name, sku, other terms).
"""

def build_query(manufacturer: str, 
                       product_name: str = None,  
                       sku: str = None,
                       tokens: list[str] = None):
    if not manufacturer:
        raise ValueError("No manufacturer provided.")

    tokens = tokens if tokens else []

    if product_name:
        tokens.append(f'"{product_name}"')

    if sku:
        tokens.append(f'"{sku}"')

    query = " OR ".join(tokens)
    query = f'{manufacturer} AND ({query})'
    
    # print(query)
    return query