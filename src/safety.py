# Phase 6 — Hallucination / Safety Control

import re
import logging
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger("MachineAssist.Safety")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

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
    "continue", "continues", "continuing", "fail", "fails", "failed", "happen", "happens", "happened",
    "at", "by", "my", "our", "there", "their", "when", "where", "which"
}

# Whitelist of recognized plant equipment and known aliases
KNOWN_MACHINE_REGISTRY = {
    "Conveyor Belt System": {"conveyor", "belt", "cb-4400", "cb4400", "cb", "conveyorbelt"},
    "CNC Milling Machine": {"cnc", "milling", "mx-7", "mx7", "mx", "cnc-100", "cnc100", "x200", "x-200", "machining"},
    "Hydraulic Press": {"hydraulic", "press", "hp-2200", "hp2200", "hp", "press-200", "press200", "p400", "p-400"},
    "Articulated Robot": {"robot", "robotarm", "robotarm-300", "robotarm300", "r300", "r-300", "arm"}
}

ALL_KNOWN_MACHINE_ALIASES = set().union(*KNOWN_MACHINE_REGISTRY.values())

# Common industrial equipment nouns used to detect foreign / unindexed machines
EQUIPMENT_NOUN_INDICATORS = {
    "cutter", "forklift", "lathe", "printer", "welder", "welding", "drill",
    "packaging", "extruder", "molding", "injection", "boiler", "crane", "compressor",
    "chiller", "generator", "plasma", "furnace", "grinder", "conveyor", "press", "robot", "cnc"
}

# Technical vocabulary covering plant hardware, parts, telemetry, fault symptoms, and schematics
FACTORY_DOMAIN_VOCAB = {
    "motor", "bearing", "spindle", "vibration", "overheat", "temperature", "overcurrent",
    "current", "voltage", "fuse", "encoder", "joint", "pressure", "leak", "coolant",
    "flow", "filter", "lubrication", "oil", "jam", "slip", "tracking", "roller",
    "tension", "brake", "valve", "pump", "actuator", "cylinder", "sensor", "rpm",
    "speed", "axis", "gear", "clutch", "drive", "feed", "payload", "seal", "torque",
    "interlock", "e-stop", "emergency", "stop", "switch", "relay", "wire", "cable",
    "noise", "alarm", "fault", "error", "symptom", "overload", "thermal", "trip",
    "tripped", "reset", "calibrate", "calibration", "power", "pneumatic", "gripper",
    "tool", "wear", "worn", "clogged", "debris", "chatter", "cavitation", "whining",
    "squeal", "chirp", "lagging", "pulley", "platen", "ram", "strainer", "resonance",
    "stickout", "runout", "alignment", "misalignment", "deviation", "fan", "ventilation",
    "diagram", "schematic", "circuit", "manifold", "layout", "drawing", "schematics", "diagrams"
}

def normalize_code(code: str) -> str:
    """Symmetric normalization for error codes: uppercase alphanumeric, hyphens removed."""
    if not code:
        return ""
    return re.sub(r"[^A-Z0-9]", "", str(code).upper().strip())

def extract_candidate_error_codes(text: str) -> List[str]:
    """
    Extracts candidate error codes from query:
    1. Alphanumeric series: e.g. E101, H205, A032, A045, R101, A999, E999
    2. Numeric codes when prefixed by error/fault/alarm/code: e.g. 'error 999', 'code 101'
    3. Standard symptom IDs: e.g. SYM-CONV-SQUEAL
    """
    codes = []
    text_clean = text.strip()

    # 1. Alphanumeric series (letter + 2 to 4 digits, optional hyphen)
    alpha_matches = re.findall(r"\b([A-Za-z]-?\d{2,4})\b", text_clean)
    for m in alpha_matches:
        norm = normalize_code(m)
        if norm and norm not in {"MX7", "CB4400", "HP2200", "CNC100", "PRESS200", "ROBOTARM300"}:
            codes.append(norm)

    # 2. Numeric error codes e.g. 'error 999', 'code 999', 'fault #999', 'error: 999'
    num_matches = re.findall(r"\b(?:error|code|fault|alarm|err)\s*[:#]?\s*(\d{2,4})\b", text_clean, re.IGNORECASE)
    for m in num_matches:
        norm = normalize_code(m)
        if norm and norm not in codes:
            codes.append(norm)

    # 3. SYM-prefixed symptoms
    sym_matches = re.findall(r"\b(SYM-[A-Za-z0-9-]+)\b", text_clean, re.IGNORECASE)
    for m in sym_matches:
        norm = normalize_code(m)
        if norm and norm not in codes:
            codes.append(norm)

    return list(dict.fromkeys(codes))

