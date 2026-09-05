import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from src.api import app
from src.diagrams import DIAGRAM_CATALOG, get_diagram_for_chunk

client = TestClient(app)

def test_diagram_catalog_structure():
    """Verify DIAGRAM_CATALOG has been shrunk to only machine-level defaults and contains no hardcoded error codes."""
    print("\n--- TEST: DIAGRAM_CATALOG Structure & Size ---")
    print(f"DIAGRAM_CATALOG entries: {len(DIAGRAM_CATALOG)}")
    for key, val in DIAGRAM_CATALOG.items():
        print(f"  {key} -> {val['filename']}")

    # Must contain exactly the 6 machine default entries
    assert len(DIAGRAM_CATALOG) == 6, f"Expected exactly 6 default entries, got {len(DIAGRAM_CATALOG)}"
    for (machine, code) in DIAGRAM_CATALOG.keys():
        assert code == "DEFAULT", f"DIAGRAM_CATALOG should only contain 'DEFAULT' entries, found code: '{code}'"
        assert machine in [
            "CNC-100",
            "CNC Milling Machine",
            "Hydraulic Press",
            "Press-200",
            "Conveyor Belt System",
            "RobotArm-300"
        ], f"Unexpected machine key in catalog: {machine}"
    print("✓ DIAGRAM_CATALOG correctly contains only 6 machine-level defaults with zero hardcoded error codes.")


