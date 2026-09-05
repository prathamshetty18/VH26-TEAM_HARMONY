"""
Cross-Encoder Reranking Module for MachineAssist.

Scores retrieved chunks against the raw user query using a cross-encoder model
('cross-encoder/ms-marco-MiniLM-L-6-v2'). Exact keyword matches (match_type="keyword")
are preserved at the front and exempted from re-scoring to guarantee deterministic
precision for exact error codes.
"""

import os
import sys
import time
import logging
from typing import List, Dict, Any, Optional

# Suppress HuggingFace Windows symlink warnings if not already set
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

logger = logging.getLogger("machineassist.rerank")

_CROSS_ENCODER = None
CROSS_ENCODER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

def get_cross_encoder():
    """
    Lazy singleton loader for the cross-encoder model.
    Loads once at module level and caches the instance.
    """
    global _CROSS_ENCODER
    if _CROSS_ENCODER is None:
        try:
            from sentence_transformers import CrossEncoder
            t0 = time.perf_counter()
            _CROSS_ENCODER = CrossEncoder(CROSS_ENCODER_MODEL_NAME)
            load_time = (time.perf_counter() - t0) * 1000
            logger.info(f"Loaded CrossEncoder '{CROSS_ENCODER_MODEL_NAME}' in {load_time:.1f}ms")
        except Exception as e:
            logger.error(f"Failed to load CrossEncoder '{CROSS_ENCODER_MODEL_NAME}': {e}")
            _CROSS_ENCODER = False
    return _CROSS_ENCODER if _CROSS_ENCODER is not False else None


def rerank(
    query: str,
    chunks: List[Dict[str, Any]],
    top_n: int = 5
) -> List[Dict[str, Any]]:
    """
    Re-scores and sorts candidate chunks using the cross-encoder:
    1. Splits chunks into keyword hits (match_type == "keyword") and rerank candidates.
    2. Exact keyword hits bypass reranking and are preserved in original order at the top.
    3. Batched cross-encoder inference is performed on (query, chunk_text) for all candidates.
    4. Attaches 'rerank_score' to each candidate while preserving original 'score'.
    5. Re-sorts candidates descending by 'rerank_score'.
    6. Returns keyword hits + top reranked candidates, capped at top_n.
    """
    if not chunks or top_n <= 0:
        return []

    # If query is empty or only whitespace, return original top_n without re-scoring
    if not query or not query.strip():
        return chunks[:top_n]

    # Partition into keyword hits and rerank candidates
    keyword_hits = []
    rerank_candidates = []

    for c in chunks:
        if c.get("match_type") == "keyword":
            # Keyword hits preserve top priority by definition
            if "rerank_score" not in c:
                c["rerank_score"] = 999.0
            keyword_hits.append(c)
        else:
            rerank_candidates.append(c)

    # If keyword hits alone satisfy or exceed top_n, return them immediately
    if len(keyword_hits) >= top_n:
        return keyword_hits[:top_n]

    # If no candidates need reranking, return keyword hits
    if not rerank_candidates:
        return keyword_hits[:top_n]

    model = get_cross_encoder()
    if model is None:
        # Fallback if cross-encoder cannot be loaded
        logger.warning("CrossEncoder unavailable; falling back to original retrieval order.")
        return (keyword_hits + rerank_candidates)[:top_n]

    # Prepare batched pairs for cross-encoder
    pairs = []
    for c in rerank_candidates:
        chunk_text = c.get("text") or f"{c.get('section', '')} {c.get('manual', '')}"
        pairs.append((query, chunk_text))

    try:
        t_start = time.perf_counter()
        scores = model.predict(pairs)
        duration_ms = (time.perf_counter() - t_start) * 1000

        # Attach rerank_score to each candidate (float conversion ensures JSON serializability)
        for c, score in zip(rerank_candidates, scores):
            c["rerank_score"] = float(score)

        # Sort candidates descending by cross-encoder score
        rerank_candidates.sort(key=lambda x: x.get("rerank_score", -999.0), reverse=True)

        logger.debug(f"Reranked {len(pairs)} candidate pairs in {duration_ms:.1f}ms")
    except Exception as e:
        logger.error(f"Error during CrossEncoder predict: {e}; keeping original order.")

    slots_needed = top_n - len(keyword_hits)
    selected_candidates = rerank_candidates[:slots_needed]

    return keyword_hits + selected_candidates


if __name__ == "__main__":
    print("--- Testing src/rerank.py standalone ---")
    mock_chunks = [
        {"manual": "cnc100.txt", "section": "E101 Overview", "text": "Excessive motor temperature", "score": 1.0, "match_type": "keyword"},
        {"manual": "cnc100.txt", "section": "General Overview", "text": "CNC milling center general maintenance", "score": 0.58, "match_type": "vector"},
        {"manual": "cnc100.txt", "section": "Spindle Thermal Expansion", "text": "High temperature causes spindle thermal growth and motor heat", "score": 0.42, "match_type": "vector"},
    ]
    
    q = "spindle getting hot and thermal expansion"
    print(f"Query: {q}")
    print("\nBefore reranking:")
    for idx, c in enumerate(mock_chunks, 1):
        print(f"  {idx}. {c['section']} (score: {c['score']}, type: {c.get('match_type')})")

    results = rerank(q, mock_chunks, top_n=3)
    print("\nAfter reranking (top_n=3):")
    for idx, c in enumerate(results, 1):
        print(f"  {idx}. {c['section']} (orig score: {c['score']}, rerank_score: {c.get('rerank_score')}, type: {c.get('match_type')})")
