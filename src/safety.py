# Phase 6 — Hallucination / Safety Control

import re

REFUSAL_MESSAGE = "The manuals don't cover this. I won't guess at a fix."

STOPWORDS = {
    "what", "does", "mean", "on", "why", "is", "stopping", "due", "to", "how", "do", "i", 
    "can", "you", "tell", "me", "about", "for", "the", "a", "an", "in", "of", "and", "or", 
    "with", "this", "that", "it", "from", "are", "was", "were", "be", "been", "being", 
    "have", "has", "had", "should", "would", "could", "machine", "manual", "section",
    "error", "code", "codes", "regarding", "fault", "troubleshoot", "fix", "fixes", "fixing",
    "corrective", "action", "actions", "resolution", "solution", "solutions", "remedy",
    "procedure", "procedures", "step", "steps", "cause", "causes", "meaning", "meanings",
    "work", "works", "working", "doesn't", "doesnt", "not", "no", "if", "else", "other", "next",
    "try", "tried", "trying", "still", "happening", "occurs", "occur", "say", "said", "saying",
    "diagram", "diagrams", "schematic", "schematics", "image", "images",
    "drawing", "drawings", "blueprint", "blueprints", "circuit", "circuits",
    "flowchart", "flowcharts", "layout", "illustration", "illustrations",
    "picture", "pictures", "photo", "photos", "show", "showing", "display", "displaying", "view", "viewing",
    "generate", "generating", "generateing", "genrate", "genrateing", "create", "creating",
    "render", "rendering", "produce", "producing", "draw", "fetch", "fetching", "load", "loading",
    "resolve", "resolving", "resolved", "explain", "explaining", "explanation",
    "first", "second", "third", "fourth", "fifth", "last", "then", "after", "before",
    "get", "see", "bring", "up", "give", "please", "help",
    "issue", "issues", "problem", "problems", "persist", "persists", "persisting",
    "continue", "continues", "continuing", "fail", "fails", "failed", "happen", "happens", "happened"
}

MACHINE_PATTERNS = {
    "cb-4400", "cb4400", "4400", "cb", "conveyor", "belt",
    "mx-7", "mx7", "mx", "milling", "precision", "cnc",
    "hp-2200", "hp2200", "2200", "hp", "hydraulic", "press",
    "cnc-100", "cnc100", "100", "x200", "x-200",
    "press-200", "press200", "200", "p400", "p-400",
    "robotarm-300", "robotarm300", "300", "robot", "arm", "r300", "r-300"
}

def _extract_content_tokens(text, machine=None):
    """Extract non-stopword, non-machine tokens from text."""
    import difflib
    raw_tokens = re.findall(r"\b[a-zA-Z0-9_-]+\b", text.lower())
    extra_patterns = set()
    if machine:
        m_lower = machine.lower()
        extra_patterns.add(m_lower)
        for part in re.findall(r"\b[a-zA-Z0-9]+\b", m_lower):
            if len(part) > 2:
                extra_patterns.add(part)

    all_machine_patterns = MACHINE_PATTERNS.union(extra_patterns)

    tokens = set()
    for t in raw_tokens:
        if t in STOPWORDS or t in all_machine_patterns:
            continue
        # Also check fuzzy match against known machine patterns (typos like presss, cnc100, etc.)
        is_fuzzy_machine = False
        for mp in all_machine_patterns:
            if len(t) >= 4 and len(mp) >= 4:
                if difflib.SequenceMatcher(None, t, mp).ratio() >= 0.80:
                    is_fuzzy_machine = True
                    break
        if is_fuzzy_machine:
            continue

        tokens.add(t)
        if "-" in t:
            tokens.add(t.replace("-", ""))
            sub_tokens = [s for s in t.split("-") if s and len(s) > 1 and not s.isdigit() and s not in STOPWORDS and s not in all_machine_patterns]
            tokens.update(sub_tokens)
    return tokens


