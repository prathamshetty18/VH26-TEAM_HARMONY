from src.embed_store import search

def retrieve(parsed_query, k=5):
    """
    Retrieves top-k relevant chunks based on parsed query parameters.
    If machine is known, filters vector search to that specific machine.
    """
    machine = parsed_query.get("machine")
    raw_query = parsed_query.get("raw_query") or ""
    error_code = parsed_query.get("error_code")

    import re
    is_diagram_query = bool(re.search(
        r"\b(diagram|diagrams|schematic|schematics|image|images|drawing|drawings|blueprint|blueprints|circuit|circuits|flowchart|layout|generate|genrate|render)\b", 
        raw_query.lower()
    ))

    # Build search query string
    search_text = raw_query
    if error_code and error_code not in raw_query:
        search_text = f"{error_code} {raw_query}"
    elif is_diagram_query and machine:
        m_label = machine if isinstance(machine, str) else "hydraulic press"
        search_text = f"{raw_query} {m_label} technical overview schematic manifold circuit"

    # Cross-Model Hydraulic Press routing:
    # Both "Hydraulic Press" (Model HP-2200) and "Press-200" (Model P400) are hydraulic presses.
    filter_machine = machine
    if machine == "Hydraulic Press":
        if error_code in ("E101", "E202", "E203"):
            filter_machine = "Press-200"
        else:
            filter_machine = "Hydraulic Press"
    elif machine == "Press-200":
        if error_code in ("H201", "H205", "H312", "H420", "H515", "H622"):
            filter_machine = "Hydraulic Press"
        else:
            filter_machine = "Press-200"

    filter_metadata = None
    if filter_machine:
        filter_metadata = {"machine": filter_machine}
        fetch_k = max(k, 15)
    elif error_code:
        filter_metadata = {"error_code": error_code}
        fetch_k = max(k, 10)
    else:
        fetch_k = max(k, 10)

    retrieved_chunks = search(query=search_text, k=fetch_k, filter_metadata=filter_metadata)

    # Re-rank: If error_code is known, bring chunks matching error_code to the front
    if error_code:
        matching_chunks = [c for c in retrieved_chunks if c.get("error_code") == error_code]
        other_chunks = [c for c in retrieved_chunks if c.get("error_code") != error_code]
        retrieved_chunks = matching_chunks + other_chunks
    elif is_diagram_query:
        diag_chunks = [c for c in retrieved_chunks if c.get("diagram_url")]
        other_chunks = [c for c in retrieved_chunks if not c.get("diagram_url")]
        retrieved_chunks = diag_chunks + other_chunks
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
            retrieved_chunks = sorted(retrieved_chunks, key=lambda c: (_symptom_priority(c), c.get("score", 0.0)), reverse=True)

    return retrieved_chunks[:k]

if __name__ == "__main__":
    from src.query_understanding import parse_query
    
    pq1 = parse_query("What does E101 mean on CNC-100?")
    chunks1 = retrieve(pq1)
    print(f"Query 1 retrieved {len(chunks1)} chunks. Top machine: {chunks1[0]['machine'] if chunks1 else 'None'}")

    pq2 = parse_query("why is Machine A overheating?")
    chunks2 = retrieve(pq2)
    print(f"Query 2 retrieved {len(chunks2)} chunks. Top machine: {chunks2[0]['machine'] if chunks2 else 'None'}")
