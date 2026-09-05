import requests

base_url = "http://127.0.0.1:8000"

queries = [
    "What does H201 mean on Hydraulic Press?",
    "What does H205 mean on Hydraulic Press?",
    "What does H312 mean on Hydraulic Press?",
    "How do I fix H201 on HP-2200?",
    "What does E101 mean on Press-200?",
    "Why does Press-200 show hydraulic oil pressure low?",
    "What does E202 mean on Press-200?",
    "What does E203 mean on Press-200?",
    "hydraulic press",
    "Show diagram for hydraulic press",
    "hydraulic press diagram",
    "diagram of hydraulic press"
]

for q in queries:
    r = requests.post(f"{base_url}/query", json={"message": q}).json()
    diags = r.get("diagrams", [])
    src_diags = [s.get("diagram_url") for s in r.get("sources", []) if s.get("diagram_url")]
    amb = r.get("ambiguous")
    ans = (r.get("answer") or "")[:50].replace("\n", " ")
    print(f"Query: {q!r}")
    print(f"  Ambiguous: {amb} | Diagrams: {len(diags)} | Ans: {ans}")
    for d in diags:
        print(f"    -> {d.get('title')} ({d.get('url')})")
    print(f"  Source URLs: {src_diags}\n")
