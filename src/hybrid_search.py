"""
Phase 2 (Bonus) — Hybrid Keyword + Vector Search.
Provides exact keyword pre-filtering for error codes alongside vector similarity search.
Deterministic keyword hits rank first with score 1.0 and match_type='keyword'.
Vector search fills in remaining slots for symptoms and queries without error codes.
"""

from typing import List, Dict, Any, Optional
import os
import sys
import re

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.embed_store import get_chroma_collection
from src.retrieval import retrieve

def keyword_search(error_code: str, machine: Optional[Any] = None, k: int = 5) -> List[Dict[str, Any]]:
    """
    Performs deterministic metadata-filtered retrieval for an exact error code using Chroma's collection.get().
    Bypasses embedding models entirely.
    All returned chunks receive score 1.0 and match_type 'keyword'.
    If machine is None, returns hits across ALL machines documenting this code (for ambiguity detection).
    """
    if not error_code or not str(error_code).strip():
        return []

    code_str = str(error_code).strip().upper()
    collection = get_chroma_collection()

    # Cross-model routing for Hydraulic Press if needed:
    # E101, E202, E203 exist in Press-200 (press200.txt)
    # H-series error codes exist in Hydraulic Press (presshp2200.txt)
    target_machine = machine
    if target_machine in ("Hydraulic Press", "Press-200"):
        if code_str in ("E101", "E202", "E203"):
            target_machine = "Press-200"
        elif code_str.startswith("H") or code_str.startswith("SYM"):
            target_machine = "Hydraulic Press"

    if target_machine:
        if isinstance(target_machine, (list, tuple, set)):
            where_clause = {
                "$and": [
                    {"error_code": {"$eq": code_str}},
                    {"machine": {"$in": list(target_machine)}}
                ]
            }
        else:
            where_clause = {
                "$and": [
                    {"error_code": {"$eq": code_str}},
                    {"machine": {"$eq": target_machine}}
                ]
            }
    else:
        where_clause = {"error_code": {"$eq": code_str}}

    try:
        res = collection.get(
            where=where_clause,
            include=["documents", "metadatas"]
        )
    except Exception as e:
        # If query fails or collection is empty, return empty list gracefully
        return []

    documents = res.get("documents") or []
    metadatas = res.get("metadatas") or []

    formatted_results = []
    for doc, meta in zip(documents, metadatas):
        page_val = None
        page_raw = meta.get("page")
        if page_raw is not None and str(page_raw).strip():
            try:
                page_val = int(str(page_raw).strip())
            except ValueError:
                m = re.search(r"\d+", str(page_raw))
                if m:
                    page_val = int(m.group(0))

        diag_url = meta.get("diagram_url")
        diag_title = meta.get("diagram_title")
        diag_caption = meta.get("diagram_caption")

        formatted_results.append({
            "text": doc,
            "machine": meta.get("machine"),
            "model": meta.get("model"),
            "manual": meta.get("manual"),
            "section": meta.get("section"),
            "page": page_val,
            "error_code": meta.get("error_code") if meta.get("error_code") != "" else None,
            "diagram_url": diag_url if diag_url else None,
            "diagram_title": diag_title if diag_title else None,
            "diagram_caption": diag_caption if diag_caption else None,
            "score": 1.0,
            "distance": 0.0,
            "score_type": "keyword_exact",
            "match_type": "keyword"
        })

    return formatted_results[:k]

def hybrid_retrieve(parsed_query: Dict[str, Any], k: int = 5) -> List[Dict[str, Any]]:
    """
    Blends deterministic keyword search and semantic vector search:
    1. If error_code is present, executes keyword_search() first.
    2. If keyword results satisfy k, vector search is completely bypassed.
    3. If slots remain (or query is symptom-based), vector search fills remaining slots.
    4. Deduplicates chunks by (manual, section).
    """
    error_code = parsed_query.get("error_code")
    machine = parsed_query.get("machine")

    keyword_chunks = []
    if error_code:
        fetch_kw_k = 20 if not machine else k
        keyword_chunks = keyword_search(error_code=error_code, machine=machine, k=fetch_kw_k)

    remaining_slots = k - len(keyword_chunks)

    # Optimization: If keyword search alone filled all requested slots, bypass vector search completely
    if remaining_slots <= 0:
        return keyword_chunks if not machine else keyword_chunks[:k]

    # Vector search fills remaining slots
    vector_fetch_k = remaining_slots + 5
    vector_chunks = retrieve(parsed_query, k=vector_fetch_k)

    # Tag vector chunks with match_type
    for c in vector_chunks:
        if "match_type" not in c:
            c["match_type"] = "vector"

    # Deduplicate by (manual, section)
    seen_keys = {(c.get("manual"), c.get("section")) for c in keyword_chunks}
    merged_results = list(keyword_chunks)

    for c in vector_chunks:
        key = (c.get("manual"), c.get("section"))
        if key not in seen_keys:
            seen_keys.add(key)
            merged_results.append(c)
            if len(merged_results) >= k:
                break

    return merged_results[:k]

if __name__ == "__main__":
    print("--- Testing Keyword Search ---")
    hits_e101 = keyword_search("E101")
    print(f"E101 hits across machines ({len(hits_e101)}):")
    for h in hits_e101:
        print(f"  {h['machine']} | {h['manual']} | {h['section']} | Score: {h['score']} ({h['match_type']})")

    hits_e101_cnc = keyword_search("E101", machine="CNC-100")
    print(f"\nE101 hits for CNC-100 ({len(hits_e101_cnc)}):")
    for h in hits_e101_cnc:
        print(f"  {h['machine']} | {h['manual']} | {h['section']} | Score: {h['score']} ({h['match_type']})")

    hits_e999 = keyword_search("E999")
    print(f"\nE999 hits (expected 0): {len(hits_e999)}")