def detect_foreign_machine(query: str, extra_known_machines: Optional[List[str]] = None) -> Tuple[bool, Optional[str]]:
    """
    Inverted Whitelist approach: Checks if the query specifies an equipment/machine
    that does NOT belong to the known machine registry or active dynamic manuals.
    """
    known_aliases = set(ALL_KNOWN_MACHINE_ALIASES)
    if extra_known_machines:
        for m in extra_known_machines:
            for token in re.findall(r"\b[a-zA-Z0-9_-]+\b", m.lower()):
                if len(token) > 1:
                    known_aliases.add(token)

    query_lower = query.lower()

    # Pattern A: Preposition + machine noun (e.g. "on the laser cutter", "for forklift", "in 3D printer")
    prep_matches = re.findall(r"\b(?:on|for|in|at)\s+(?:the\s+)?([a-z0-9_-]+(?:\s+[a-z0-9_-]+){0,2})", query_lower)
    for target in prep_matches:
        target_tokens = [t for t in re.findall(r"\b[a-z0-9_-]+\b", target) if t not in STOPWORDS]
        if not target_tokens:
            continue
        has_equip_noun = any(t in EQUIPMENT_NOUN_INDICATORS for t in target_tokens)
        matches_known = any(t in known_aliases for t in target_tokens)
        if has_equip_noun and not matches_known:
            return True, target.strip()

    # Pattern B: Direct equipment noun combos (e.g. "forklift hydraulic", "laser cutter nozzle")
    direct_foreign_terms = {
        "forklift", "laser cutter", "laser", "3d printer", "printer", "lathe",
        "injection molding", "welder", "welding machine", "boiler", "crane", "compressor"
    }
    for dft in direct_foreign_terms:
        if re.search(rf"\b{re.escape(dft)}\b", query_lower):
            if not any(t in known_aliases for t in dft.split()):
                return True, dft

    return False, None

def _extract_content_tokens(text: str, machine: Optional[str] = None) -> List[str]:
    """Extract non-stopword, non-machine tokens from text."""
    raw_tokens = re.findall(r"\b[a-zA-Z0-9_-]+\b", text.lower())
    extra_machine_tokens = set()
    if machine:
        for part in re.findall(r"\b[a-zA-Z0-9]+\b", machine.lower()):
            if len(part) > 2:
                extra_machine_tokens.add(part)

    tokens = []
    for t in raw_tokens:
        if t in STOPWORDS or t in ALL_KNOWN_MACHINE_ALIASES or t in extra_machine_tokens:
            continue
        tokens.append(t)
        if "-" in t:
            sub = [s for s in t.split("-") if s and len(s) > 1 and s not in STOPWORDS and s not in ALL_KNOWN_MACHINE_ALIASES and s not in extra_machine_tokens]
            tokens.extend(sub)
    return list(dict.fromkeys(tokens))

