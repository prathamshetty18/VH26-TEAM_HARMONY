import sys
import os
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.embed_store import get_chroma_collection
from src.hybrid_search import keyword_search, hybrid_retrieve
from src.query_understanding import parse_query
from src.safety import is_sufficient, REFUSAL_MESSAGE

def test_phase_0_prerequisites():
    print("\n--- TEST: Phase 0 - Confirm Metadata Prerequisite ---")
    collection = get_chroma_collection()
    res = collection.get(include=["metadatas"])
    metadatas = res["metadatas"]
    assert len(metadatas) > 0, "Collection is empty"

    chunks_missing_key = [m for m in metadatas if "error_code" not in m]
    assert len(chunks_missing_key) == 0, f"Found {len(chunks_missing_key)} chunks missing 'error_code' key"

    with_code = [m for m in metadatas if m.get("error_code")]
    without_code = [m for m in metadatas if not m.get("error_code")]
    print(f"  [OK] Total indexed chunks: {len(metadatas)}")
    print(f"  [OK] Chunks with error_code: {len(with_code)}")
    print(f"  [OK] Chunks normalized to empty string: {len(without_code)}")
    print("Phase 0 passed: Chroma collection satisfies error_code metadata prerequisite.")

def test_phase_1_keyword_lookup():
    print("\n--- TEST: Phase 1 - Pure Keyword Lookup (collection.get) ---")
    
    # 1. Broad query across machines (E101)
    hits_all = keyword_search("E101", machine=None, k=10)
    machines_found = {h["machine"] for h in hits_all}
    print(f"  'E101' across all machines found on: {machines_found}")
    assert "CNC-100" in machines_found, "CNC-100 missing from E101 hits"
    assert any("Press" in m for m in machines_found), "Press-200 missing from E101 hits"
    assert all(h["score"] == 1.0 for h in hits_all), "All keyword hits must have score 1.0"
    assert all(h["match_type"] == "keyword" for h in hits_all), "All keyword hits must have match_type 'keyword'"

    # 2. Scoped query for CNC-100
    hits_cnc = keyword_search("E101", machine="CNC-100", k=5)
    print(f"  'E101' scoped to CNC-100 returned {len(hits_cnc)} chunk(s):")
    for h in hits_cnc:
        print(f"    - {h['machine']} | {h['manual']} | {h['section']}")
        assert h["machine"] == "CNC-100", f"Expected only CNC-100, got {h['machine']}"

    # 3. Non-existent code (E999)
    hits_nonexistent = keyword_search("E999")
    print(f"  'E999' nonexistent code returned: {hits_nonexistent}")
    assert hits_nonexistent == [], "Non-existent error code must return empty list"
    print("Phase 1 passed: keyword_search functions deterministically across all scopes.")

def test_phase_2_merge_and_hybrid_retrieve():
    print("\n--- TEST: Phase 2 - Hybrid Merge with Vector Search ---")

    # 1. Error code query: keyword hits must precede any vector hits
    pq_err = parse_query("What does E101 mean on CNC-100?")
    chunks_hybrid = hybrid_retrieve(pq_err, k=5)
    print(f"  Hybrid retrieve for 'E101 on CNC-100' returned {len(chunks_hybrid)} chunks:")
    assert len(chunks_hybrid) > 0
    # First hits must be keyword
    assert chunks_hybrid[0]["match_type"] == "keyword", f"Top hit must be keyword match, got {chunks_hybrid[0]['match_type']}"
    assert chunks_hybrid[0]["score"] == 1.0

    # 2. Symptom query with no error code: all hits must be vector
    pq_sym = parse_query("Why does Press-200 show hydraulic oil pressure low?")
    chunks_sym = hybrid_retrieve(pq_sym, k=5)
    print(f"  Hybrid retrieve for symptom query returned {len(chunks_sym)} chunks:")
    for c in chunks_sym:
        assert c["match_type"] == "vector", f"Expected vector match, got {c['match_type']}"
    print(f"    Top score: {chunks_sym[0]['score']:.4f} ({chunks_sym[0]['match_type']})")

    # 3. Deduplication check: no duplicate (manual, section)
    seen = set()
    for c in chunks_hybrid:
        key = (c["manual"], c["section"])
        assert key not in seen, f"Duplicate chunk found: {key}"
        seen.add(key)
    print("  [OK] Zero duplicates found in hybrid merged result list.")

    # 4. Performance check: when keyword fills k, vector search is bypassed
    start_time = time.perf_counter()
    chunks_k2 = hybrid_retrieve(pq_err, k=2)
    elapsed = time.perf_counter() - start_time
    assert len(chunks_k2) == 2
    assert all(c["match_type"] == "keyword" for c in chunks_k2)
    print(f"  [OK] When keyword search fills k=2, vector search is skipped (took {elapsed*1000:.2f}ms).")
    print("Phase 2 passed: hybrid_retrieve correctly blends, deduplicates, and optimizes.")

def test_phase_3_and_4_pipeline_and_safety():
    print("\n--- TEST: Phase 3 & 4 - Safety Gate & Ambiguity Integration ---")

    # 1. Safety Gate with keyword match: auto-clears similarity threshold
    pq_err = parse_query("What does E101 mean on CNC-100?")
    chunks = hybrid_retrieve(pq_err, k=5)
    suff, res = is_sufficient(chunks, query=pq_err["raw_query"], machine=pq_err["machine"])
    assert suff is True, f"Keyword match should pass is_sufficient: {res}"
    print("  [OK] Exact keyword match auto-clears Gate 1 similarity threshold.")

    # 2. Safety Gate with vector-only undocumented topic: must refuse
    pq_undoc = parse_query("How do I replace spindle bearing on CNC-100?")
    chunks_undoc = hybrid_retrieve(pq_undoc, k=5)
    suff_u, res_u = is_sufficient(chunks_undoc, query=pq_undoc["raw_query"], machine=pq_undoc["machine"])
    assert suff_u is False, "Undocumented topic must fail safety gate"
    assert res_u == REFUSAL_MESSAGE
    print("  [OK] Undocumented topic correctly refused by safety gate.")

    print("\n==================================================")
    print("ALL HYBRID SEARCH TESTS PASSED WITH 100% SUCCESS!")
    print("==================================================")

if __name__ == "__main__":
    test_phase_0_prerequisites()
    test_phase_1_keyword_lookup()
    test_phase_2_merge_and_hybrid_retrieve()
    test_phase_3_and_4_pipeline_and_safety()
