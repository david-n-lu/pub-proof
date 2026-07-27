"""
downloader.py

Backend for downloading publications from Europe PMC.

Responsibilities:
- Searches Europe PMC with manufacturer as the query
- Downloads publication metadata
- Handles pagination and retries
- Saves progress with checkpoints
- Exports downloaded results to project files
"""

import json
import time
import os
import requests


EUROPE_PMC_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


def build_query(manufacturer="GeneCopoeia"):
    return f"{manufacturer}"


def fetch_with_retry(params, retries=3, timeout=30):

    delay = 1

    for attempt in range(retries):

        try:
            r = requests.get(
                EUROPE_PMC_URL,
                params=params,
                timeout=timeout,
            )

            r.raise_for_status()

            return r.json()


        except Exception as e:

            print(
                f"[retry {attempt+1}] {e}"
            )

            if attempt == retries - 1:
                raise

            time.sleep(delay)
            delay *= 2



def get_total_hits(manufacturer):
    """
    Get total number of Europe PMC search results.
    """

    params = {
        "query": build_query(manufacturer),
        "resultType": "core",
        "format": "json",
        "pageSize": 1,
    }

    data = fetch_with_retry(params)

    return data.get(
        "hitCount",
        0
    )



def load_checkpoint(path):

    if os.path.exists(path):

        with open(path, "r") as f:
            return json.load(f)

    return {
        "cursor": "*",
        "downloaded": 0,
    }



def save_checkpoint(path, checkpoint):

    with open(path, "w") as f:
        json.dump(
            checkpoint,
            f
        )


def reset_checkpoint(path):
    """
    Reset the download checkpoint to its initial state.
    """

    save_checkpoint(
        path,
        {
            "cursor": "*",
            "downloaded": 0,
        },
    )


def delete_checkpoint(path):

    if os.path.exists(path):
        os.remove(path)



def erase_output_file(path):
    """
    Delete the output JSONL file if it exists.
    """

    if os.path.exists(path):
        os.remove(path)


def populate_seen_from_output(output_path):
    """
    Populate seen identifiers from an existing JSONL output file.

    Returns:
        set: identifiers already downloaded
    """

    seen = set()

    if not os.path.exists(output_path):
        return seen

    with open(
        output_path,
        "r",
        encoding="utf-8"
    ) as f:

        for line in f:

            if not line.strip():
                continue

            try:
                article = json.loads(line)

            except json.JSONDecodeError:
                continue


            key = (
                article.get("pmcid")
                or article.get("pmid")
                or article.get("doi")
                or article.get("id")
            )

            if key:
                seen.add(key)

    return seen


def fetch_articles_stream(
    manufacturer,
    output_path,
    checkpoint_path,
    page_size=100,
    max_pages=1000,
):

    query = build_query(manufacturer)

    checkpoint = load_checkpoint(
        checkpoint_path
    )

    cursor = checkpoint["cursor"]

    seen = populate_seen_from_output(
        output_path
    )

    saved = len(seen)

    searched = 0
    skipped = 0


    try:

        with open(
            output_path,
            "a",
            encoding="utf-8"
        ) as f:


            for page in range(max_pages):

                params = {
                    "query": query,
                    "resultType": "core",
                    "format": "json",
                    "pageSize": page_size,
                    "cursorMark": cursor,
                    "sort": "P_PDATE_D desc",
                }


                data = fetch_with_retry(params)


                hits = data.get(
                    "resultList",
                    {}
                ).get(
                    "result",
                    []
                )


                searched += len(hits)


                next_cursor = data.get(
                    "nextCursorMark"
                )


                print(f"[page {page + 1}] hits={len(hits)} cursor={cursor}")
                print("hitCount:", data.get("hitCount"))


                for h in hits:

                    key = (
                        h.get("pmcid")
                    )


                    if not key or key in seen:
                        skipped += 1
                        continue
                    

                    seen.add(key)


                    article = {
                        "pmcid": h.get("pmcid"),
                        "pmid": h.get("pmid"),
                        "doi": h.get("doi"),

                        "title": h.get("title"),
                        "abstract": h.get("abstractText"),

                        "journal": h.get("journalInfo", {}).get("journal", {}).get("title"),
                        "journal_medline": h.get("journalInfo", {}).get("journal", {}).get("medlineAbbreviation"),
                        "journal_iso": h.get("journalInfo", {}).get("journal", {}).get("isoabbreviation"),

                        "authors": h.get("authorString"),
                        "affiliation": h.get("affiliation"),

                        "year": h.get("firstPublicationDate", "")[:4],

                        "date": h.get("firstPublicationDate"),
                        "volume": h.get("journalInfo", {}).get("volume"),
                        "issue": h.get("journalInfo", {}).get("issue"),

                        "cited_by_count": h.get("citedByCount"),

                        "is_open_access": h.get("isOpenAccess"),

                        "source": "europe_pmc",
                    }


                    f.write(
                        json.dumps(
                            article,
                            ensure_ascii=False
                        )
                        + "\n"
                    )


                    saved += 1


                f.flush()


                if not next_cursor or next_cursor == cursor:
                    break

                cursor = next_cursor

                save_checkpoint(
                    checkpoint_path,
                    {
                        "cursor": cursor,
                        "downloaded": saved,
                    }
                )


    except KeyboardInterrupt:
        print("Interrupted")
        raise

    except Exception as e:
        print(f"Error occurred: {e}")
        raise

    finally:
        save_checkpoint(
            checkpoint_path,
            {
                "cursor": cursor,
                "downloaded": saved,
            }
        )


    return {
        "searched": searched,
        "saved": saved,
        "skipped": skipped,
    }