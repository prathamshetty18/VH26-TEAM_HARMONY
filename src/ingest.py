import os
import re
from typing import List, Dict, Any, Optional

def resolve_diagram_for_section(
    machine: str,
    model: str,
    error_code: Optional[str],
    section_title: str,
    text: str
) -> Optional[Dict[str, str]]:
    """
    Authoritative chunk-level diagram resolution performed during manual ingestion.
    Inspects explicit DIAGRAM directives first, then associates the chunk with
    the technically accurate subsystem schematic based on machine, error code, and section content:
    - cnc_coolant_circuit.svg: Through-Spindle Coolant (TSC), FL-10 flow sensor, cooling fan, reservoir
    - cnc_spindle_motor.svg: Spindle motor stator RTD thermistor, chiller refrigeration, ceramic bearings, tool unclamp, drives
    - conveyor_vfd_drive.svg: Variable Frequency Drive (VFD), inverter, pulse tachometer, motor overload, drum lagging
    - hydraulic_press_manifold.svg: Proportional directional valve PV-01, pressure transducer PT-01, chiller heat exchanger, accumulators
    - robot_arm_joint_drive.svg: Brushless AC servo, harmonic drive reducer, dual optical resolver
    """
    # 1. Explicit directive inside text
    diag_match = re.search(r"^DIAGRAM:\s*(.+)$", text, re.MULTILINE)
    if diag_match:
        diag_filename = diag_match.group(1).strip()
        return {
            "title": f"{section_title} Schematic",
            "filename": diag_filename,
            "url": f"/static/diagrams/{diag_filename}",
            "caption": f"Technical schematic for {machine} {section_title}"
        }

    m = (machine or "").lower()
    code = (error_code or "").upper()
    sec = (section_title or "").lower()

    # --- CNC-100 ---
    if "cnc-100" in m or m == "cnc-100":
        if code == "E102":
            return {
                "title": "Spindle Axis Drive & Overload Protection Loop",
                "filename": "cnc100_spindle_drive.svg",
                "url": "/static/diagrams/cnc100_spindle_drive.svg",
                "caption": "Main drive motor windings, spindle mechanical coupling, and current overload sensor"
            }
        # E101 (motor temp/cooling fan/ventilation) & E103 (coolant pressure below threshold) & default
        return {
            "title": "Cooling Circuit & Spindle Thermal Flow Diagram",
            "filename": "cnc100_cooling_fan.svg",
            "url": "/static/diagrams/cnc100_cooling_fan.svg",
            "caption": "Cooling fan assembly, ventilation ducts, and heat dissipation path"
        }

    # --- CNC Milling Machine (MX-7) ---
    if "cnc milling" in m or "mx-7" in m:
        if code == "E101" or "coolant" in sec or "fl-10" in sec or code == "SYM-MIST-LEAKAGE":
            return {
                "title": "Through-Spindle Coolant (TSC) Flow Circuit",
                "filename": "cnc_coolant_circuit.svg",
                "url": "/static/diagrams/cnc_coolant_circuit.svg",
                "caption": "Inline Electronic Flow Sensor FL-10, Primary Filter Unit, and High-Pressure Delivery Line"
            }
        if code == "E108":
            return {
                "title": "Spindle Motor Stator & Chiller Loop Assembly",
                "filename": "cnc_spindle_motor.svg",
                "url": "/static/diagrams/cnc_spindle_motor.svg",
                "caption": "Platinum RTD thermistor wiring, glycol cooling jacket, and bearing cartridge"
            }
        if code == "SYM-SPINDLE-WHINING":
            return {
                "title": "Hybrid Ceramic Spindle Bearing Architecture",
                "filename": "cnc_spindle_motor.svg",
                "url": "/static/diagrams/cnc_spindle_motor.svg",
                "caption": "Dual angular contact bearing pack, labyrinth air purge seal, and synthetic grease channels"
            }
        if code == "SYM-CHATTER-MARKS":
            return {
                "title": "Spindle Bearing Preload & Slideway Damping Assembly",
                "filename": "cnc_spindle_motor.svg",
                "url": "/static/diagrams/cnc_spindle_motor.svg",
                "caption": "Preloaded angular contact bearings, hydraulic toolholder chuck, and slideway gib strips"
            }
        if code == "E202":
            return {
                "title": "Z-Axis Slideway Optical Scale & Servo Drive Loop",
                "filename": "cnc_spindle_motor.svg",
                "url": "/static/diagrams/cnc_spindle_motor.svg",
                "caption": "Heidenhain glass linear optical scale, air purge regulator, and ballscrew feedback"
            }
        if code == "E310":
            return {
                "title": "Spindle Tool Unclamp Piston & Air Purge Manifold",
                "filename": "cnc_spindle_motor.svg",
                "url": "/static/diagrams/cnc_spindle_motor.svg",
                "caption": "Pneumatic unclamp cylinder, Belleville spring stack, and tool clamp limit switches"
            }
        if code == "E415":
            return {
                "title": "AC Spindle Drive Power Module & Braking Resistor Circuit",
                "filename": "cnc_spindle_motor.svg",
                "url": "/static/diagrams/cnc_spindle_motor.svg",
                "caption": "Dynamic braking IGBT module, external resistor bank, and thermal overload sensor"
            }
        if code == "E520":
            return {
                "title": "Spindle Position Sensor & Orientation Encoder Loop",
                "filename": "cnc_spindle_motor.svg",
                "url": "/static/diagrams/cnc_spindle_motor.svg",
                "caption": "Magnetic spindle orientation sensor, pulse pickup gap, and tooth wheel assembly"
            }
        if code == "SYM-BORE-ACCURACY":
            return {
                "title": "Spindle Taper & Toolholder Interface Geometry",
                "filename": "cnc_spindle_motor.svg",
                "url": "/static/diagrams/cnc_spindle_motor.svg",
                "caption": "CAT-40 / BT-40 precision spindle taper, drawbar pull-stud retention balls, and gauge line"
            }
        # General CNC Milling fallback
        return {
            "title": "Through-Spindle Coolant (TSC) Flow Circuit",
            "filename": "cnc_coolant_circuit.svg",
            "url": "/static/diagrams/cnc_coolant_circuit.svg",
            "caption": "Inline Electronic Flow Sensor FL-10, Primary Filter Unit, and High-Pressure Delivery Line"
        }

    # --- Hydraulic Press (HP-2200) ---
    if "hydraulic press" in m or "hp-2200" in m or "hp2200" in m:
        if code == "H205":
            return {
                "title": "Hydraulic Oil Filtration & Water Chiller Heat Exchanger",
                "filename": "hydraulic_press_manifold.svg",
                "url": "/static/diagrams/hydraulic_press_manifold.svg",
                "caption": "Shell-and-tube oil-to-water heat exchanger, thermostatic modulating valve, and tank return line"
            }
        if code == "H312":
            return {
                "title": "Main Ram Proportional Hydraulic Manifold & Accumulator Circuit",
                "filename": "hydraulic_press_manifold.svg",
                "url": "/static/diagrams/hydraulic_press_manifold.svg",
                "caption": "High-pressure bladder accumulator bank, proportional directional valve, and prefill circuit"
            }
        # Default for H201, H420, H515, H622, and all symptoms
        return {
            "title": "Main Ram Proportional Hydraulic Manifold",
            "filename": "hydraulic_press_manifold.svg",
            "url": "/static/diagrams/hydraulic_press_manifold.svg",
            "caption": "Proportional directional valve PV-01, cylinder pressure transducer PT-01, and pilot check line"
        }

    # --- Press-200 (P400) ---
    if "press-200" in m or "press200" in m:
        if code == "E202":
            return {
                "title": "Hydraulic Press E-Stop & Safety Valve Interlock",
                "filename": "press200_hydraulic_circuit.svg",
                "url": "/static/diagrams/press200_hydraulic_circuit.svg",
                "caption": "Emergency stop circuit, master dump valve, and cylinder lock blocks"
            }
        if code == "E203":
            return {
                "title": "Hydraulic Ram Alignment & Guide Pillar Circuit",
                "filename": "press200_hydraulic_circuit.svg",
                "url": "/static/diagrams/press200_hydraulic_circuit.svg",
                "caption": "Main cylinder ram alignment guide pillars, stroke sensor, and leveling manifold"
            }
        return {
            "title": "Main Cylinder Hydraulic Pressure Loop",
            "filename": "press200_hydraulic_circuit.svg",
            "url": "/static/diagrams/press200_hydraulic_circuit.svg",
            "caption": "Pump intake manifold, relief bypass valve, and main ram chamber"
        }

    # --- Conveyor Belt System (CB-4400) ---
    if "conveyor" in m or "cb-4400" in m or "cb4400" in m:
        if code in ("E202", "E305"):
            return {
                "title": "Optical Shaft Speed Encoder & Tail Pulley Assembly",
                "filename": "conveyor_vfd_drive.svg",
                "url": "/static/diagrams/conveyor_vfd_drive.svg",
                "caption": "Speed encoder SE-04, belt slip sensor, and mechanical tension take-up carriage"
            }
        return {
            "title": "Variable Frequency Drive (VFD) & Inverter Power Circuit",
            "filename": "conveyor_vfd_drive.svg",
            "url": "/static/diagrams/conveyor_vfd_drive.svg",
            "caption": "VFD inverter module, thermal overload relay, and 3-phase motor winding schematic"
        }

    # --- RobotArm-300 (R300) ---
    if "robot" in m or "r300" in m or "arm" in m:
        return {
            "title": "Joint Axis Servo Drive & Dual Optical Encoder Loop",
            "filename": "robot_arm_joint_drive.svg",
            "url": "/static/diagrams/robot_arm_joint_drive.svg",
            "caption": "AC synchronous brushless servo motor, harmonic drive reducer, and resolver feedback"
        }

    return None

