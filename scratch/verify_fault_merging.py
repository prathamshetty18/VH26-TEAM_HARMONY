# -*- coding: utf-8 -*-
import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.api import handle_query, QueryRequest
import json

def test_cases():
    print("=" * 60)
    print("RUNNING VERIFICATION OF FAULT MERGING & CANDIDATE RANKING")
    print("=" * 60)

    # Test 1: E101 on CNC-100
    print("\n--- Test 1: What does E101 mean on CNC-100? ---")
    req1 = QueryRequest(message="What does E101 mean on CNC-100?")
    resp1 = handle_query(req1)
    
    print(f"Primary Fault: {resp1.fault}")
    print(f"Component: {resp1.component}")
    print(f"Confidence: {resp1.confidence_percentage}% ({resp1.confidence_level})")
    print(f"Number of possible faults: {len(resp1.possible_faults)}")
    
    assert len(resp1.possible_faults) == 1, f"Expected exactly 1 fault, got {len(resp1.possible_faults)}"
    pf1 = resp1.possible_faults[0]
    print(f"Candidate 0: code={pf1.fault_code}, name={pf1.fault_name}, display={pf1.fault}")
    print(f"Supporting Evidence: {pf1.supporting_evidence}")
    
    assert pf1.fault_code == "E101"
    assert "Overview" not in pf1.fault_name
    assert "Troubleshooting" not in pf1.fault_name
    assert len(pf1.supporting_evidence) >= 2
    assert any("Overview" in ev for ev in pf1.supporting_evidence)
    assert any("Troubleshooting" in ev for ev in pf1.supporting_evidence)
    assert pf1.confidence_percentage >= 90
    print("[PASS] Test 1 passed!")

    # Test 2: E101 on CB-4400 Conveyor Belt
    print("\n--- Test 2: How do I fix error E101 on the CB-4400 conveyor belt? ---")
    req2 = QueryRequest(message="How do I fix error E101 on the CB-4400 conveyor belt?")
    resp2 = handle_query(req2)
    
    print(f"Primary Fault: {resp2.fault}")
    print(f"Component: {resp2.component}")
    print(f"Confidence: {resp2.confidence_percentage}% ({resp2.confidence_level})")
    print(f"Number of possible faults: {len(resp2.possible_faults)}")
    
    assert len(resp2.possible_faults) == 1, f"Expected exactly 1 fault, got {len(resp2.possible_faults)}"
    pf2 = resp2.possible_faults[0]
    print(f"Candidate 0: code={pf2.fault_code}, name={pf2.fault_name}, display={pf2.fault}")
    print(f"Supporting Evidence: {pf2.supporting_evidence}")
    
    assert pf2.fault_code == "E101"
    assert "Drive Motor Overcurrent" in pf2.fault_name or "Overload" in pf2.fault_name
    assert len(pf2.supporting_evidence) >= 2
    assert pf2.confidence_percentage >= 90
    print("[PASS] Test 2 passed!")

    # Test 3: Press-200 E101
    print("\n--- Test 3: What causes error E101 on Press-200? ---")
    req3 = QueryRequest(message="What causes error E101 on Press-200?")
    resp3 = handle_query(req3)
    
    print(f"Primary Fault: {resp3.fault}")
    print(f"Component: {resp3.component}")
    print(f"Confidence: {resp3.confidence_percentage}% ({resp3.confidence_level})")
    print(f"Number of possible faults: {len(resp3.possible_faults)}")
    
    assert len(resp3.possible_faults) == 1, f"Expected exactly 1 fault, got {len(resp3.possible_faults)}"
    pf3 = resp3.possible_faults[0]
    print(f"Candidate 0: code={pf3.fault_code}, name={pf3.fault_name}, display={pf3.fault}")
    print(f"Supporting Evidence: {pf3.supporting_evidence}")
    
    assert pf3.fault_code == "E101"
    assert "Overview" not in pf3.fault_name
    assert "Troubleshooting" not in pf3.fault_name
    assert "Hydraulic" in pf3.fault_name or "Pressure" in pf3.fault_name
    assert any("Overview" in ev for ev in pf3.supporting_evidence)
    assert any("Troubleshooting" in ev for ev in pf3.supporting_evidence)
    print("[PASS] Test 3 passed!")

    # Test 4: Symptom query
    print("\n--- Test 4: The spindle is whining and vibrating on MX-7 ---")
    req4 = QueryRequest(message="The spindle is whining and vibrating on the MX-7")
    resp4 = handle_query(req4)
    
    print(f"Primary Fault: {resp4.fault}")
    print(f"Component: {resp4.component}")
    print(f"Confidence: {resp4.confidence_percentage}% ({resp4.confidence_level})")
    print(f"Number of possible faults: {len(resp4.possible_faults)}")
    
    assert len(resp4.possible_faults) >= 1
    for i, pf in enumerate(resp4.possible_faults):
        print(f"Candidate {i}: primary={pf.is_primary}, score={pf.confidence_score}, fault={pf.fault}, comp={pf.component}")
        print(f"  Supporting Evidence: {pf.supporting_evidence}")
        assert "Overview" not in pf.fault
        assert "Troubleshooting" not in pf.fault

    print("[PASS] Test 4 passed!")
    print("\nALL VERIFICATION TESTS COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    test_cases()
