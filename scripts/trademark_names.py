import json
from matching.normalization import normalize, normalize_for_matching

trademark_names = [
    "OmicsArray™",
    "Luc-Pair™",
    "EndoFectin™",
    "CRISPR-Fectin™",
    "Fast-Fusion™",
    "CoolCutter™",
    "ExoSure™",
    "ExoCt™",
    "SuperCut™",
    "IndelCheck™",
    "Smart-Join™",
    "Genome-TALER™",
    "GeneHero™",
    "VividFISH™",
    "Lenti-Pac™",
    "Lentifect™",
    "AAVPrime™",
    "EZRecombinase™",
    "CytoCt™",
    "All-in-One™",
    "SureScript™",
    "BlazeTaq™",
    "SYBR®",
    "ExProfile™",
    "miProfile™",
    "miTarget™",
    "OmicsLink™",
    "GLuc-ON™",
    "MiExpress™",
    "OmicsLink™",
    "RNAzol®",
    "AccelerRT®",
    "UltraHiPF®",
    "NileHiFi®",
]



if __name__ == "__main__":
    sentence_corpus_path = "data/europe_pmc/genecopoeia_sentences.jsonl"
    product_map_path = "data/raw_products"

    sentences = []
    with open(sentence_corpus_path, "r", encoding="utf-8") as f:

        for line in f:
            record = json.loads(line)
            sentences.append(record.get("sentence", ""))
    
    trademark_names_norm = [normalize_for_matching(name) for name in trademark_names]

    trademark_names_dict = dict(zip(trademark_names_norm, trademark_names))

    statistics = {}
    count = 0

    print(len(sentences))

    for sentence in sentences:
        words = normalize_for_matching(sentence[:-1]).split()

        for word in words:
            if word in trademark_names_norm:
                full_name = trademark_names_dict.get(word)

                if full_name not in statistics:
                    statistics[full_name] = 0
                
                statistics[full_name] += 1
                count += 1
    
    for name, value in statistics.items():
        print(f"{name}: {value}")
    
    print(f"{count} sentences with trademark name")

    print(len(trademark_names))
    print(len(statistics))
    