def load_and_chunk_manuals(manuals_dir="data/manuals") -> List[Dict[str, Any]]:
    """
    Reads manual text files from manuals_dir, normalizes and splits them into structured
    chunks based on 'SECTION:' markers, and extracts error_code, machine, model, and page.
    Supports both single-section header format and dual-section error code/troubleshooting format.
    """
    chunks = []
    
    if not os.path.exists(manuals_dir):
        return chunks

    for filename in sorted(os.listdir(manuals_dir)):
        if not filename.endswith(".txt"):
            continue
            
        filepath = os.path.join(manuals_dir, filename)
        
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Global header metadata
        global_machine = None
        global_model = None

        m_match = re.search(r"^MACHINE:\s*(.+)$", content, re.MULTILINE)
        if m_match:
            global_machine = m_match.group(1).strip()

        mod_match = re.search(r"^MODEL:\s*(.+)$", content, re.MULTILINE)
        if mod_match:
            global_model = mod_match.group(1).strip()

        # Normalize format: if ERROR CODE: precedes SECTION:, swap so SECTION: comes first
        normalized = re.sub(
            r"(?m)^ERROR CODE:\s*([^\n]+)\s*\n\s*SECTION:\s*([^\n]+)$",
            r"SECTION: \2\nERROR CODE: \1",
            content
        )

        # Split on SECTION:
        sections = re.split(r"(?m)^SECTION:\s*", normalized)
        
        current_error_code = None
        
        for sec in sections:
            sec = sec.strip()
            if not sec:
                continue

            lines = sec.split("\n")
            section_title = lines[0].strip()
            sec_text = "\n".join(lines[1:]).strip()

            # Error code extraction
            err_match = re.search(r"^ERROR CODE:\s*(.+)$", sec_text, re.MULTILINE)
            if err_match:
                raw_code = err_match.group(1).strip()
                current_error_code = raw_code.replace("-", "") if not raw_code.startswith("SYM-") else raw_code
            else:
                # Regex fallback for error codes in section title e.g. E101, H205, R101, or SYM-...
                title_err_match = re.search(r"\b([A-Z]-?\d{3,4}|SYM-[A-Z0-9-]+)\b", section_title)
                if title_err_match:
                    raw_tc = title_err_match.group(1).strip()
                    current_error_code = raw_tc.replace("-", "") if not raw_tc.startswith("SYM-") else raw_tc

            # Machine / Model
            sec_machine = global_machine
            chunk_m_match = re.search(r"^MACHINE:\s*(.+)$", sec_text, re.MULTILINE)
            if chunk_m_match:
                sec_machine = chunk_m_match.group(1).strip()

            sec_model = global_model
            chunk_mod_match = re.search(r"^MODEL:\s*(.+)$", sec_text, re.MULTILINE)
            if chunk_mod_match:
                sec_model = chunk_mod_match.group(1).strip()

            page_match = re.search(r"^PAGE:\s*(.+)$", sec_text, re.MULTILINE)
            page_num = page_match.group(1).strip() if page_match else None

            # Ensure error code and machine context are present in text for high-fidelity retrieval
            chunk_text = sec_text
            if current_error_code and f"ERROR CODE: {current_error_code}" not in chunk_text:
                chunk_text = f"ERROR CODE: {current_error_code}\n" + chunk_text

            # Authoritative chunk-level diagram resolution
            diag_info = resolve_diagram_for_section(
                machine=sec_machine or "Unknown",
                model=sec_model or "Unknown",
                error_code=current_error_code,
                section_title=section_title,
                text=sec_text
            )

            chunks.append({
                "text": chunk_text,
                "machine": sec_machine or "Unknown",
                "model": sec_model or "Unknown",
                "manual": filename,
                "section": section_title,
                "page": page_num,
                "error_code": current_error_code,
                "diagram_url": diag_info["url"] if diag_info else None,
                "diagram_title": diag_info["title"] if diag_info else None,
                "diagram_caption": diag_info["caption"] if diag_info else None
            })

    return chunks

if __name__ == "__main__":
    parsed_chunks = load_and_chunk_manuals()
    print(f"Total chunks parsed: {len(parsed_chunks)}")
    for i, c in enumerate(parsed_chunks[:5]):
        print(f"--- Chunk {i+1} ---")
        print(f"Machine: {c['machine']} | Model: {c['model']} | Manual: {c['manual']}")
        print(f"Section: {c['section']} | Page: {c['page']} | Error Code: {c['error_code']}")
        print(f"Text Preview:\n{c['text'][:140]}...\n")
