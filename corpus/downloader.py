"""
downloader.py

Europe PMC downloader (robust version)

Upgrades over MVP:
- Uses cursorMark pagination (NOT page-based)
- Adds retry with exponential backoff
- Handles API instability safely
- Deduplicates PMCID/PMID results
- Streams full result set reliably
"""

import json
import time
import requests

# from corpus.query_builder import build_query


EUROPE_PMC_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


# -----------------------------
# minimal query
# -----------------------------

def build_query(manufacturer="GeneCopoeia"):
    return f'{manufacturer}'


# -----------------------------
# retry helper
# -----------------------------

def fetch_with_retry(params, retries=3, timeout=30):
    """
    Make Europe PMC request with retry + exponential backoff.
    """

    delay = 1

    for attempt in range(retries):
        try:
            r = requests.get(EUROPE_PMC_URL, params=params, timeout=timeout)
            r.raise_for_status()
            return r.json()

        except Exception as e:
            print(f"[retry {attempt+1}] error: {e}")

            if attempt == retries - 1:
                raise

            time.sleep(delay)
            delay *= 2


# -----------------------------
# main fetch
# -----------------------------

def fetch_articles(
    manufacturer,
    page_size=100,
    max_pages=1000,
    sort="P_PDATE_D desc",
):
    """
    Fetch articles using cursorMark pagination.

    Args:
        manufacturer (str): target entity (e.g. GeneCopoeia)
        page_size (int): results per request
        max_pages (int): safety cap on iterations
        sort (str): Europe PMC sort field

    Returns:
        list[dict]: article metadata
    """

    query = build_query(manufacturer)
    
    print(query)

    cursor = "*"
    seen = set()
    results = []

    for i in range(max_pages):
        params = {
            "query": query,
            "resultType": "core",
            "format": "json",
            "pageSize": page_size,
            "cursorMark": cursor,
            "sort": sort,
        }

        data = fetch_with_retry(params)

        hits = data.get("resultList", {}).get("result", [])
        next_cursor = data.get("nextCursorMark")

        print(f"[page {i+1}] hits={len(hits)} cursor={cursor}")
        print("hitCount:", data.get("hitCount"))

        if not hits:
            break

        for h in hits:
            
            pmcid = h.get("pmcid")
            pmid = h.get("pmid")

            key = pmcid or pmid
            if not key or key in seen:
                continue

            seen.add(key)

            results.append(
                {
                    "pmcid": pmcid,
                    "pmid": pmid,
                    
                    # identifiers
                    "doi": h.get("doi"),

                    # publication info
                    "title": h.get("title"),
                    "abstract": h.get("abstractText"),
                    "journal": h.get("journalTitle"),
                    "authors": h.get("authorString"),
                    "affiliation": h.get("affiliation"),
                    "year": (h.get("firstPublicationDate") or "")[:4],
                    "date": h.get("firstPublicationDate"),
                    "volume": h.get("journalVolume"),
                    "issue": h.get("issue"),
                    "pages": h.get("pageInfo"),

                    # impact
                    "cited_by_count": h.get("citedByCount"),

                    # article metadata
                    "pub_type": h.get("pubType"),
                    "is_open_access": h.get("isOpenAccess"),
                    # "has_pdf": h.get("hasPDF"),

                    # # future-proofing
                    # "keyword_list": h.get("keywordList"),
                    # "mesh_terms": h.get("meshHeadingList"),

                    "source": "europe_pmc",
                }
            )

        # stop conditions
        if not next_cursor or next_cursor == cursor:
            break

        cursor = next_cursor

    return results


# -----------------------------
# save
# -----------------------------

def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return text

    return (
        text.replace("\r\n", "\n")
            .replace("\r", "\n")
            .replace("\u2028", "\n")
            .replace("\u2029", "\n")
            .replace("\u00A0", " ")
            .replace("\u200B", "")
    )

def save_jsonl(path, records):
    """
    Save results to JSONL.
    """

    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in records:
            r = {k: clean_text(v) for k, v in r.items()}
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


# -----------------------------
# runner
# -----------------------------

def run_download(
    output_path="data/europe_pmc/genecopoeia.jsonl",
):
    """
    End-to-end execution.
    """

    data = fetch_articles("GeneCopoeia")

    save_jsonl(output_path, data)

    print(f"Saved {len(data)} records → {output_path}")


if __name__ == "__main__":
    run_download()