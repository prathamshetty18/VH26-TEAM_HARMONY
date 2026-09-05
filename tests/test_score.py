import sys, os
sys.path.insert(0, os.path.abspath("."))
from src.query_understanding import parse_query
from src.retrieval import retrieve

q = "show diagram for hydraulic press"
pq = parse_query(q)
print("Parsed:", pq)
chunks = retrieve(pq, k=5)
print(f"Retrieved {len(chunks)} chunks:")
for c in chunks:
    print(f"  Machine: {c.get('machine')} | Score: {c.get('score'):.4f} | Section: {c.get('section')} | Diag: {c.get('diagram_url')}")
