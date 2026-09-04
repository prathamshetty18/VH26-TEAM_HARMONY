import sys
import os

# Add root directory to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)

def run_demo_tests():
    print("==================================================")
    print("RUNNING 4 DEMO TEST CASES FOR MACHINEASSIST")
    print("==================================================")

    # Demo 1: Exact error code on specified machine
    print("\n--- DEMO 1: Exact Error Code (E101 on CNC-100) ---")
    resp1 = client.post("/query", json={"message": "What does E101 mean on CNC-100?", "session_id": "test_s1"})
    print("Status:", resp1.status_code)
    data1 = resp1.json()
    print("Ambiguous:", data1["ambiguous"])
    print("Sources:", [f"{s['manual']} ({s['section']})" for s in data1["sources"]])
    print("Answer Preview:\n", data1["answer"][:300], "...\n")

    # Demo 2: Natural language symptom query
    print("--- DEMO 2: Natural Language Symptom ('Why does Press-200 show hydraulic oil pressure low?') ---")
    resp2 = client.post("/query", json={"message": "Why does Press-200 show hydraulic oil pressure low?", "session_id": "test_s2"})
    print("Status:", resp2.status_code)
    data2 = resp2.json()
    print("Ambiguous:", data2["ambiguous"])
    print("Sources:", [f"{s['manual']} ({s['section']})" for s in data2["sources"]])
    print("Answer Preview:\n", data2["answer"][:300], "...\n")

    # Demo 3: Cross-manual ambiguity (E101 without machine)
    print("--- DEMO 3: Cross-Manual Ambiguity ('What does E101 mean?') ---")
    resp3 = client.post("/query", json={"message": "What does E101 mean?", "session_id": "test_s3"})
    print("Status:", resp3.status_code)
    data3 = resp3.json()
    print("Ambiguous:", data3["ambiguous"])
    print("Options:", data3["options"])
    print("Answer:", data3["answer"], "\n")

    # Demo 4: Insufficient Information / Refusal (Pre-filter Gate)
    print("--- DEMO 4: Insufficient Information ('How do I replace spindle bearing on CNC-100?') ---")
    resp4 = client.post("/query", json={"message": "How do I replace spindle bearing on CNC-100?", "session_id": "test_s4"})
    print("Status:", resp4.status_code)
    data4 = resp4.json()
    print("Ambiguous:", data4["ambiguous"])
    print("Answer:", data4["answer"], "\n")

    # Demo 5: Second-Line LLM Safety Net (Pre-Filter Bypass Case)
    print("--- DEMO 5: Second-Line LLM Self-Refusal ('electrical torque spec for E101') ---")
    resp5 = client.post("/query", json={"message": "What is the exact electrical torque specification for resetting E101 motor on CNC-100?", "session_id": "test_s5"})
    print("Status:", resp5.status_code)
    data5 = resp5.json()
    print("Ambiguous:", data5["ambiguous"])
    print("Answer:", data5["answer"])
    print("==================================================")

if __name__ == "__main__":
    run_demo_tests()
