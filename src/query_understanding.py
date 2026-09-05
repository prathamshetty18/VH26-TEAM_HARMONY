import re
from typing import Optional, List, Dict, Any

DEFAULT_KNOWN_MACHINES = [
    "CNC-100",
    "Press-200",
    "RobotArm-300",
    "Conveyor Belt System",
    "CNC Milling Machine",
    "Hydraulic Press"
]

MACHINE_ALIASES = {
    # CNC-100
    "cnc-100": "CNC-100",
    "cnc 100": "CNC-100",
    "cnc100": "CNC-100",
    "machine a": "CNC-100",

    # Press-200
    "press-200": "Press-200",
    "press 200": "Press-200",
    "press200": "Press-200",
    "machine b": "Press-200",

    # RobotArm-300
    "robot-arm-300": "RobotArm-300",
    "robot arm 300": "RobotArm-300",
    "robotarm-300": "RobotArm-300",
    "robotarm 300": "RobotArm-300",
    "robotarm300": "RobotArm-300",
    "robotarm": "RobotArm-300",
    "machine c": "RobotArm-300",
    "r300": "RobotArm-300",
    "r-300": "RobotArm-300",
    "r 300": "RobotArm-300",

    # Conveyor Belt System (CB-4400)
    "cb-4400": "Conveyor Belt System",
    "cb 4400": "Conveyor Belt System",
    "cb4400": "Conveyor Belt System",
    "conveyor belt system": "Conveyor Belt System",
    "conveyor belt": "Conveyor Belt System",
    "conveyor": "Conveyor Belt System",

    # CNC Milling Machine (MX-7 Precision)
    "mx-7 precision": "CNC Milling Machine",
    "mx-7": "CNC Milling Machine",
    "mx 7": "CNC Milling Machine",
    "mx7": "CNC Milling Machine",
    "cnc milling machine": "CNC Milling Machine",
    "cnc milling": "CNC Milling Machine",
    "cnc milled": "CNC Milling Machine",
    "milling machine": "CNC Milling Machine",
    "cnc mill": "CNC Milling Machine",

    # Hydraulic Press (HP-2200)
    "hp-2200": "Hydraulic Press",
    "hp 2200": "Hydraulic Press",
    "hp2200": "Hydraulic Press",
    "hydraulic press 2200": "Hydraulic Press",
    "hydraulic press": "Hydraulic Press",

    # Legacy Test Machines (for test suite backwards compatibility)
    "cnc-100": "CNC-100",
    "cnc 100": "CNC-100",
    "cnc100": "CNC-100",
    "machine a": "CNC-100",
    "press-200": "Press-200",
    "press 200": "Press-200",
    "press200": "Press-200",
    "machine b": "Press-200",
    "robotarm-300": "RobotArm-300",
    "robot arm 300": "RobotArm-300",
    "robotarm300": "RobotArm-300",
    "machine c": "RobotArm-300",
}

LEGACY_MAP = {
    "CNC-100": "CNC Milling Machine",
    "Press-200": "Hydraulic Press",
    "RobotArm-300": "RobotArm-300"
}