def is_sufficient(retrieved_chunks: List[Dict[str, Any]], query: str = "", threshold: float = 0.35, machine: Optional[str] = None) -> Tuple[bool, Any]:
    """
    Evaluates whether retrieved chunks provide sufficient, ground-truth information to answer.

    Strict Ordered Gate Architecture:
    Gate 0: Baseline similarity score threshold (bypassed for exact keyword matches, relaxed for diagrams).
    Gate 1: Error Code Verification (T2/T3 vs T4)
            - If keyword match confirmed -> ACCEPT (T4).
            - If query mentions error codes, at least ONE must exist in manual chunks/metadata.
    Gate 2: Foreign Machine Inversion Check (T5)
    Gate 3: Undocumented Safety Bypasses & Unauthorized Actions
    Gate 4: Undocumented Signaling Indicators (LED / Blink patterns)
    Gate 5: General Symptoms & Borderline Overlap Floor (T1 / T6 / T7)
    """
    if not retrieved_chunks:
        logger.info("[SAFETY_GATE] decision=REFUSE (No Chunks Retrieved), query='%s'", query)
        return False, REFUSAL_MESSAGE

    top_chunk = retrieved_chunks[0]
    raw_sim = float(top_chunk.get("score", 0.0))
    is_keyword_match = top_chunk.get("match_type") == "keyword"

    has_diagram_intent = bool(re.search(
        r"\b(diagram|diagrams|schematic|schematics|image|images|drawing|drawings|blueprint|blueprints|circuit|circuits|flowchart|flowcharts|layout|illustration|illustrations|picture|pictures|photo|photos|generate|generating|genrate|render|rendering)\b",
        query.lower()
    ))

    if not query or not query.strip():
        return True, retrieved_chunks

    # Build chunk tokens & normalized chunk error codes
    combined_chunk_text = " ".join([c.get("text", "").lower() for c in retrieved_chunks[:3]])
    all_chunk_tokens = set(re.findall(r"\b[a-zA-Z0-9_-]+\b", combined_chunk_text))

    normalized_chunk_codes = set()
    for c in retrieved_chunks:
        if c.get("error_code"):
            normalized_chunk_codes.add(normalize_code(c["error_code"]))
        txt_codes = re.findall(r"\b([A-Za-z]-?\d{2,4}|SYM-[A-Za-z0-9-]+)\b", c.get("text", ""))
        for tc in txt_codes:
            normalized_chunk_codes.add(normalize_code(tc))

    # -------------------------------------------------------------------------
    # GATE 0: Baseline similarity score threshold
    # -------------------------------------------------------------------------
    effective_threshold = 0.0 if is_keyword_match else (0.25 if has_diagram_intent else threshold)
    if raw_sim < effective_threshold:
        logger.info(
            "[SAFETY_GATE] decision=REFUSE (Below Baseline Threshold %.3f < %.3f), query='%s'",
            raw_sim, effective_threshold, query
        )
        return False, REFUSAL_MESSAGE

    # -------------------------------------------------------------------------
    # GATE 1: Error Code Verification (T2/T3 vs T4)
    # -------------------------------------------------------------------------
    if is_keyword_match:
        logger.info("[SAFETY_GATE] decision=ACCEPT (Exact Keyword Match), query='%s'", query)
        return True, retrieved_chunks

    candidate_codes = extract_candidate_error_codes(query)
    if candidate_codes:
        matched_code = None
        for code in candidate_codes:
            if code in normalized_chunk_codes or code.lower() in combined_chunk_text:
                matched_code = code
                break

        if matched_code:
            logger.info(
                "[SAFETY_GATE] decision=ACCEPT (T4: Ground-Truth Code Confirmed), query='%s', raw_sim=%.3f, matched_code=%s",
                query, raw_sim, matched_code
            )
            return True, retrieved_chunks
        else:
            logger.info(
                "[SAFETY_GATE] decision=REFUSE (T2/T3: Unsupported Error Code), query='%s', raw_sim=%.3f, candidate_codes=%s",
                query, raw_sim, candidate_codes
            )
            return False, REFUSAL_MESSAGE

    # -------------------------------------------------------------------------
    # GATE 2: Foreign Machine Inversion Check (T5)
    # -------------------------------------------------------------------------
    is_foreign, foreign_name = detect_foreign_machine(query)
    if is_foreign:
        logger.info(
            "[SAFETY_GATE] decision=REFUSE (T5: Foreign Machine), query='%s', raw_sim=%.3f, foreign_machine='%s'",
            query, raw_sim, foreign_name
        )
        return False, REFUSAL_MESSAGE

    # -------------------------------------------------------------------------
    # GATE 3: Undocumented Safety Bypasses & Unauthorized Actions
    # -------------------------------------------------------------------------
    query_tokens = _extract_content_tokens(query, machine=machine)
    critical_actions = {
        "bypass", "override", "rewire", "hack", "firmware",
        "disable", "bridge", "jumper", "defeat", "tamper"
    }
    for ca in critical_actions:
        if ca in query_tokens and ca not in all_chunk_tokens:
            logger.info("[SAFETY_GATE] decision=REFUSE (Undocumented Action), query='%s', action='%s'", query, ca)
            return False, REFUSAL_MESSAGE

    # Guard against undocumented procedural replacement queries
    if "replace" in query_tokens and not any(w in all_chunk_tokens for w in ["replace", "replacement", "replacing"]):
        logger.info("[SAFETY_GATE] decision=REFUSE (Undocumented Component Replacement), query='%s'", query)
        return False, REFUSAL_MESSAGE

    # -------------------------------------------------------------------------
    # GATE 4: Undocumented Signaling Indicators (LED / Blink Patterns)
    # -------------------------------------------------------------------------
    signaling_indicators = {"led", "blinking", "blinks", "flashing", "flickering", "flicker", "beep", "beeps"}
    blink_patterns = {"blinking", "blinks", "flashing", "flickering", "flicker", "beep", "beeps"}
    if any(ind in query_tokens for ind in signaling_indicators):
        if any(bp in query_tokens for bp in blink_patterns) or not any(ind in all_chunk_tokens for ind in signaling_indicators):
            logger.info("[SAFETY_GATE] decision=REFUSE (Undocumented Signaling), query='%s'", query)
            return False, REFUSAL_MESSAGE

    # Diagram request with recognized machine passes safety
    if has_diagram_intent:
        logger.info("[SAFETY_GATE] decision=ACCEPT (Diagram Intent), query='%s', raw_sim=%.3f", query, raw_sim)
        return True, retrieved_chunks

    # -------------------------------------------------------------------------
    # GATE 5: General Symptoms & Borderline Overlap Floor (T1 / T6 / T7)
    # -------------------------------------------------------------------------
    domain_tokens = [t for t in query_tokens if t in FACTORY_DOMAIN_VOCAB]

    # Sub-case 5A: Zero domain vocabulary and low similarity -> pure gibberish / off-topic
    if not domain_tokens and raw_sim < 0.40:
        logger.info(
            "[SAFETY_GATE] decision=REFUSE (T1: Zero Domain Vocab & Low Sim), query='%s', raw_sim=%.3f",
            query, raw_sim
        )
        return False, REFUSAL_MESSAGE

    # Sub-case 5B: Below general symptom floor
    if raw_sim < 0.35:
        logger.info(
            "[SAFETY_GATE] decision=REFUSE (T1: Below Symptom Floor), query='%s', raw_sim=%.3f",
            query, raw_sim
        )
        return False, REFUSAL_MESSAGE

    # Sub-case 5C: Borderline similarity [0.35, 0.50) -> token overlap check
    if raw_sim < 0.50:
        content_tokens = [t for t in query_tokens if len(t) > 1 and not t.isdigit()]
        if content_tokens:
            matching = [t for t in content_tokens if t in all_chunk_tokens]
            overlap_ratio = len(matching) / len(content_tokens)
            if overlap_ratio < 0.40:
                logger.info(
                    "[SAFETY_GATE] decision=REFUSE (T6: Borderline Low Overlap), query='%s', raw_sim=%.3f, overlap=%.2f",
                    query, raw_sim, overlap_ratio
                )
                return False, REFUSAL_MESSAGE
            else:
                logger.info(
                    "[SAFETY_GATE] decision=ACCEPT (T6: Borderline Overlap Validated), query='%s', raw_sim=%.3f, overlap=%.2f",
                    query, raw_sim, overlap_ratio
                )
                return True, retrieved_chunks

    # Sub-case 5D: Strong semantic similarity (>= 0.50) with domain vocabulary
    logger.info(
        "[SAFETY_GATE] decision=ACCEPT (T7: Strong Semantic Symptom), query='%s', raw_sim=%.3f, domain_tokens=%s",
        query, raw_sim, domain_tokens
    )
    return True, retrieved_chunks
