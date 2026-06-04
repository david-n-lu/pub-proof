"""
core/query_builder.py

Shared query construction logic for PubMed and Europe PMC searches.

Builds boolean search queries from product metadata (manufacturer,
product_name, sku, other terms).
"""

def build_search_query(manufacturer: str, 
                       product_name: str = None,  
                       catalog_number: str = None,
                       terms: list[str] = None):
    if not manufacturer:
        raise ValueError("No manufacturer provided.")

    terms = terms if terms else []

    if product_name:
        terms.append(f'"{product_name}"')

    if catalog_number:
        terms.append(f'"{catalog_number}"')

    query = " OR ".join(terms)
    query = f'{manufacturer} AND ({query})'
    
    # print(query)
    return query