def is_sufficient(retrieved_chunks, query="", threshold=0.35, machine=None):
    """
    Evaluates whether retrieved chunks provide sufficient information to answer the query.
    """
    if not retrieved_chunks:
        return False, REFUSAL_MESSAGE

    top_chunk = retrieved_chunks[0]
    score = top_chunk.get("score", 0.0)

    has_diagram_intent = bool(re.search(
        r"\b(diagram|diagrams|schematic|schematics|image|images|drawing|drawings|blueprint|blueprints|circuit|circuits|flowchart|flowcharts|layout|illustration|illustrations|picture|pictures|photo|photos|generate|generating|genrate|render|rendering)\b",
        query.lower()
    ))
    has_known_machine = bool(machine or any(mp in query.lower() for mp in MACHINE_PATTERNS))

    is_keyword_match = top_chunk.get("match_type") == "keyword"

    # For keyword matches, similarity threshold is satisfied automatically (certainty 1.0).
    # For diagram requests, allow a slightly lower baseline threshold (0.25).
    effective_threshold = 0.0 if is_keyword_match else (0.25 if has_diagram_intent else threshold)

    # Gate 1: Baseline similarity score threshold
    if score < effective_threshold:
        return False, REFUSAL_MESSAGE

    # If cross-encoder scored top chunk as strongly negative (< -6.0) on a non-keyword, non-diagram query, refuse
    rerank_score = top_chunk.get("rerank_score")
    if rerank_score is not None and not is_keyword_match and not has_diagram_intent and rerank_score < -6.0:
        return False, REFUSAL_MESSAGE

    if not query or not query.strip():
        return False, REFUSAL_MESSAGE

    query_tokens = _extract_content_tokens(query, machine=machine)
    if not query_tokens:
        has_general_troubleshoot_intent = bool(re.search(
            r"\b(fix|troubleshoot|maintenance|guide|repair|service|manual|overview|spec|specs|info|resolve|problem|issue|persist|happen|cause|action|step|procedure)\b",
            query.lower()
        ))
        if has_known_machine and (has_general_troubleshoot_intent or has_diagram_intent or len(query.strip().split()) <= 8):
            return True, retrieved_chunks
        return False, REFUSAL_MESSAGE

    # Extract all tokens from retrieved chunks
    combined_chunk_text = " ".join([c.get("text", "").lower() for c in retrieved_chunks])
    chunk_tokens = set(re.findall(r"\b[a-zA-Z0-9_-]+\b", combined_chunk_text))
    all_chunk_tokens = set()
    for ct in chunk_tokens:
        all_chunk_tokens.add(ct)
        for st in ct.split("-"):
            if st:
                all_chunk_tokens.add(st)

    # Gate 2: Explicit error code verification (All alphanumeric series e.g. E101, H205, R101, SYM-series)
    error_codes_in_query = [
        t.replace("-", "") for t in query_tokens 
        if re.match(r"^[a-z]-?\d{3,4}$", t) or t.startswith("sym")
    ]
    for ec in error_codes_in_query:
        if ec not in all_chunk_tokens and ec.lower() not in combined_chunk_text:
            return False, REFUSAL_MESSAGE

    # Critical Action Gate: Queries requesting safety bypasses or unauthorized modifications
    # (e.g. bypass, override, rewire, rebuild, firmware) MUST be documented in the manuals.
    critical_actions = {
        "bypass", "override", "rewire", "hack", "firmware", 
        "disable", "bridge", "jumper", "defeat", "tamper"
    }
    for ca in critical_actions:
        if ca in query_tokens and ca not in all_chunk_tokens:
            return False, REFUSAL_MESSAGE

    # Gate 3: Keyword overlap check
    # - If non-error query tokens exist and NONE appear anywhere in the manual chunks (0% overlap), reject.
    # - For similarity (< 0.55), require at least 40% token match to prevent keyword drift.
    non_ec_query_tokens = [
        t for t in query_tokens 
        if not (re.match(r"^[a-z]-?\d{3,4}$", t) or t.startswith("sym"))
        and not (t.isdigit() and len(t) <= 4)
        and len(t) > 1
    ]
    if non_ec_query_tokens:
        matching = [t for t in non_ec_query_tokens if t in all_chunk_tokens]
        if len(matching) == 0:
            return False, REFUSAL_MESSAGE
        if score < 0.55:
            match_ratio = len(matching) / len(non_ec_query_tokens)
            if match_ratio < 0.40:
                return False, REFUSAL_MESSAGE

    return True, retrieved_chunks
