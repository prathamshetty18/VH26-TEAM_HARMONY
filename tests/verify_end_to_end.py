import requests

def test_endpoints():
    print("--- 1. Testing Vite Frontend & SVG Static Assets ---")
    r1 = requests.get("http://localhost:5173/")
    assert r1.status_code == 200, f"Frontend returned {r1.status_code}"
    print("  [OK] Vite Dev server serving on http://localhost:5173/")

    r2 = requests.get("http://localhost:5173/diagrams/hydraulic_press_manifold.svg")
    assert r2.status_code == 200 and "<svg" in r2.text, "Vite failed to serve hydraulic press SVG"
    print("  [OK] Vite serving hydraulic_press_manifold.svg")

    r3 = requests.get("http://127.0.0.1:8000/static/diagrams/hydraulic_press_manifold.svg")
    assert r3.status_code == 200 and "<svg" in r3.text, "Backend static failed to serve SVG"
    print("  [OK] Backend /static serving hydraulic_press_manifold.svg")

    r4 = requests.get("http://127.0.0.1:8000/diagrams/hydraulic_press_manifold.svg")
    assert r4.status_code == 200 and "<svg" in r4.text, "Backend /diagrams endpoint failed to serve SVG"
    print("  [OK] Backend /diagrams serving hydraulic_press_manifold.svg")

    print("\n--- 2. Testing Diagram Retrieval Queries ---")
    cases = [
        {"message": "Show diagram for hydraulic press", "session_id": "test_e2e_1"},
        {"message": "hydraulic press diagram", "session_id": "test_e2e_2"},
        {"message": "diagram of hydraulic press", "session_id": "test_e2e_3"},
        {"message": "What does H201 mean on Hydraulic Press?", "session_id": "test_e2e_4"},
        {"message": "What does H205 mean on Hydraulic Press?", "session_id": "test_e2e_5"},
        {"message": "What does H312 mean on Hydraulic Press?", "session_id": "test_e2e_6"},
        {"message": "How do I fix H201 on HP-2200?", "session_id": "test_e2e_7"},
        {"message": "What does E101 mean on Press-200?", "session_id": "test_e2e_8"},
        {"message": "Why does Press-200 show hydraulic oil pressure low?", "session_id": "test_e2e_9"},
        {"message": "What does E101 mean?", "machine_filter": "Hydraulic Press", "session_id": "test_e2e_10"},
        {"message": "show diagram", "machine_filter": "Hydraulic Press", "session_id": "test_e2e_11"},
        {"message": "show schematic", "machine_filter": "Press-200", "session_id": "test_e2e_12"},
    ]

    for c in cases:
        r = requests.post("http://127.0.0.1:8000/query", json=c)
        assert r.status_code == 200
        data = r.json()
        assert not data.get("ambiguous"), f"Query unexpectedly ambiguous: {c['message']}"
        diags = data.get("diagrams", [])
        sources = data.get("sources", [])
        assert len(diags) > 0, f"No diagrams returned for query: {c['message']}"
        is_press200 = "Press-200" in c["message"] or c.get("machine_filter") == "Press-200" or ("E101" in c["message"] and "H20" not in c["message"])
        expected_svg = "press200_hydraulic_circuit.svg" if is_press200 else "hydraulic_press_manifold.svg"
        assert diags[0]["filename"] == expected_svg, f"Wrong diagram: {diags[0]['filename']} (expected {expected_svg})"
        assert all(s.get("diagram_url") is not None for s in sources), f"Sources missing diagram_url in: {c['message']}"
        print(f"  [OK] '{c['message']}' (filter: {c.get('machine_filter')}) -> {diags[0]['title']} ({diags[0]['filename']})")

    print("\n--- 3. Testing Random Text Refusal ---")
    random_cases = [
        {"message": "asdkjasdkjqwpe", "session_id": "rand_1"},
        {"message": "what is the capital of France?", "session_id": "rand_2"},
        {"message": "recipe for chocolate cake", "session_id": "rand_3"},
    ]
    for rc in random_cases:
        r = requests.post("http://127.0.0.1:8000/query", json=rc)
        data = r.json()
        assert "don't cover this" in data.get("answer", "").lower(), f"Failed to refuse random text: {rc['message']}"
        assert len(data.get("sources", [])) == 0, "Refusal should have 0 sources"
        assert len(data.get("diagrams", [])) == 0, "Refusal should have 0 diagrams"
        print(f"  [OK] Correctly refused: '{rc['message']}'")

    print("\n==================================================")
    print("ALL END-TO-END VERIFICATIONS PASSED 100%!")
    print("==================================================")

if __name__ == "__main__":
    test_endpoints()
