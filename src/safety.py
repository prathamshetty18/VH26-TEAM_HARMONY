# Phase 6 — Hallucination / Safety Control

import re

REFUSAL_MESSAGE = "The manuals don't cover this. I won't guess at a fix."

STOPWORDS = {
    "what", "does", "mean", "on", "why", "is", "stopping", "due", "to", "how", "do", "i", 
    "can", "you", "tell", "me", "about", "for", "the", "a", "an", "in", "of", "and", "or", 
    "with", "this", "that", "it", "from", "are", "was", "were", "be", "been", "being", 
    "have", "has", "had", "should", "would", "could", "machine", "manual", "section",
    "error", "code", "codes", "regarding", "fault", "troubleshoot", "fix"
}

MACHINE_PATTERNS = {
    "cb-4400", "cb4400", "4400", "cb", "conveyor",
    "mx-7", "mx7", "mx", "milling", "precision", "cnc",
    "hp-2200", "hp2200", "2200", "hp", "hydraulic", "press",
    "cnc-100", "cnc100", "100", "press-200", "press200", "200", "robotarm-300", "robotarm300", "300"
}

def _extract_content_tokens(text):
    """Extract non-stopword, non-machine tokens from text."""
    raw_tokens = re.findall(r"\b[a-zA-Z0-9_-]+\b", text.lower())
    tokens = []
    for t in raw_tokens:
        if t in STOPWORDS or t in MACHINE_PATTERNS:
            continue
        sub_tokens = [s for s in t.split("-") if s and s not in STOPWORDS and s not in MACHINE_PATTERNS]
        tokens.extend(sub_tokens)
    return set(tokens)


def is_sufficient(retrieved_chunks, query="", threshold=0.35):
    """
    Evaluates whether retrieved chunks provide sufficient information to answer the query.

    Three-Gate Architecture:
    1. Score Gate: top chunk similarity score must be >= threshold (0.35).
    2. Error Code Gate: if the query asks for an explicit error code (e.g. E101, H205), 
       that code MUST exist in the retrieved manual chunks.
    3. Hybrid Semantic / Borderline Overlap Gate:
       - High similarity (>= 0.50): trusted as a valid semantic match/paraphrase even without literal word overlap.
       - Borderline similarity (0.35 <= score < 0.50): requires at least 40% query content token overlap 
         in retrieved chunks to filter out incidental single-keyword matches (e.g. spindle bearing).

    Returns (is_sufficient_bool, result_or_refusal_message).
    """
    if not retrieved_chunks:
        return False, REFUSAL_MESSAGE

    top_chunk = retrieved_chunks[0]
    score = top_chunk.get("score", 0.0)

    # Gate 1: Baseline similarity score threshold
    if score < threshold:
        return False, REFUSAL_MESSAGE

    if not query:
        return True, retrieved_chunks

    query_tokens = _extract_content_tokens(query)
    if not query_tokens:
        return True, retrieved_chunks

    # Extract all tokens from top 3 retrieved chunks
    combined_chunk_text = " ".join([c.get("text", "").lower() for c in retrieved_chunks[:3]])
    chunk_tokens = set(re.findall(r"\b[a-zA-Z0-9_-]+\b", combined_chunk_text))
    all_chunk_tokens = set()
    for ct in chunk_tokens:
        all_chunk_tokens.add(ct)
        for st in ct.split("-"):
            if st:
                all_chunk_tokens.add(st)

    # Gate 2: Explicit error code verification (E-series, H-series, SYM-series)
    error_codes_in_query = [t for t in query_tokens if re.match(r"^[eh]\d{3}$", t) or t.startswith("sym")]
    for ec in error_codes_in_query:
        if ec not in all_chunk_tokens:
            return False, REFUSAL_MESSAGE

    # Critical Action Gate: Queries requesting safety bypasses or unauthorized modifications
    # (e.g. bypass, override, rewire, rebuild, firmware) MUST be documented in the manuals.
    critical_actions = {"bypass", "override", "rewire", "hack", "firmware"}
    for ca in critical_actions:
        if ca in query_tokens and ca not in all_chunk_tokens:
            return False, REFUSAL_MESSAGE

    # Gate 3: Borderline score keyword overlap check
    # High semantic similarity (>= 0.50) passes automatically (supports semantic paraphrasing).
    # Borderline similarity (< 0.50) requires at least 40% query token match to prevent keyword drift.
    if score < 0.50:
        non_ec_query_tokens = [t for t in query_tokens if not (re.match(r"^[eh]\d{3}$", t) or t.startswith("sym"))]
        if non_ec_query_tokens:
            matching = [t for t in non_ec_query_tokens if t in all_chunk_tokens]
            match_ratio = len(matching) / len(non_ec_query_tokens)
            if match_ratio < 0.40:
                return False, REFUSAL_MESSAGE

    return True, retrieved_chunks
