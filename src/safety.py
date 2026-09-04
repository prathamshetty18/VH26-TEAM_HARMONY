# Phase 6 — Hallucination / Safety Control

REFUSAL_MESSAGE = "The available manuals do not provide sufficient information to answer this. I won't provide an unsupported answer."

def is_sufficient(retrieved_chunks, threshold=0.48):
    """
    Checks if retrieved chunks contain sufficient information based on relevance scores.
    Returns (sufficient: bool, response_or_chunks)
    """
    if not retrieved_chunks:
        return False, REFUSAL_MESSAGE

    top_chunk = retrieved_chunks[0]
    score = top_chunk.get("score", 0.0)

    # If top similarity score is below the threshold, refuse to answer
    if score < threshold:
        return False, REFUSAL_MESSAGE

    return True, retrieved_chunks
