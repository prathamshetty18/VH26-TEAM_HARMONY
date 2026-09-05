import sys, os
sys.path.insert(0, os.path.abspath("."))

from src.query_understanding import parse_query
from src.retrieval import retrieve
from src.safety import is_sufficient, _extract_content_tokens

q = "Show diagram for hydraulic press"
pq = parse_query(q)
print("PQ:", pq)
chunks = retrieve(pq, k=5)
print(f"Retrieved {len(chunks)} chunks, top score: {chunks[0]['score'] if chunks else 0}")
tokens = _extract_content_tokens(q, machine=pq.get("machine"))
print("Tokens:", tokens)

suff, res = is_sufficient(chunks, query=q, machine=pq.get("machine"))
print("is_sufficient result:", suff, res if not suff else "PASSED")