def test_diagram_retrieval_all_machines():
    print("\n==================================================")
    print("TESTING COMPREHENSIVE DIAGRAM RETRIEVAL PIPELINE")
    print("==================================================")

    # 1. CNC-100 (E101)
    print("\n--- TEST 1: E101 on CNC-100 ---")
    resp = client.post("/query", json={"message": "What does E101 mean on CNC-100?", "session_id": "test_diag_cnc100"})
    assert resp.status_code == 200
    diagrams = resp.json().get("diagrams", [])
    assert len(diagrams) > 0, "No diagram returned for E101 on CNC-100"
    assert "cnc100_cooling_fan.svg" in diagrams[0]["url"]
    print(f"✓ CNC-100 E101 -> {diagrams[0]['filename']} ({diagrams[0]['title']})")

    # 2. CNC Milling Machine (E101 & E108)
    print("\n--- TEST 2a: E101 on CNC Milling Machine (MX-7) ---")
    resp = client.post("/query", json={"message": "What does E101 mean on CNC Milling Machine MX-7?", "session_id": "test_diag_mx7_e101"})
    assert resp.status_code == 200
    diagrams = resp.json().get("diagrams", [])
    assert len(diagrams) > 0, "No diagram returned for E101 on CNC Milling Machine"
    assert "cnc_coolant_circuit.svg" in diagrams[0]["url"]
    print(f"✓ CNC Milling Machine E101 -> {diagrams[0]['filename']} ({diagrams[0]['title']})")

    print("\n--- TEST 2b: E108 on CNC Milling Machine (MX-7) ---")
    resp = client.post("/query", json={"message": "How do I fix E108 spindle motor overtemperature on the CNC Milling Machine?", "session_id": "test_diag_mx7_e108"})
    assert resp.status_code == 200
    diagrams = resp.json().get("diagrams", [])
    assert len(diagrams) > 0, "No diagram returned for E108 on CNC Milling Machine"
    assert "cnc_spindle_motor.svg" in diagrams[0]["url"]
    print(f"✓ CNC Milling Machine E108 -> {diagrams[0]['filename']} ({diagrams[0]['title']})")

    # 3. Conveyor Belt System (E101 & E202)
    print("\n--- TEST 3: E101 on Conveyor Belt System (CB-4400) ---")
    resp = client.post("/query", json={"message": "How do I fix E101 on the CB-4400 conveyor belt?", "session_id": "test_diag_conveyor"})
    assert resp.status_code == 200
    diagrams = resp.json().get("diagrams", [])
    assert len(diagrams) > 0, "No diagram returned for E101 on Conveyor"
    assert "conveyor_vfd_drive.svg" in diagrams[0]["url"]
    print(f"✓ Conveyor Belt E101 -> {diagrams[0]['filename']} ({diagrams[0]['title']})")

    # 4. Press-200 (E101 & E202)
    print("\n--- TEST 4: E101 on Press-200 ---")
    resp = client.post("/query", json={"message": "Why does Press-200 show hydraulic oil pressure low E101?", "session_id": "test_diag_press200"})
    assert resp.status_code == 200
    diagrams = resp.json().get("diagrams", [])
    assert len(diagrams) > 0, "No diagram returned for E101 on Press-200"
    assert "press200_hydraulic_circuit.svg" in diagrams[0]["url"]
    print(f"✓ Press-200 E101 -> {diagrams[0]['filename']} ({diagrams[0]['title']})")

    # 5. Hydraulic Press HP-2200 (H201 & H205) - Mandatory prompt test case
    print("\n--- TEST 5: H205 on Hydraulic Press HP-2200 (Mandatory Check) ---")
    resp = client.post("/query", json={"message": "What is the corrective action for fault H205 on the HP-2200 hydraulic press?", "session_id": "test_diag_hp2200_h205"})
    assert resp.status_code == 200
    diagrams = resp.json().get("diagrams", [])
    assert len(diagrams) > 0, "No diagram returned for H205 on HP-2200"
    assert "hydraulic_press_manifold.svg" in diagrams[0]["url"]
    print(f"✓ HP-2200 H205 -> {diagrams[0]['filename']} ({diagrams[0]['title']})")

    # 6. RobotArm-300 (R101)
    print("\n--- TEST 6: R101 on RobotArm-300 ---")
    resp = client.post("/query", json={"message": "What does R101 mean on RobotArm-300?", "session_id": "test_diag_robot"})
    assert resp.status_code == 200
    diagrams = resp.json().get("diagrams", [])
    assert len(diagrams) > 0, "No diagram returned for R101 on RobotArm-300"
    assert "robot_arm_joint_drive.svg" in diagrams[0]["url"]
    print(f"✓ RobotArm-300 R101 -> {diagrams[0]['filename']} ({diagrams[0]['title']})")

    # 7. Symptom query - CNC spindle whining (Mandatory prompt test case)
    print("\n--- TEST 7: CNC Spindle Whining Symptom (Mandatory Check) ---")
    resp = client.post("/query", json={"message": "The CNC Milling Machine spindle is whining and making excessive high-frequency noise.", "session_id": "test_diag_symptom_whine"})
    assert resp.status_code == 200
    diagrams = resp.json().get("diagrams", [])
    assert len(diagrams) > 0, "No diagram returned for CNC Milling Machine spindle whining"
    assert "cnc_spindle_motor.svg" in diagrams[0]["url"]
    print(f"✓ CNC Spindle Whining -> {diagrams[0]['filename']} ({diagrams[0]['title']})")

    # 8. Fallback resolution test of last resort
    print("\n--- TEST 8: Machine Default Fallback Resolution ---")
    fb = get_diagram_for_chunk("RobotArm-300")
    assert fb is not None
    assert fb["filename"] == "robot_arm_joint_drive.svg"

    fb_cnc = get_diagram_for_chunk("CNC-100")
    assert fb_cnc is not None
    assert fb_cnc["filename"] == "cnc100_cooling_fan.svg"

    fb_press = get_diagram_for_chunk("Hydraulic Press")
    assert fb_press is not None
    assert fb_press["filename"] == "hydraulic_press_manifold.svg"

    fb_p200 = get_diagram_for_chunk("Press-200")
    assert fb_p200 is not None
    assert fb_p200["filename"] == "press200_hydraulic_circuit.svg"
    print("✓ get_diagram_for_chunk resolves machine-level defaults accurately.")

    # 9. Static SVG file route check
    print("\n--- TEST 9: Static Schematic Route Check ---")
    for svg_file in [
        "cnc_coolant_circuit.svg",
        "cnc_spindle_motor.svg",
        "hydraulic_press_manifold.svg",
        "conveyor_vfd_drive.svg",
        "robot_arm_joint_drive.svg",
        "cnc100_cooling_fan.svg",
        "press200_hydraulic_circuit.svg"
    ]:
        d_resp = client.get(f"/diagrams/{svg_file}")
        assert d_resp.status_code == 200, f"Failed to retrieve /diagrams/{svg_file}"
        assert "image/svg+xml" in d_resp.headers.get("content-type", "")
        print(f"✓ /diagrams/{svg_file} -> HTTP 200 ({len(d_resp.content)} bytes)")

    print("\n==================================================")
    print("ALL COMPREHENSIVE DIAGRAM RETRIEVAL TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    test_diagram_catalog_structure()
    test_diagram_retrieval_all_machines()

