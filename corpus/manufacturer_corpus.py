"""
manufacturer_corpus.py

Builds a sentence-level corpus from Europe PMC articles
containing mentions of a manufacturer.

Designed to work with PySide6 UI through callbacks.
"""

import json
import re
import requests
import os

from corpus.xml_parser import parse_pmc_article
from corpus.sentence_extractor import get_sentences_with_manufacturer


EUROPE_PMC_XML = (
    "https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
)


# ---------------------------------------------------------
# Callback helpers
# ---------------------------------------------------------

def log_message(log_callback, message: str):
    """
    Send log messages to UI or console.
    """
    if log_callback:
        log_callback(message)


def update_progress(progress_callback, current: int, total: int):
    """
    Update progress bar.

    Expected callback:
        callback(current, total)
    """
    if progress_callback:
        progress_callback(current, total)


# ---------------------------------------------------------
# Europe PMC XML fetching
# ---------------------------------------------------------

def fetch_xml(pmcid: str) -> str:
    """
    Fetch full-text XML from Europe PMC.

    Note:
        Currently not used because parse_pmc_article()
        handles retrieval.
    """

    url = EUROPE_PMC_XML.format(pmcid=pmcid)

    response = requests.get(
        url,
        timeout=30
    )

    response.raise_for_status()

    return response.text


# ---------------------------------------------------------
# Text utilities
# ---------------------------------------------------------

def split_sentences(text: str):
    """
    Split text into sentences.
    """

    return re.split(
        r"(?<=[.!?])\s+",
        text
    )


def normalize(text: str):
    """
    Normalize text for matching.
    """

    return re.sub(
        r"\s+",
        " ",
        text.lower()
    ).strip()


# ---------------------------------------------------------
# Manufacturer sentence extraction
# ---------------------------------------------------------

def extract_manufacturer_sentences(
    full_text: str,
    pmcid: str,
    manufacturer: str = "GeneCopoeia"
):
    """
    Extract sentences containing manufacturer.

    Returns:
        [
            {
                "pmcid": "...",
                "manufacturer": "...",
                "sentence": "..."
            }
        ]
    """

    sentences = split_sentences(full_text)

    manufacturer_norm = normalize(manufacturer)

    results = []

    for sentence in sentences:

        if manufacturer_norm in normalize(sentence):

            results.append(
                {
                    "pmcid": pmcid,
                    "manufacturer": manufacturer,
                    "sentence": sentence.strip()
                }
            )

    return results


# ---------------------------------------------------------
# JSONL utilities
# ---------------------------------------------------------

def save_jsonl(path, records):
    """
    Write JSONL file from scratch.
    """

    with open(
        path,
        "w",
        encoding="utf-8",
        newline="\n"
    ) as f:

        for record in records:
            f.write(
                json.dumps(
                    record,
                    ensure_ascii=False
                )
                + "\n"
            )


def flush_jsonl(path, records):
    """
    Append records to JSONL file.
    """

    with open(
        path,
        "a",
        encoding="utf-8",
        newline="\n"
    ) as f:

        for record in records:
            f.write(
                json.dumps(
                    record,
                    ensure_ascii=False
                )
                + "\n"
            )


def count_lines(path):
    """
    Count JSONL records for progress tracking.
    """

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        return sum(
            1 for _ in f
        )



# ---------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------

