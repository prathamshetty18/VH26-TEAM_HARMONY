from src.embed_store import search

def retrieve(parsed_query, k=5):
    """
    Retrieves top-k relevant chunks based on parsed query parameters.
    If machine is known, filters vector search to that specific machine.
    """
    machine = parsed_query.get("machine")
    raw_query = parsed_query.get("raw_query") or ""
    error_code = parsed_query.get("error_code")

    # Build search query string
    search_text = raw_query
    if error_code and error_code not in raw_query:
        search_text = f"{error_code} {raw_query}"

    retrieved_chunks = []
    
    if machine and error_code:
        # Fetch exact error code chunks for this machine first
        code_chunks = search(query=search_text, k=max(k, 10), filter_metadata={"machine": machine, "error_code": error_code})
        # Also fetch machine chunks to ensure broader context if needed
        general_chunks = search(query=search_text, k=max(k, 10), filter_metadata={"machine": machine})
        retrieved_chunks = code_chunks + general_chunks
    elif machine:
        retrieved_chunks = search(query=search_text, k=max(k, 15), filter_metadata={"machine": machine})
    elif error_code:
        # Fetch across all machines for ambiguity evaluation
        retrieved_chunks = search(query=search_text, k=25, filter_metadata={"error_code": error_code})
    else:
        retrieved_chunks = search(query=search_text, k=k)

    # Deduplicate by (manual, section) while preserving order
    seen = set()
    deduped = []
    for c in retrieved_chunks:
        key = (c.get("manual"), c.get("section"))
        if key not in seen:
            seen.add(key)
            deduped.append(c)

    # Re-rank: If error_code is known, bring chunks matching error_code to the front
    if error_code:
        matching_chunks = [c for c in deduped if c.get("error_code") == error_code]
        other_chunks = [c for c in deduped if c.get("error_code") != error_code]
        deduped = matching_chunks + other_chunks

    # For ambiguity detection, return all disambiguation candidates if machine is None
    if not machine and error_code:
        return deduped[:15]

    return deduped[:k]

if __name__ == "__main__":
    from src.query_understanding import parse_query
    
    pq1 = parse_query("What does E101 mean on CNC-100?")
    chunks1 = retrieve(pq1)
    print(f"Query 1 retrieved {len(chunks1)} chunks. Top machine: {chunks1[0]['machine'] if chunks1 else 'None'}")

    pq2 = parse_query("why is Machine A overheating?")
    chunks2 = retrieve(pq2)
    print(f"Query 2 retrieved {len(chunks2)} chunks. Top machine: {chunks2[0]['machine'] if chunks2 else 'None'}")
