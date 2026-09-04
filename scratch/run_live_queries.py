import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)

QUERIES = [
    {"id": 1, "query": "How do I fix error E101 on the CB-4400 conveyor belt?", "category": "1. Exact Code"},
    {"id": 2, "query": "What does error E101 mean on the CNC Milling Machine MX-7 Precision?", "category": "1. Exact Code"},
    {"id": 3, "query": "What is the corrective action for fault H205 on the HP-2200 hydraulic press?", "category": "1. Exact Code"},
    {"id": 4, "query": "Why is the conveyor overheating?", "category": "2. Symptom"},
    {"id": 5, "query": "The conveyor belt is squealing and chirping during morning startup.", "category": "2. Symptom"},
    {"id": 6, "query": "Our CNC milled parts show high-pitched chatter marks along the finished vertical surfaces.", "category": "2. Symptom"},
    {"id": 7, "query": "The hydraulic press main pump is making a loud cavitation whining sound.", "category": "2. Symptom"},
    {"id": 8, "query": "E101", "category": "3. Ambiguous"},
    {"id": 9, "query": "What does error E101 mean?", "category": "3. Ambiguous"},
    {"id": 10, "query": "How do I fix error E101?", "category": "3. Ambiguous"},
    {"id": 11, "query": "The status LED is flashing 3 short blinks followed by a long pause, what does this pattern mean?", "category": "4. Undocumented"},
    {"id": 12, "query": "What causes the intermittent flickering pattern on the CNC MX-7 status LED?", "category": "4. Undocumented"},
    {"id": 13, "query": "The hydraulic press HP-2200 status LED is blinking 3 times in a row. How do I clear it?", "category": "4. Undocumented"},
]

def main():
    results = []
    print("Executing 13 live benchmark queries against /query endpoint...\n")
    for q in QUERIES:
        resp = client.post("/query", json={"message": q["query"], "session_id": f"bench_{q['id']}"})
        status = resp.status_code
        data = resp.json() if status == 200 else {"error": resp.text}
        
        result_entry = {
            "id": q["id"],
            "query": q["query"],
            "category": q["category"],
            "status_code": status,
            "ambiguous": data.get("ambiguous"),
            "options": data.get("options"),
            "sources": data.get("sources"),
            "answer": data.get("answer"),
        }
        results.append(result_entry)
        print(f"[{q['id']}/13] Query: '{q['query']}'")
        print(f"      Status: {status} | Ambiguous: {data.get('ambiguous')}")
        print(f"      Sources: {len(data.get('sources', []))} sources")
        print(f"      Answer: {str(data.get('answer'))[:120]}...\n")

    with open("tests/live_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("Completed. Results written to tests/live_test_results.json")

if __name__ == "__main__":
    main()
