def check_ambiguity(parsed_query, retrieved_chunks):
    """
    Detects if an error code query is ambiguous across multiple machines.
    Returns:
    {
        "ambiguous": bool,
        "options": [ {"machine": str, "summary": str}, ... ]
    }
    """
    error_code = parsed_query.get("error_code")
    specified_machine = parsed_query.get("machine")

    # If a machine was explicitly specified in the query, it is not ambiguous
    if specified_machine or not error_code:
        return {"ambiguous": False, "options": []}

    # Group retrieved chunks by machine for the matching error_code
    import re
    machine_options = {}
    for chunk in retrieved_chunks:
        c_machine = chunk.get("machine")
        c_model = chunk.get("model")
        c_err = chunk.get("error_code")
        
        if c_err == error_code and c_machine and c_machine != "Unknown":
            display_machine = f"{c_machine} ({c_model})" if c_model and c_model != "Unknown" and f"({c_model})" not in c_machine else c_machine
            text = chunk.get("text", "")
            meaning_match = re.search(r"^MEANING:\s*(.+)$", text, re.MULTILINE)
            summary = meaning_match.group(1).strip() if meaning_match else None
            
            if not summary:
                sec_match = re.search(r"^SECTION:\s*(.+)$", text, re.MULTILINE)
                summary = sec_match.group(1).strip() if sec_match else f"Error Code {error_code}"

            # Only overwrite if we found a genuine MEANING or don't have one yet
            if display_machine not in machine_options or meaning_match:
                machine_options[display_machine] = summary

    # If the error code spans 2+ different machines, it is ambiguous!
    if len(machine_options) >= 2:
        options = [
            {"machine": machine, "summary": summary}
            for machine, summary in machine_options.items()
        ]
        return {
            "ambiguous": True,
            "options": options
        }

    return {"ambiguous": False, "options": []}

if __name__ == "__main__":
    # Test case 1: Ambiguous query (E101, no machine specified)
    test_chunks = [
        {
            "machine": "CNC-100",
            "error_code": "E101",
            "text": "SECTION: E101 Overview\nMEANING: Excessive motor temperature."
        },
        {
            "machine": "Press-200",
            "error_code": "E101",
            "text": "SECTION: E101 Overview\nMEANING: Hydraulic oil pressure low."
        }
    ]
    res1 = check_ambiguity({"error_code": "E101", "machine": None}, test_chunks)
    print("Test 1 (E101 no machine):", res1)

    # Test case 2: Unambiguous (machine specified)
    res2 = check_ambiguity({"error_code": "E101", "machine": "CNC-100"}, test_chunks)
    print("Test 2 (E101 with machine):", res2)
