import re

DEFAULT_KNOWN_MACHINES = ["CNC-100", "Press-200", "RobotArm-300"]

MACHINE_ALIASES = {
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

def parse_query(query: str, known_machines=None, known_error_codes=None):
    """
    Extracts machine name and error code from a query string.
    Returns:
    {
        "machine": str or None,
        "error_code": str or None,
        "raw_query": str
    }
    """
    if known_machines is None:
        known_machines = DEFAULT_KNOWN_MACHINES

    query_lower = query.lower()

    # 1. Detect Machine Name
    detected_machine = None
    
    # First check aliases
    for alias, canonical in MACHINE_ALIASES.items():
        if alias in query_lower:
            detected_machine = canonical
            break

    # If no alias hit, check known machines
    if not detected_machine:
        for m in known_machines:
            if m.lower() in query_lower:
                detected_machine = m
                break

    # 2. Detect Error Code
    detected_error_code = None
    err_match = re.search(r"\b(E\d{3})\b", query, re.IGNORECASE)
    if err_match:
        detected_error_code = err_match.group(1).upper()

    return {
        "machine": detected_machine,
        "error_code": detected_error_code,
        "raw_query": query
    }

if __name__ == "__main__":
    test_queries = [
        "What does E101 mean on Machine A?",
        "What does E101 mean on CNC-100?",
        "the motor is making a weird noise",
        "E101 error on Press-200",
        "What does E101 mean?"
    ]
    for q in test_queries:
        res = parse_query(q)
        print(f"Query: '{q}' -> {res}")
