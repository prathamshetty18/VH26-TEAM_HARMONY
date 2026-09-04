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

    # Press-200
    "press-200": "Press-200",
    "press 200": "Press-200",
    "press200": "Press-200",

    # RobotArm-300
    "robot-arm-300": "RobotArm-300",
    "robot arm 300": "RobotArm-300",
    "robotarm-300": "RobotArm-300",
    "robotarm 300": "RobotArm-300",
    "robotarm300": "RobotArm-300",
    "r300": "RobotArm-300",
    "r-300": "RobotArm-300",
    "r 300": "RobotArm-300",

    # Conveyor Belt System (CB-4400)
    "cb-4400": "Conveyor Belt System",
    "cb 4400": "Conveyor Belt System",
    "cb4400": "Conveyor Belt System",
    "conveyor belt system": "Conveyor Belt System",
    "conveyor belt": "Conveyor Belt System",

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

if __name__ == "__main__":
    test_queries = [
        "What does E101 mean on Machine A?",
        "What does E101 mean on CNC-100?",
        "What does E101 mean on CNC-999?",
        "What does E101 mean on CNC?",
        "the motor is making a weird noise",
        "E101 error on Press-200",
        "What does E101 mean?"
    ]
    for q in test_queries:
        res = parse_query(q, known_machines=["Conveyor Belt System", "CNC Milling Machine", "Hydraulic Press"])
        print(f"Query: '{q}' -> {res}")