def parse_query(query: str, known_machines=None, known_error_codes=None) -> Dict[str, Any]:
    """
    Extracts machine name (or unrecognized machine) and error code from a query string.
    Returns:
    {
        "machine": str or None,
        "unrecognized_machine": str or None,
        "error_code": str or None,
        "raw_query": str
    }
    """
    if known_machines is None:
        known_machines = DEFAULT_KNOWN_MACHINES

    query_lower = query.lower()

    # 1. Detect Machine Name with strict whole-entity / exact boundary matching
    detected_machine = None
    
    valid_targets = set(known_machines)
    for k, v in LEGACY_MAP.items():
        if v in valid_targets or v == k:
            valid_targets.add(k)

    sorted_aliases = sorted(MACHINE_ALIASES.keys(), key=len, reverse=True)
    for alias in sorted_aliases:
        target = MACHINE_ALIASES[alias]
        if target in valid_targets or target in known_machines:
            pattern = rf"(?:^|[^a-zA-Z0-9_-]){re.escape(alias)}(?:$|[^a-zA-Z0-9_-])"
            if re.search(pattern, query_lower):
                detected_machine = target
                break

    # If no alias hit, check known machines directly
    if not detected_machine:
        sorted_known = sorted(known_machines, key=len, reverse=True)
        for m in sorted_known:
            pattern = rf"(?:^|[^a-zA-Z0-9_-]){re.escape(m.lower())}(?:$|[^a-zA-Z0-9_-])"
            if re.search(pattern, query_lower):
                detected_machine = m
                break

    unrecognized_machine = None
    if not detected_machine:
        # Check if a machine was mentioned in the query
        prep_match = re.search(
            r"\b(?:on|for|in|at|machine|model|unit)\s+([A-Za-z0-9_.\-]+(?:\s+[A-Za-z0-9_.\-]+)*)",
            query,
            re.IGNORECASE
        )
        candidate = None
        if prep_match:
            raw_cand = prep_match.group(1).strip()
            raw_cand = re.sub(r"[?,.!;:\"']+$", "", raw_cand).strip()
            raw_cand = re.sub(r"^(?:the|my|a|an)\s+", "", raw_cand, flags=re.IGNORECASE).strip()
            if raw_cand:
                candidate = raw_cand
        else:
            token_match = re.search(r"\b([A-Za-z0-9]+-[A-Za-z0-9-]+)\b", query)
            if token_match:
                candidate = token_match.group(1).strip()
            else:
                mach_match = re.search(r"\b(Machine\s+[A-Za-z0-9]+)\b", query, re.IGNORECASE)
                if mach_match:
                    candidate = mach_match.group(1).strip()

        if candidate:
            cand_lower = candidate.lower()
            is_known = False
            for m in known_machines:
                if cand_lower == m.lower():
                    is_known = True
                    detected_machine = m
                    break
            if not is_known:
                for alias, target in MACHINE_ALIASES.items():
                    if cand_lower == alias.lower() and (target in valid_targets or target in known_machines):
                        is_known = True
                        detected_machine = target
                        break

            if not is_known:
                unrecognized_machine = candidate

    # 2. Detect Error Code (Supports alphanumeric error codes like E101, E-101, H205, A032, and SYM- series)
    # Exclude machine model numbers (e.g. X200, P400, R300, HP2200, CB4400) from being treated as error codes.
    detected_error_code = None
    for match in re.finditer(r"\b([A-Z]-?\d{3,4}|SYM-[A-Z0-9-]+)\b", query, re.IGNORECASE):
        raw_code = match.group(1).upper()
        norm_code = raw_code if raw_code.startswith("SYM-") else raw_code.replace("-", "")
        if raw_code.lower() in MACHINE_ALIASES or norm_code.lower() in MACHINE_ALIASES:
            continue
        detected_error_code = norm_code
        break

    return {
        "machine": detected_machine,
        "unrecognized_machine": unrecognized_machine,
        "error_code": detected_error_code,
        "raw_query": query
    }

# ==============================================================================
# AUTOMATIC MACHINE DETECTION LAYERS: FUZZY, SEMANTIC, AND SESSION CONTEXT
# ==============================================================================

import difflib
import math
from typing import Optional, Dict, Any, List

MACHINE_DESCRIPTIONS: Dict[str, str] = {
    "CNC-100": "CNC-100 computer numerical control milling machine, cutting tool, spindle motor, and workpiece machining center",
    "Press-200": "Press-200 industrial hydraulic stamping press, hydraulic fluid pump, and ram cylinder",
    "RobotArm-300": "RobotArm-300 articulated multi-axis robotic arm, joint servo drive, wrist manipulator, and motion controller",
    "Conveyor Belt System": "CB-4400 industrial conveyor belt material handling transport line with variable frequency drive roller",
    "CNC Milling Machine": "MX-7 precision CNC milling center with high-speed spindle cartridge, cutting tool, and coolant flow circuit",
    "Hydraulic Press": "HP-2200 heavy-duty hydraulic press with proportional manifold valve and ram cylinder"
}

