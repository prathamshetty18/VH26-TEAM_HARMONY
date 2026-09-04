import re

DEFAULT_KNOWN_MACHINES = [
    "Conveyor Belt System",
    "CNC Milling Machine",
    "Hydraulic Press"
]

MACHINE_ALIASES = {
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
    "milling": "CNC Milling Machine",
    "cnc": "CNC Milling Machine",

    # Hydraulic Press (HP-2200)
    "hp-2200": "Hydraulic Press",
    "hp 2200": "Hydraulic Press",
    "hp2200": "Hydraulic Press",
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

    # 2. Detect Error Code (Supports E-series, H-series, and SYM- series)
    detected_error_code = None
    err_match = re.search(r"\b([EH]\d{3}|SYM-[A-Z0-9-]+)\b", query, re.IGNORECASE)
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
