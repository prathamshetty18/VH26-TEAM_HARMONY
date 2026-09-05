import re
from typing import List, Dict, Any, Optional
from src.embed_store import search, get_distinct_machines

LEGACY_MACHINE_MAP = {
    "CNC-100": "CNC Milling Machine",
    "Press-200": "Hydraulic Press",
    "RobotArm-300": "RobotArm-300"
}

def retrieve(parsed_query: Dict[str, Any], k: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieves top-k relevant chunks based on parsed query parameters.
    If machine is known, filters vector search to that specific machine.
    Automatically maps legacy aliases (CNC-100 -> CNC Milling Machine) only if
    the collection contains solely production manuals and not dedicated models.
    """
    machine = parsed_query.get("machine")
    raw_query = parsed_query.get("raw_query") or ""
    error_code = parsed_query.get("error_code")

    is_diagram_query = bool(re.search(
        r"\b(diagram|diagrams|schematic|schematics|image|images|drawing|drawings|blueprint|blueprints|circuit|circuits|flowchart|layout|generate|genrate|render)\b", 
        raw_query.lower()
    ))

    # Map legacy names if collection uses production manuals and lacks specific machine
    target_machine = machine
    if machine in LEGACY_MACHINE_MAP:
        try:
            distinct = get_distinct_machines()
            if machine not in distinct and LEGACY_MACHINE_MAP[machine] in distinct:
                target_machine = LEGACY_MACHINE_MAP[machine]
        except Exception:
            pass

    # Cross-Model Hydraulic Press routing:
    # Both "Hydraulic Press" (Model HP-2200) and "Press-200" (Model P400) are hydraulic presses.
    filter_machine = target_machine
    if target_machine == "Hydraulic Press":
        if error_code in ("E101", "E202", "E203"):
            filter_machine = "Press-200"
        else:
            filter_machine = "Hydraulic Press"
    elif target_machine == "Press-200":
        if error_code in ("H201", "H205", "H312", "H420", "H515", "H622"):
            filter_machine = "Hydraulic Press"
        else:
            filter_machine = "Press-200"

    # Build search query string
    search_text = raw_query
    if error_code and error_code not in raw_query:
        search_text = f"{error_code} {raw_query}"
    elif is_diagram_query and filter_machine:
        m_label = filter_machine if isinstance(filter_machine, str) else "hydraulic press"
        search_text = f"{raw_query} {m_label} technical overview schematic manifold circuit"

    retrieved_chunks = []
    if filter_machine and error_code:
        # Fetch exact error code chunks for this machine first
        code_chunks = search(query=search_text, k=max(k, 10), filter_metadata={"machine": filter_machine, "error_code": error_code})
        # Also fetch machine chunks to ensure broader context if needed
        general_chunks = search(query=search_text, k=max(k, 10), filter_metadata={"machine": filter_machine})
        retrieved_chunks = code_chunks + general_chunks
    elif filter_machine:
        retrieved_chunks = search(query=search_text, k=max(k, 15), filter_metadata={"machine": filter_machine})
    elif error_code:
        # Fetch across all machines for ambiguity evaluation
        retrieved_chunks = search(query=search_text, k=25, filter_metadata={"error_code": error_code})
    else:
        retrieved_chunks = search(query=search_text, k=max(k, 10))

    # Deduplicate by (manual, section) while preserving order
    seen = set()
    deduped = []
    for c in retrieved_chunks:
        key = (c.get("manual"), c.get("section"))
        if key not in seen:
            seen.add(key)
            deduped.append(c)

    # Re-rank: If error_code is known, bring chunks matching error_code to the front and boost score
    if error_code:
        matching_chunks = []
        other_chunks = []
        for c in deduped:
            if c.get("error_code") == error_code or re.search(rf"\b{re.escape(error_code)}\b", c.get("text", ""), re.IGNORECASE):
                c_copy = dict(c)
                # Boost confidence for verified exact ground-truth code matches
                c_copy["score"] = max(c_copy.get("score", 0.0), 0.90)
                matching_chunks.append(c_copy)
            else:
                other_chunks.append(c)
        deduped = matching_chunks + other_chunks
    elif is_diagram_query:
        diag_chunks = [c for c in deduped if c.get("diagram_url")]
        other_chunks = [c for c in deduped if not c.get("diagram_url")]
        deduped = diag_chunks + other_chunks
    else:
        # Re-rank symptom queries: prioritize chunks explicitly matching specific diagnostic terms
        content_words = set(re.findall(r"\b[a-zA-Z]{4,}\b", raw_query.lower())) - {
            "conveyor", "machine", "press", "milling", "robot", "system", "what", "does", "mean", "why", "stopping", "troubleshoot"
        }
        if content_words:
            def _symptom_priority(c):
                sec = c.get("section", "").lower()
                txt = c.get("text", "").lower()
                return sum(2 if w in sec else (1 if w in txt else 0) for w in content_words)
            deduped = sorted(deduped, key=lambda c: (_symptom_priority(c), c.get("score", 0.0)), reverse=True)

    # For ambiguity detection, return all disambiguation candidates if machine is None
    if not machine and error_code:
        return deduped[:15]

    return deduped[:k]

if __name__ == "__main__":
    from src.query_understanding import parse_query
    q = parse_query("What does E101 mean on CNC-100?")
    res = retrieve(q)
    print(f"Retrieved {len(res)} chunks:")
    for r in res:
        print(f"  Machine: {r.get('machine')} | Code: {r.get('error_code')} | Diag: {r.get('diagram_url')}")
