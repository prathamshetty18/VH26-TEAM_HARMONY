import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_machine_detection():
    print("=" * 65)
    print("LIVE TESTING AUTOMATIC MACHINE MODEL DETECTION FROM CONTEXT")
    print("=" * 65)

    # ----------------------------------------------------
    # LAYER 1: ALIAS MATCHING
    # ----------------------------------------------------
    print("\n[LAYER 1: EXACT & ALIAS MATCHING]")
    alias_queries = [
        ("What does E101 mean on CNC-100?", "CNC-100"),
        ("Why is HP-2200 losing pressure?", "Hydraulic Press"),
        ("Error R101 on robotarm", "RobotArm-300"),
        ("What is the speed setting on CB-4400?", "Conveyor Belt System")
    ]
    for q, expected in alias_queries:
        r = requests.post(f"{BASE_URL}/query", json={"message": q, "session_id": f"alias_{int(time.time()*1000)}"}).json()
        src = r.get("machine_source")
        machine = r.get("sources", [{}])[0].get("machine") if r.get("sources") else None
        print(f"  Query: '{q}'")
        print(f"    -> Detected Source: {src} | Machine: {machine} | Expected: {expected}")
        assert src == "alias", f"Expected source 'alias', got {src}"

    # ----------------------------------------------------
    # LAYER 2: FUZZY MATCHING (TYPOS & NEAR-MISSES)
    # ----------------------------------------------------
    print("\n[LAYER 2: FUZZY MATCHING (TYPOS & NEAR-MISSES)]")
    fuzzy_queries = [
        ("How do I fix presss-200?", "Press-200"),
        ("press  200 cylinder guide fault", "Press-200"),
        ("robotic-armm axis error", "RobotArm-300"),
        ("conveyorr belt tracking problem", "Conveyor Belt System")
    ]
    for q, expected in fuzzy_queries:
        r = requests.post(f"{BASE_URL}/query", json={"message": q, "session_id": f"fuzzy_{int(time.time()*1000)}"}).json()
        src = r.get("machine_source")
        machine = r.get("sources", [{}])[0].get("machine") if r.get("sources") else None
        print(f"  Query: '{q}'")
        print(f"    -> Detected Source: {src} | Machine: {machine} | Expected: {expected}")
        assert src == "fuzzy", f"Expected source 'fuzzy', got {src}"

    # ----------------------------------------------------
    # LAYER 3: SEMANTIC MATCHING (DESCRIPTIVE QUERIES, NO MACHINE NAME)
    # ----------------------------------------------------
    print("\n[LAYER 3: SEMANTIC MATCHING (ZERO MACHINE NAMES)]")
    semantic_queries = [
        ("the metal cutting milling spindle keeps overheating", "CNC-100"),
        ("the heavy stamping ram is losing tonnage pressure", "Hydraulic Press"),
        ("material handling transport belt has stalled and stopped moving", "Conveyor Belt System"),
        ("the 6-axis joint articulation has severe tracking deviation", "RobotArm-300")
    ]
    for q, expected in semantic_queries:
        r = requests.post(f"{BASE_URL}/query", json={"message": q, "session_id": f"sem_{int(time.time()*1000)}"}).json()
        src = r.get("machine_source")
        machine = r.get("sources", [{}])[0].get("machine") if r.get("sources") else None
        print(f"  Query: '{q}'")
        print(f"    -> Detected Source: {src} | Machine: {machine} | Expected: {expected}")
        assert src in ("semantic", "alias"), f"Expected semantic/alias, got {src}"

    # ----------------------------------------------------
    # LAYER 4: SESSION CONTEXT FALLBACK (MULTI-TURN DIALOGUE)
    # ----------------------------------------------------
    print("\n[LAYER 4: SESSION CONTEXT FALLBACK & DISAMBIGUATION SUPPRESSION]")
    
    # Test 4A: Fresh session without context -> E101 MUST trigger disambiguation prompt
    fresh_session = f"session_fresh_{int(time.time())}"
    r_fresh = requests.post(f"{BASE_URL}/query", json={"message": "What does E101 mean?", "session_id": fresh_session}).json()
    print(f"  Turn 1 (No context): 'What does E101 mean?'")
    print(f"    -> Ambiguous: {r_fresh.get('ambiguous')}")
    print(f"    -> Prompt: {r_fresh.get('answer')[:75]}...")
    assert r_fresh.get("ambiguous") is True, "Fresh session for E101 must trigger disambiguation"

    # Test 4B: Context active with CNC-100 -> E101 automatically detected from context!
    ctx_session_cnc = f"session_cnc_{int(time.time())}"
    # Turn 1: Discuss CNC-100
    r1 = requests.post(f"{BASE_URL}/query", json={"message": "What is the recommended maintenance for CNC-100?", "session_id": ctx_session_cnc}).json()
    print(f"\n  Turn 1: 'What is the recommended maintenance for CNC-100?'")
    print(f"    -> Machine detected: CNC-100 (Source: {r1.get('machine_source')})")

    # Turn 2: User asks bare 'What does E101 mean?' WITHOUT mentioning CNC-100
    r2 = requests.post(f"{BASE_URL}/query", json={"message": "What does E101 mean?", "session_id": ctx_session_cnc}).json()
    print(f"  Turn 2: 'What does E101 mean?' (bare error code, no machine name)")
    print(f"    -> Ambiguous: {r2.get('ambiguous')} (Disambiguation successfully SUPPRESSED)")
    print(f"    -> Machine Source: {r2.get('machine_source')}")
    top_machine = r2.get("sources", [{}])[0].get("machine")
    top_manual = r2.get("sources", [{}])[0].get("manual")
    print(f"    -> Resolved Machine: {top_machine} | Manual: {top_manual}")
    assert r2.get("ambiguous") is False, "Session context must suppress disambiguation"
    assert r2.get("machine_source") == "session_context", f"Expected machine_source 'session_context', got {r2.get('machine_source')}"
    assert "cnc" in top_manual.lower(), f"Expected CNC manual, got {top_manual}"

    # Test 4C: Context active with Press-200 -> E101 automatically detected from context as Press-200!
    ctx_session_press = f"session_press_{int(time.time())}"
    # Turn 1: Discuss Press-200
    requests.post(f"{BASE_URL}/query", json={"message": "Show troubleshooting for Press-200", "session_id": ctx_session_press}).json()
    # Turn 2: User asks bare 'What does E101 mean?'
    r_press2 = requests.post(f"{BASE_URL}/query", json={"message": "What does E101 mean?", "session_id": ctx_session_press}).json()
    print(f"\n  Turn 1: Discuss Press-200")
    print(f"  Turn 2: 'What does E101 mean?' (bare error code in Press-200 session)")
    print(f"    -> Ambiguous: {r_press2.get('ambiguous')} (Suppressed)")
    print(f"    -> Machine Source: {r_press2.get('machine_source')}")
    press_manual = r_press2.get("sources", [{}])[0].get("manual")
    print(f"    -> Resolved Manual: {press_manual}")
    assert r_press2.get("ambiguous") is False
    assert r_press2.get("machine_source") == "session_context"
    assert "press" in press_manual.lower()

    # Test 4D: Vague follow-up phrasing ("what about the causes?")
    r_vague = requests.post(f"{BASE_URL}/query", json={"message": "what are the main causes?", "session_id": ctx_session_press}).json()
    print(f"\n  Turn 3: 'what are the main causes?' (completely vague follow-up)")
    print(f"    -> Machine Source: {r_vague.get('machine_source')}")
    print(f"    -> Sources: {[s['section'] for s in r_vague.get('sources', [])][:2]}")
    assert r_vague.get("machine_source") == "session_context"

    print("\n" + "=" * 65)
    print("RESULTS: ALL 4 AUTOMATIC CONTEXT DETECTION LAYERS FULLY OPERATIONAL!")
    print("=" * 65)

if __name__ == "__main__":
    test_machine_detection()
