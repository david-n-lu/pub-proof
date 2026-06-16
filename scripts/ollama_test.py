import requests

def ask_ollama(prompt, model="llama3"):
    r = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False
        }
    )
    return r.json()["response"]

text = "qRT-PCR assays were conducted using BlazeTaq SYBR Green Mix (GeneCopoeia)"

prompt = f"Extract all products and kits from this sentence:\n\n{text}"

print(ask_ollama(prompt))