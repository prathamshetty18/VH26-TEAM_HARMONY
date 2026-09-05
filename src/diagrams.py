"""
Diagram and Schematic Catalog for MachineAssist Troubleshooting System.
Associates machine models, error codes, and technical sections with high-resolution
schematics, wiring diagrams, and hydraulic flowcharts.
"""

from typing import Optional, Dict, Any

DIAGRAM_CATALOG = {
    # CNC-100 (Model X200)
    ("CNC-100", "DEFAULT"): {
        "title": "Cooling Circuit & Spindle Thermal Flow Diagram",
        "filename": "cnc100_cooling_fan.svg",
        "caption": "Cooling fan assembly, ventilation ducts, and heat dissipation path",
        "system": "Cooling System"
    },

    # CNC Milling Machine (Model MX-7 Precision)
    ("CNC Milling Machine", "DEFAULT"): {
        "title": "Through-Spindle Coolant (TSC) Flow Circuit",
        "filename": "cnc_coolant_circuit.svg",
        "caption": "Inline Electronic Flow Sensor FL-10, Primary Filter Unit, and High-Pressure Delivery Line",
        "system": "Cooling System"
    },

    # Hydraulic Press (Model HP-2200)
    ("Hydraulic Press", "DEFAULT"): {
        "title": "Main Cylinder Hydraulic Pressure Loop & Manifold",
        "filename": "hydraulic_press_manifold.svg",
        "caption": "Pump intake manifold, relief bypass valve, proportional manifold, and main ram chamber",
        "system": "Hydraulics"
    },

    # Press-200 (Model P400)
    ("Press-200", "DEFAULT"): {
        "title": "Main Cylinder Hydraulic Pressure Loop",
        "filename": "press200_hydraulic_circuit.svg",
        "caption": "Pump intake manifold, relief bypass valve, and main ram chamber",
        "system": "Hydraulics"
    },

    # Conveyor Belt System (Model CB-4400)
    ("Conveyor Belt System", "DEFAULT"): {
        "title": "Variable Frequency Drive (VFD) & Inverter Power Circuit",
        "filename": "conveyor_vfd_drive.svg",
        "caption": "VFD inverter module, thermal overload relay, and 3-phase motor winding schematic",
        "system": "Drive & Electrical"
    },

    # RobotArm-300 (Model R300)
    ("RobotArm-300", "DEFAULT"): {
        "title": "Joint Axis Servo Drive & Dual Optical Encoder Loop",
        "filename": "robot_arm_joint_drive.svg",
        "caption": "AC synchronous brushless servo motor, harmonic drive reducer, and resolver feedback",
        "system": "Robotics & Motion Control"
    }
}

def get_diagram_for_chunk(machine: str, error_code: Optional[str] = None, section: Optional[str] = None) -> Optional[Dict[str, str]]:
    """
    Fallback diagram resolver of last resort.
    When retrieved chunks lack embedded diagram metadata, returns the machine-level
    default schematic without guessing or maintaining hardcoded error-code tables.
    """
    if not machine:
        return None

    # 1. Exact match in catalog
    match = DIAGRAM_CATALOG.get((machine, "DEFAULT"))
    if match:
        return {
            **match,
            "url": f"/static/diagrams/{match['filename']}"
        }

    # 2. Match by canonical machine identity / model keywords
    m_lower = machine.lower()
    canonical_key = None

    if "robot" in m_lower or "r300" in m_lower or "arm" in m_lower:
        canonical_key = ("RobotArm-300", "DEFAULT")
    elif "cb-4400" in m_lower or "conveyor" in m_lower:
        canonical_key = ("Conveyor Belt System", "DEFAULT")
    elif "hp-2200" in m_lower or "hydraulic press" in m_lower:
        canonical_key = ("Hydraulic Press", "DEFAULT")
    elif "p400" in m_lower or "press-200" in m_lower or "press 200" in m_lower:
        canonical_key = ("Press-200", "DEFAULT")
    elif "mx-7" in m_lower or "milling" in m_lower:
        canonical_key = ("CNC Milling Machine", "DEFAULT")
    elif "x200" in m_lower or "cnc-100" in m_lower or "cnc 100" in m_lower or "cnc" in m_lower:
        canonical_key = ("CNC-100", "DEFAULT")
    elif "press" in m_lower:
        canonical_key = ("Hydraulic Press", "DEFAULT")

    if canonical_key and canonical_key in DIAGRAM_CATALOG:
        data = DIAGRAM_CATALOG[canonical_key]
        return {
            **data,
            "url": f"/static/diagrams/{data['filename']}"
        }

    return None
