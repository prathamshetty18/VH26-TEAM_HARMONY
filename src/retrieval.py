import re
from src.embed_store import search, get_distinct_machines

LEGACY_MACHINE_MAP = {
    "CNC-100": "CNC Milling Machine",
    "Press-200": "Hydraulic Press",
    "RobotArm-300": "RobotArm-300"
}

def retrieve(parsed_query, k=5):
    """
    Retrieves top-k relevant chunks based on parsed query parameters.
    If machine is known, filters vector search to that specific machine.
    Automatically maps legacy aliases (CNC-100 -> CNC Milling Machine) if
    the collection contains the production manuals.
    """
    machine = parsed_query.get("machine")
    raw_query = parsed_query.get("raw_query") or ""
    error_code = parsed_query.get("error_code")

    # Map legacy names if collection uses production manuals
    target_machine = machine
    if machine in LEGACY_MACHINE_MAP:
        try:
            distinct = get_distinct_machines()
            if machine not in distinct and LEGACY_MACHINE_MAP[machine] in distinct:
                target_machine = LEGACY_MACHINE_MAP[machine]
        except Exception:
            pass

    # Build search query string
    search_text = raw_query
    if error_code and error_code not in raw_query:
        search_text = f"{error_code} {raw_query}"

    filter_metadata = None
    if target_machine:
        filter_metadata = {"machine": target_machine}
        fetch_k = max(k, 15) if error_code else k
    elif error_code:
        filter_metadata = {"error_code": error_code}
        fetch_k = max(k, 10)
    else:
        fetch_k = k

    retrieved_chunks = search(query=search_text, k=fetch_k, filter_metadata=filter_metadata)

    # Re-rank: If error_code is known, bring chunks matching error_code to the front and boost score
    if error_code:
        matching_chunks = []
        other_chunks = []
        for c in retrieved_chunks:
            if c.get("error_code") == error_code or re.search(rf"\b{re.escape(error_code)}\b", c.get("text", ""), re.IGNORECASE):
                c_copy = dict(c)
                # Boost confidence for verified exact ground-truth code matches
                c_copy["score"] = max(c_copy.get("score", 0.0), 0.90)
                matching_chunks.append(c_copy)
            else:
                other_chunks.append(c)
        retrieved_chunks = matching_chunks + other_chunks

    return retrieved_chunks[:k]

if __name__ == "__main__":
    from src.query_understanding import parse_query
    
    pq1 = parse_query("What does E101 mean on CNC-100?")
    chunks1 = retrieve(pq1)
    print(f"Query 1 retrieved {len(chunks1)} chunks. Top machine: {chunks1[0]['machine'] if chunks1 else 'None'}")

    pq2 = parse_query("why is Machine A overheating?")
    chunks2 = retrieve(pq2)
    print(f"Query 2 retrieved {len(chunks2)} chunks. Top machine: {chunks2[0]['machine'] if chunks2 else 'None'}")
