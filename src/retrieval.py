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

    filter_metadata = None
    if machine:
        filter_metadata = {"machine": machine}

    retrieved_chunks = search(query=search_text, k=k, filter_metadata=filter_metadata)

    return retrieved_chunks

if __name__ == "__main__":
    from src.query_understanding import parse_query
    
    pq1 = parse_query("What does E101 mean on CNC-100?")
    chunks1 = retrieve(pq1)
    print(f"Query 1 retrieved {len(chunks1)} chunks. Top machine: {chunks1[0]['machine'] if chunks1 else 'None'}")

    pq2 = parse_query("why is Machine A overheating?")
    chunks2 = retrieve(pq2)
    print(f"Query 2 retrieved {len(chunks2)} chunks. Top machine: {chunks2[0]['machine'] if chunks2 else 'None'}")