def build_manufacturer_sentence_corpus(
    input_path: str,
    output_path: str,
    manufacturer: str = "GeneCopoeia",
    documents_to_process: int | None = None,
    batch_size: int = 100,
    clear_output: bool = True,
    start_line=None,
    resume=True,

    # UI callbacks
    progress_callback=None,
    log_callback=None,
    finished_callback=None,
    should_cancel=None,
    current_line_callback=None,
):
    """
    Build a sentence-level corpus containing only sentences
    mentioning a manufacturer.

    Steps:
        1. Read Europe PMC JSONL
        2. Parse PMC full text
        3. Extract manufacturer sentences
        4. Save JSONL incrementally

    Callbacks:

        progress_callback(current, total)
            Updates progress bar

        log_callback(message)
            Sends text logs to UI

        finished_callback()
            Called when complete

        should_cancel()
            Returns True if user pressed cancel
    """


    # -----------------------------------------------------
    # Prepare output
    # -----------------------------------------------------

    checkpoint_path = get_checkpoint_path(
        output_path
    )


    if clear_output:

        open(
            output_path,
            "w",
            encoding="utf-8"
        ).close()

        delete_checkpoint(
            checkpoint_path
        )


    # -----------------------------------------------------
    # Determine starting position
    # -----------------------------------------------------

    checkpoint_path = get_checkpoint_path(
        output_path
    )


    if resume and start_line is None:

        last_completed = load_checkpoint(
            checkpoint_path
        )

        start_line = last_completed + 1

    else:

        start_line = start_line or 1


    # -----------------------------------------------------
    # Calculate progress size
    # -----------------------------------------------------

    total_lines = count_lines(input_path)

    remaining = total_lines - start_line

    if documents_to_process is None:
        total_lines = remaining
    else:
        total_lines = min(remaining, documents_to_process)

    processed_count = 0

    buffer = []


    # -----------------------------------------------------
    # Read input JSONL
    # -----------------------------------------------------

    with open(
        input_path,
        "r",
        encoding="utf-8"
    ) as f:


        end_line = None

        if documents_to_process is not None:
            end_line = start_line + documents_to_process - 1


        for index, line in enumerate(f):

            line_number = index + 1


            # ---------------------------------------------
            # Resume support
            # ---------------------------------------------

            if line_number < start_line:
                continue


            # ---------------------------------------------
            # Max document limit
            # ---------------------------------------------

            if (
                end_line
                and line_number > end_line
            ):
                break


            # -----------------------------------------------------
            # Update current processing position
            # Used for auto-resume after failures
            # -----------------------------------------------------
            
            if current_line_callback:
                current_line_callback(line_number)


            # ---------------------------------------------
            # Cancellation
            # ---------------------------------------------

            if (
                should_cancel
                and should_cancel()
            ):

                log_message(
                    log_callback,
                    "[CANCELLED] Saving current batch..."
                )

                if buffer:

                    flush_jsonl(
                        output_path,
                        buffer
                    )

                    save_checkpoint(
                        checkpoint_path,
                        line_number
                    )

                return


            # ---------------------------------------------
            # Parse JSON record
            # ---------------------------------------------

            record = json.loads(line)

            pmcid = record.get(
                "pmcid"
            )


            sentences = []


            # ---------------------------------------------
            # Extract sentences
            # ---------------------------------------------

            if pmcid:

                try:

                    xml_result = parse_pmc_article(
                        pmcid
                    )


                    full_text = xml_result.get(
                        "full_text"
                    )


                    if full_text:

                        sentences = (
                            get_sentences_with_manufacturer(
                                full_text=full_text,
                                manufacturer=manufacturer
                            )
                        )


                except Exception as e:

                    log_message(
                        log_callback,
                        f"[ERROR] {pmcid}: {e}"
                    )


            # ---------------------------------------------
            # Deduplicate sentences
            # ---------------------------------------------

            seen = set()

            for sentence in sentences:

                sentence = sentence.strip()


                if sentence in seen:
                    continue


                seen.add(sentence)


                new_record = record.copy()

                new_record["sentence"] = sentence


                buffer.append(
                    new_record
                )


            # ---------------------------------------------
            # Progress update
            # ---------------------------------------------

            processed_count += 1


            update_progress(
                progress_callback,
                processed_count,
                total_lines
            )


            log_message(
                log_callback,
                (
                    f"[PROCESSED] "
                    f"{line_number} | {pmcid}"
                )
            )


            log_message(
                log_callback,
                (
                    f"[RESULT] "
                    f"{pmcid} → "
                    f"{len(sentences)} sentences"
                )
            )


            # ---------------------------------------------
            # Batch flush
            # ---------------------------------------------

            if (
                processed_count % batch_size == 0
            ):

                if buffer:

                    flush_jsonl(
                        output_path,
                        buffer
                    )


                    save_checkpoint(
                        checkpoint_path,
                        line_number
                    )


                    buffer.clear()


                log_message(
                    log_callback,
                    (
                        f"[FLUSH] "
                        f"Saved batch at sentence {line_number}"
                    )
                )


    # -----------------------------------------------------
    # Final flush
    # -----------------------------------------------------

    if buffer:

        flush_jsonl(
            output_path,
            buffer
        )

        save_checkpoint(
            checkpoint_path,
            line_number
        )


    log_message(
        log_callback,
        "[COMPLETE] Manufacturer corpus created"
    )


    if finished_callback:

        finished_callback()



# ---------------------------------------------------------
# Checkpointing if a crash or exception occur
# ---------------------------------------------------------


CHECKPOINT_SUFFIX = ".checkpoint.json"


def get_checkpoint_path(output_path):
    return output_path + CHECKPOINT_SUFFIX


def save_checkpoint(path, line_number):
    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            {
                "last_completed_line": line_number
            },
            f
        )


def load_checkpoint(path):
    if not os.path.exists(path):
        return 0

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:
        data = json.load(f)

    return data.get(
        "last_completed_line",
        0
    )


def delete_checkpoint(path):
    if os.path.exists(path):
        os.remove(path)




# ---------------------------------------------------------
# Quick test
# ---------------------------------------------------------

if __name__ == "__main__":

    clear_output = True
    start_line = 0


    build_manufacturer_sentence_corpus(
        input_path="data/europe_pmc/genecopoeia_articles.jsonl",
        output_path="data/europe_pmc/genecopoeia_sentences_UI_test.jsonl",

        manufacturer="GeneCopoeia",

        # processing
        documents_to_process=100,
        batch_size=100,

        # resume settings
        clear_output=clear_output,
        start_line=start_line,

        # console callbacks
        log_callback=print,

        progress_callback=lambda current, total: (
            print(
                f"[PROGRESS] {current}/{total}"
            )
        ),

        finished_callback=lambda: (
            print(
                "[DONE]"
            )
        ),
    )