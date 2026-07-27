import json


sentences = []

with open(
        "data/europe_pmc/genecopoeia_sentences.jsonl",
        "r",
        encoding="utf-8-sig",
    ) as f:

    for line in f:
            record = json.loads(line)
            sentence = record.get("sentence", "")
            
            sentences.append(sentence)
    
with open("just_sentences.jsonl", "w", encoding="utf-8") as f:
        for s in sentences:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")