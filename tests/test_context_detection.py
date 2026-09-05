import sys
import os
import time
import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.embed_store import get_embedding_function
from src.query_understanding import (
    parse_query,
    fuzzy_match_machine,
    semantic_match_machine,
    parse_query_with_context
)

def test_phase_0_embedding_function():
    print("\n--- TEST: Phase 0 - Expose Embedding Function ---")
    fn = get_embedding_function()
    assert callable(fn), "Embedding function must be callable"
    embs = fn(["Test machine query"])
    assert len(embs) == 1 and len(embs[0]) == 384, f"Expected 384-dim vector, got {len(embs[0]) if embs else 0}"
    print("[OK] Phase 0 passed: get_embedding_function returns shared SentenceTransformer embedding function")

def test_phase_1_fuzzy_matching():
    print("\n--- TEST: Phase 1 - Fuzzy Matching Layer ---")
    assert fuzzy_match_machine("presss-200") == "Press-200", "presss-200 failed to match Press-200"
    assert fuzzy_match_machine("press  200") == "Press-200", "press  200 failed to match Press-200"
    assert fuzzy_match_machine("cnc-1000") is None or fuzzy_match_machine("coffee") is None
    assert fuzzy_match_machine("coffee") is None, "coffee should not match any machine"
    print("[OK] Phase 1 passed: Fuzzy matching resolves typos ('presss-200', 'press  200') and rejects 'coffee'")

def test_phase_2_semantic_matching():
    print("\n--- TEST: Phase 2 - Semantic Matching Layer ---")
    match1 = semantic_match_machine("the milling machine keeps stalling")
    print(f"  Descriptive 'the milling machine keeps stalling' -> {match1}")
    assert match1 in ("CNC-100", "CNC Milling Machine"), f"Expected CNC machine, got {match1}"
    
    match_unrelated = semantic_match_machine("where can I buy some hot coffee?")
    print(f"  Unrelated 'hot coffee' -> {match_unrelated}")
    assert match_unrelated is None, f"Expected None for unrelated query, got {match_unrelated}"
    print("[OK] Phase 2 passed: Semantic matching resolves descriptive queries and rejects unrelated text")

def test_phase_3_session_context_fallback():
    print("\n--- TEST: Phase 3 - Session Context Fallback ---")
    # 1. Fresh query without session memory
    r1 = parse_query_with_context("What does E101 mean?", session_memory=None)
    assert r1["machine"] is None, "Machine must be None without context"
    assert r1["machine_source"] is None, "Source must be None without match"

    # 2. Query with session memory and require_vague_language=False
    mem = {"last_machine": "CNC-100", "last_error_code": "E101"}
    r2 = parse_query_with_context("What does E101 mean?", session_memory=mem, require_vague_language=False)
    assert r2["machine"] == "CNC-100", f"Expected CNC-100, got {r2['machine']}"
    assert r2["machine_source"] == "session_context", f"Expected session_context, got {r2['machine_source']}"

    # 3. Query with session memory and require_vague_language=True
    r3 = parse_query_with_context("What does E101 mean?", session_memory=mem, require_vague_language=True)
    assert r3["machine"] is None, "Should not fall back when require_vague_language=True on explicit error code"

    # 4. Vague follow-up with require_vague_language=True
    r4 = parse_query_with_context("what about that?", session_memory=mem, require_vague_language=True)
    assert r4["machine"] == "CNC-100", f"Expected CNC-100, got {r4['machine']}"
    assert r4["error_code"] == "E101", f"Expected E101, got {r4['error_code']}"
    assert r4["machine_source"] == "session_context"

    # 5. Verify machine_source accurately reflects each layer
    assert parse_query_with_context("E101 on CNC-100")["machine_source"] == "alias"
    assert parse_query_with_context("E101 on presss-200")["machine_source"] == "fuzzy"
    assert parse_query_with_context("material handling belt stalled")["machine_source"] == "semantic"
    print("[OK] Phase 3 passed: parse_query_with_context correctly implements all 4 detection layers")

def test_phase_4_pipeline_api():
    print("\n--- TEST: Phase 4 - Pipeline Integration in /query ---")
    base_url = "http://127.0.0.1:8000"
    
    # Wait for server ready
    for _ in range(20):
        try:
            res = requests.get(f"{base_url}/machines", timeout=2)
            if res.status_code == 200:
                break
        except Exception:
            time.sleep(1)

    # 1. Fresh Session -> Ambiguity Prompt for ambiguous E101
    fresh_sid = f"fresh_test_{int(time.time())}"
    resp1 = requests.post(f"{base_url}/query", json={"message": "What does E101 mean?", "session_id": fresh_sid}).json()
    assert resp1.get("ambiguous") is True, "Fresh session with E101 must trigger ambiguity"
    print("[OK] 4A. Fresh session correctly triggers disambiguation for bare E101")

    # 2. Contextual Session: Discuss CNC-100 first, then bare E101
    ctx_sid = f"ctx_test_{int(time.time())}"
    # Turn 1: Discuss CNC-100
    resp2_1 = requests.post(f"{base_url}/query", json={"message": "What does E101 mean on CNC-100?", "session_id": ctx_sid}).json()
    assert resp2_1.get("ambiguous") is False
    assert resp2_1.get("machine_source") == "alias"
    
    # Turn 2: Ask bare E101 with session context active
    resp2_2 = requests.post(f"{base_url}/query", json={"message": "What does E101 mean?", "session_id": ctx_sid}).json()
    assert resp2_2.get("ambiguous") is False, "Context session should resolve E101 to active machine CNC-100"
    assert resp2_2.get("machine_source") == "session_context", f"Expected machine_source=session_context, got {resp2_2.get('machine_source')}"
    assert any("cnc" in s.get("manual", "").lower() for s in resp2_2.get("sources", [])), "Sources should be for CNC-100"
    print("[OK] 4B. Session context suppresses ambiguity and resolves directly for CNC-100")

    # 3. Fuzzy match in API query
    fuzzy_sid = f"fuzzy_test_{int(time.time())}"
    resp3 = requests.post(f"{base_url}/query", json={"message": "How do I fix presss-200?", "session_id": fuzzy_sid}).json()
    assert resp3.get("machine_source") == "fuzzy", f"Expected machine_source=fuzzy, got {resp3.get('machine_source')}"
    assert any("press" in s.get("manual", "").lower() for s in resp3.get("sources", [])), "Sources should be for Press-200"
    print("[OK] 4C. Fuzzy typos ('presss-200') resolve to Press-200 end-to-end")

    print("\n==================================================")
    print("ALL CONTEXT DETECTION PHASES PASSED WITH 100% SUCCESS!")
    print("==================================================")

if __name__ == "__main__":
    test_phase_0_embedding_function()
    test_phase_1_fuzzy_matching()
    test_phase_2_semantic_matching()
    test_phase_3_session_context_fallback()
    test_phase_4_pipeline_api()
