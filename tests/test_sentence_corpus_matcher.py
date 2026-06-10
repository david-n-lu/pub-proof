import csv
import json

from matching.sentence_corpus_matcher import match_corpus, match_sentence
from matching.citation import cite_from_europe_pmc
from matching.product_map import build_product_map, build_alias_index

def test_matcher(
    manufacturer: str = "GeneCopoeia",
    sentence_corpus_path: str = "tests/data/genecopoeia_sentences.jsonl",
    product_map: dict = None,
    alias_map: dict = None,
    output_csv: str = "tests/data/matcher_results.csv",
    min_score: int = 3,
):
    """
    Run matcher against a sentence corpus and export results for inspection.
    """


    matches = match_corpus(
        sentence_corpus_path=sentence_corpus_path,
        product_map=product_map,
        alias_map=alias_map,
        min_score=min_score,
    )

    with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)

        writer.writerow([
            "manufacturer",
            "product_name",
            "sku",
            "url",
            "citation",
            "matched_aliases",
            "score",
            "sentence",
        ])


        for m in matches:
            id = m.get("pmcid").replace("PMC","")

            writer.writerow([
                manufacturer,
                m.get("product_name"),
                m.get("sku"),
                f"https://europepmc.org/article/PMC/{id}",
                "", # cite_from_europe_pmc(id),
                m.get("aliases"),
                m.get("score"),
                m.get("sentence"),
            ])

    print(f"Exported {len(matches):,} matches to {output_csv}")


def debug_match_sentence(sentence: str, alias_map: dict, max_alias_words: int = 8):
    print("=" * 80)
    print("SENTENCE:")
    print(sentence)

    matches = match_sentence(
        sentence=sentence,
        alias_map=alias_map,
        max_alias_words=max_alias_words,
    )

    print("\nMATCHES:")

    if not matches:
        print("NONE")
        return

    for sku, hits in matches.items():
        print(f"\nSKU: {sku}")
        for h in hits:
            print(f"  - alias: {h['alias']}")
            print(f"    score: {h['score']}")


if __name__ == "__main__":

    alias_path = "data/raw_products"

    product_map = build_product_map(alias_path)
    print("Built product map")

    alias_map = build_alias_index(product_map)
    print("Build alias map")

    test_matcher(product_map=product_map, alias_map=alias_map)

    # sentence = "First-strand cDNA synthesis was performed with 1 μg total RNA using the SureScript™ First-Strand cDNA Synthesis Kit (GeneCopoeia, USA), incorporating oligo(dT) primers and RNase inhibitor."
    # debug_match_sentence(sentence=sentence, alias_map=alias_map)