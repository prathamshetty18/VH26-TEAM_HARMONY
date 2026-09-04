import re

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
    "robot arm": "RobotArm-300",
    "robotic arm": "RobotArm-300",
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
    "conveyor": "Conveyor Belt System",
    "belt conveyor": "Conveyor Belt System",

    # CNC-100 (Model X200)
    "cnc-100": "CNC-100",
    "cnc 100": "CNC-100",
    "cnc100": "CNC-100",
    "x200": "CNC-100",
    "x-200": "CNC-100",
    "x 200": "CNC-100",

    # Press-200 (Model P400)
    "press-200": "Press-200",
    "press 200": "Press-200",
    "press200": "Press-200",
    "p400": "Press-200",
    "p-400": "Press-200",
    "p 400": "Press-200",

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
    "milling": "CNC Milling Machine",
    "cnc": "CNC Milling Machine",

    # Hydraulic Press (HP-2200)
    "hp-2200": "Hydraulic Press",
    "hp 2200": "Hydraulic Press",
    "hp2200": "Hydraulic Press",
    "hydraulic press 2200": "Hydraulic Press",
    "hydraulic press": "Hydraulic Press",
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
    
    # First check aliases (longest first to avoid substring collision)
    sorted_aliases = sorted(MACHINE_ALIASES.keys(), key=len, reverse=True)
    for alias in sorted_aliases:
        if re.search(rf"\b{re.escape(alias)}\b", query_lower):
            detected_machine = MACHINE_ALIASES[alias]
            break

    # If no alias hit, check known machines
    if not detected_machine:
        for m in sorted(known_machines, key=len, reverse=True):
            if re.search(rf"\b{re.escape(m.lower())}\b", query_lower):
                detected_machine = m
                break

    # 2. Detect Error Code (Supports alphanumeric error codes like E101, E-101, H205, R101, and SYM- series)
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