_CACHED_DESCRIPTION_EMBEDDINGS: Optional[Dict[str, List[float]]] = None

def fuzzy_match_machine(query: str, known_machines=None, cutoff: float = 0.82) -> Optional[str]:
    """
    Fuzzy matching layer using difflib.SequenceMatcher.
    Builds 1-3 word sliding-window candidates from lowercased query and compares against aliases.
    """
    if not query:
        return None

    # Clean query into tokens while preserving hyphens
    cleaned = re.sub(r"[^\w\s-]", " ", query.lower())
    tokens = [t for t in re.split(r"\s+", cleaned) if t]
    if not tokens:
        return None

    target_aliases = dict(MACHINE_ALIASES)
    target_aliases.update({
        "robotic-arm": "RobotArm-300",
        "robotic arm": "RobotArm-300",
        "robot-arm": "RobotArm-300",
        "robot arm": "RobotArm-300",
    })
    if known_machines:
        for m in known_machines:
            target_aliases[m.lower()] = m
    else:
        for m in DEFAULT_KNOWN_MACHINES:
            target_aliases[m.lower()] = m

    best_ratio = 0.0
    best_machine = None

    # Check normalized full string
    normalized_full = " ".join(tokens)
    for alias, machine in target_aliases.items():
        ratio = difflib.SequenceMatcher(None, normalized_full, alias).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_machine = machine

    # Build 1 to 3 word sliding windows
    candidates = set()
    num_tokens = len(tokens)
    for n in (1, 2, 3):
        for i in range(num_tokens - n + 1):
            window = tokens[i:i+n]
            candidates.add(" ".join(window))
            candidates.add("-".join(window))

    for cand in candidates:
        if len(cand) < 3:
            continue
        for alias, machine in target_aliases.items():
            # Skip if length discrepancy is large
            if abs(len(cand) - len(alias)) > max(3, int(len(alias) * 0.4)):
                continue
            ratio = difflib.SequenceMatcher(None, cand, alias).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_machine = machine

    if best_ratio >= cutoff:
        return best_machine
    return None

def _get_description_embeddings(descriptions: Dict[str, str]) -> Dict[str, List[float]]:
    global _CACHED_DESCRIPTION_EMBEDDINGS
    if _CACHED_DESCRIPTION_EMBEDDINGS is None:
        try:
            from src.embed_store import get_embedding_function
        except ImportError:
            from embed_store import get_embedding_function
        fn = get_embedding_function()
        names = list(descriptions.keys())
        texts = [descriptions[k] for k in names]
        embs = fn(texts)
        _CACHED_DESCRIPTION_EMBEDDINGS = {name: emb for name, emb in zip(names, embs)}
    return _CACHED_DESCRIPTION_EMBEDDINGS

def _cosine_sim(vec1: List[float], vec2: List[float]) -> float:
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

def semantic_match_machine(query: str, descriptions: Optional[Dict[str, str]] = None, threshold: float = 0.45) -> Optional[str]:
    """
    Semantic matching layer using SentenceTransformer embeddings.
    Embeds query and compares cosine similarity against cached machine descriptions.
    """
    if not query or not query.strip():
        return None

    descs = descriptions or MACHINE_DESCRIPTIONS
    try:
        try:
            from src.embed_store import get_embedding_function
        except ImportError:
            from embed_store import get_embedding_function
        fn = get_embedding_function()
        query_emb = fn([query.strip()])[0]
        desc_embeddings = _get_description_embeddings(descs)

        best_sim = -1.0
        best_machine = None
        for machine, d_emb in desc_embeddings.items():
            sim = _cosine_sim(query_emb, d_emb)
            if sim > best_sim:
                best_sim = sim
                best_machine = machine

        if best_sim >= threshold:
            return best_machine
    except Exception:
        pass
    return None

