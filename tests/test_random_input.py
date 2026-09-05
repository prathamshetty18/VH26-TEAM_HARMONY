import requests
import uuid

base_url = "http://127.0.0.1:8000"

import time
for _ in range(30):
    try:
        res = requests.get(f"{base_url}/machines", timeout=2)
        if res.status_code == 200:
            break
    except Exception:
        time.sleep(1)

queries = [
    "test",
    "hello",
    "hi",
    "help",
    "random text",
    "xyz",
    "what is this",
    "can you help me",
    "tell me something",
    "fix problem",
    "motor",
    "leak",
    "oil",
    "bearing",
    "speed",
    "why is it not working",
    "broken",
    "machine is stopped",
    "asdfasdfasdf",
    "what is the weather today",
    "give me a recipe for pizza"
]

print("=== FRESH SESSION RANDOM QUERIES ===")
for q in queries:
    sid = f"fresh_{uuid.uuid4().hex[:8]}"
    r = requests.post(f"{base_url}/query", json={"message": q, "session_id": sid}).json()
    sc = len(r.get("sources", []))
    ms = r.get("machine_source")
    amb = r.get("ambiguous")
    ans = (r.get("answer") or "")[:60].replace("\n", " ")
    print(f"Q: {q!r:28} | src: {ms} | sources: {sc} | amb: {amb} | ans: {ans}")

print("\n=== CONTEXT SESSION (AFTER CNC-100) RANDOM QUERIES ===")
ctx_sid = f"ctx_{uuid.uuid4().hex[:8]}"
requests.post(f"{base_url}/query", json={"message": "What does E101 mean on CNC-100?", "session_id": ctx_sid})

for q in queries[:10]:
    r = requests.post(f"{base_url}/query", json={"message": q, "session_id": ctx_sid}).json()
    sc = len(r.get("sources", []))
    ms = r.get("machine_source")
    amb = r.get("ambiguous")
    ans = (r.get("answer") or "")[:60].replace("\n", " ")
    print(f"Q: {q!r:28} | src: {ms} | sources: {sc} | amb: {amb} | ans: {ans}")

print("\n=== SCOPED MACHINE RANDOM QUERIES ===")
for q in ["random text", "asdfghjk", "what is this", "tell me anything", "can you help", "xyz"]:
    r = requests.post(f"{base_url}/query", json={"message": q, "machine_filter": "CNC-100", "session_id": str(uuid.uuid4())}).json()
    sc = len(r.get("sources", []))
    ans = (r.get("answer") or "")[:60].replace("\n", " ")
    print(f"Q: {q!r:28} | sources: {sc} | ans: {ans}")

print("\n=== GENUINE VALID FOLLOW-UP INQUIRIES ===")
# Follow-up 1: "How do I fix it?" should return sources for CNC-100
r_fu1 = requests.post(f"{base_url}/query", json={"message": "How do I fix it?", "session_id": ctx_sid}).json()
print(f"Follow-up 'How do I fix it?': sources: {len(r_fu1.get('sources', []))} | ans: {(r_fu1.get('answer') or '')[:60].replace(chr(10), ' ')}")

# Follow-up 2: "What about that?"
r_fu2 = requests.post(f"{base_url}/query", json={"message": "What causes that?", "session_id": ctx_sid}).json()
print(f"Follow-up 'What causes that?': sources: {len(r_fu2.get('sources', []))} | ans: {(r_fu2.get('answer') or '')[:60].replace(chr(10), ' ')}")

