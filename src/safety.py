# Phase 6 — Hallucination / Safety Control

import re

REFUSAL_MESSAGE = "The available manuals do not provide sufficient information to answer this. I won't provide an unsupported answer."

STOPWORDS = {
    "what", "does", "mean", "on", "why", "is", "stopping", "due", "to", "how", "do", "i", 
    "can", "you", "tell", "me", "about", "for", "the", "a", "an", "in", "of", "and", "or", 
    "with", "this", "that", "it", "from", "are", "was", "were", "be", "been", "being", 
    "have", "has", "had", "should", "would", "could", "machine", "manual", "section"
}

MACHINE_PATTERNS = {
    "cnc-100", "press-200", "robotarm-300", 
    "cnc100", "press200", "robotarm300", 
    "cnc", "press", "robotarm", "100", "200", "300"
}

def _extract_content_tokens(text):
    """Extract meaningful non-stopwords and non-machine tokens from query."""
    raw_tokens = re.findall(r"\b[a-zA-Z0-9_-]+\b", text.lower())
    tokens = []
    for t in raw_tokens:
        if t in STOPWORDS or t in MACHINE_PATTERNS:
            continue
        sub_tokens = [s for s in t.split("-") if s and s not in STOPWORDS and s not in MACHINE_PATTERNS]
        tokens.extend(sub_tokens)
    return set(tokens)


def is_sufficient(retrieved_chunks, query="", threshold=0.40):
    """
    Evaluates whether the retrieved chunks provide sufficient information to answer the query.

    Checks:
    1. Score threshold: top chunk similarity score must be >= threshold.
    2. Error code presence: if query mentions an error code (e.g. E101), that code MUST exist in chunks.
    3. Content overlap: at least 50% of the query's non-machine content keywords must appear in retrieved chunks.

    Returns (is_sufficient_bool, result_or_refusal_message).
    """
    if not retrieved_chunks:
        return False, REFUSAL_MESSAGE

    top_chunk = retrieved_chunks[0]
    score = top_chunk.get("score", 0.0)

    # Gate 1: Similarity score check
    if score < threshold:
        return False, REFUSAL_MESSAGE

    if not query:
        return True, retrieved_chunks

    query_tokens = _extract_content_tokens(query)
    if not query_tokens:
        return True, retrieved_chunks

    # Combine text of top retrieved chunks
    combined_chunk_text = " ".join([c.get("text", "").lower() for c in retrieved_chunks[:3]])
    chunk_tokens = set(re.findall(r"\b[a-zA-Z0-9_-]+\b", combined_chunk_text))
    all_chunk_tokens = set()
    for ct in chunk_tokens:
        all_chunk_tokens.add(ct)
        for st in ct.split("-"):
            if st:
                all_chunk_tokens.add(st)

    # Gate 2: Error code verification
    error_codes_in_query = [t for t in query_tokens if re.match(r"^e\d{3}$", t)]
    for ec in error_codes_in_query:
        if ec not in all_chunk_tokens:
            return False, REFUSAL_MESSAGE

    # Gate 3: Content token overlap requirement (>= 50%)
    non_ec_query_tokens = [t for t in query_tokens if not re.match(r"^e\d{3}$", t)]
    if non_ec_query_tokens:
        matching = [t for t in non_ec_query_tokens if t in all_chunk_tokens]
        match_ratio = len(matching) / len(non_ec_query_tokens)
        if match_ratio < 0.5:
            return False, REFUSAL_MESSAGE

    return True, retrieved_chunks