def parse_query_with_context(
    query: str,
    session_memory: Optional[Any] = None,
    known_machines: Optional[List[str]] = None,
    machine_descriptions: Optional[Dict[str, str]] = None,
    require_vague_language: bool = False
) -> Dict[str, Any]:
    """
    Context-aware query understanding with 4 detection layers:
    1. Alias match (exact/substring) -> machine_source="alias"
    2. Fuzzy match (typos & near-misses) -> machine_source="fuzzy"
    3. Semantic match (descriptive phrases) -> machine_source="semantic"
    4. Session context fallback -> machine_source="session_context"
    """
    parsed = parse_query(query, known_machines=known_machines)

    # Layer 1: Alias Match
    if parsed.get("machine"):
        parsed["machine_source"] = "alias"
        return parsed

    # Layer 2: Fuzzy Match
    fuzzy_res = fuzzy_match_machine(query, known_machines=known_machines)
    if fuzzy_res:
        parsed["machine"] = fuzzy_res
        parsed["machine_source"] = "fuzzy"
        return parsed

    # Layer 3: Semantic Match
    semantic_res = semantic_match_machine(query, descriptions=machine_descriptions)
    if semantic_res:
        parsed["machine"] = semantic_res
        parsed["machine_source"] = "semantic"
        return parsed

    # Layer 4: Session Context Fallback
    if session_memory:
        last_m = None
        last_e = None
        if isinstance(session_memory, dict):
            last_m = session_memory.get("last_machine") or session_memory.get("machine")
            last_e = session_memory.get("last_error_code") or session_memory.get("error_code")
        else:
            last_m = getattr(session_memory, "last_machine", getattr(session_memory, "machine", None))
            last_e = getattr(session_memory, "last_error_code", getattr(session_memory, "error_code", None))

        if last_m:
            should_fallback = False
            if require_vague_language:
                if re.search(r"\b(that|it|this|again|the machine|same|there|above)\b", query.lower()):
                    should_fallback = True
            else:
                should_fallback = True

            if should_fallback:
                parsed["machine"] = last_m
                parsed["machine_source"] = "session_context"
                if not parsed.get("error_code") and last_e:
                    has_explicit_symptom = bool(re.search(
                        r"\b(led|blink|blinking|blinks|flash|flashing|flicker|flickering|pattern|smoke|leak|chatter|squeal|cavitation|whine|whining|vibrat|chirp)\w*",
                        query.lower()
                    ))
                    if not has_explicit_symptom:
                        if re.search(r"\b(it|that|again|fix|troubleshoot|step|steps|cause|causes|action|actions|procedure|how|why|diagram|diagrams|schematic|schematics|image|images|picture|pictures|drawing|drawings|blueprint|blueprints|photo|photos|generate|generating|genrate|genrateing|render|rendering|illustration|illustrations|view|display|show|explain|solve|resolve|clear|reset|do|should|first|second|third|next|check|now|mean)\b", query.lower()):
                            parsed["error_code"] = last_e
                return parsed

    parsed["machine_source"] = None
    return parsed

if __name__ == "__main__":
    test_queries = [
        "What does E101 mean on Machine A?",
        "What does E101 mean on CNC-100?",
        "What does E101 mean on CNC-999?",
        "What does E101 mean on CNC?",
        "the motor is making a weird noise",
        "E101 error on Press-200",
        "What does E101 mean?",
        "how to fix presss-200",
        "press  200 oil pressure",
        "the milling machine keeps stalling",
        "coffee"
    ]
    for q in test_queries:
        res = parse_query_with_context(q)
        print(f"Query: '{q}' -> Machine: {res['machine']} (Source: {res['machine_source']}) Code: {res['error_code']}")
