import re
from typing import List, Dict, Any, Tuple, Optional

KNOWN_FAULTS_CATALOG = {
    ("cnc milling machine", "e101"): {
        "name": "Spindle Coolant Flow Failure",
        "component": "Through-Spindle Coolant (TSC) Unit & FL-10 Sensor",
        "circuit": "Coolant Delivery & Safety Interlock Circuit"
    },
    ("cnc milling machine", "e108"): {
        "name": "Spindle Motor Stator Overtemperature",
        "component": "Electro-Spindle Stator Winding",
        "circuit": "Spindle Thermal Protection Circuit"
    },
    ("cnc milling machine", "e202"): {
        "name": "Axis Servo Following Error",
        "component": "Axis AC Servo Drive & Optical Scale",
        "circuit": "Position Feedback & Servo Drive Loop"
    },
    ("cnc milling machine", "e310"): {
        "name": "Automatic Tool Changer Arm Jam",
        "component": "ATC 40-Station Arm & Pneumatic Gripper",
        "circuit": "ATC Pneumatic Solenoid & Interlock Sensor"
    },
    ("cnc milling machine", "e415"): {
        "name": "Centralized Way Lubrication Pressure Loss",
        "component": "Automated Slideway Lubrication Pump",
        "circuit": "Lubrication Pressure Sensor & Manifold"
    },
    ("cnc milling machine", "e520"): {
        "name": "Operator Enclosure Safety Interlock Open",
        "component": "Safety Enclosure Interlock Door & RFID Sensor",
        "circuit": "Safety Gate Dual-Channel Interlock Loop"
    },
    ("conveyor belt system", "e101"): {
        "name": "Drive Motor Overcurrent Fault",
        "component": "VFD Inverter Drive & Head Pulley Drum",
        "circuit": "VFD Motor Inverter & Thermal Overload Loop"
    },
    ("conveyor belt system", "e102"): {
        "name": "Belt Tracking Misalignment Drift",
        "component": "Tracking Limit Switches & Tail Pulley Tensioner",
        "circuit": "Lateral Edge Limit Switch Circuit (LS-10A/B)"
    },
    ("conveyor belt system", "e204"): {
        "name": "Emergency Stop Circuit Loop Open",
        "component": "Dual-Channel E-Stop Relay & Perimeter Pull-Cord",
        "circuit": "Perimeter Emergency Safety Relay SR-1 Circuit"
    },
    ("conveyor belt system", "e305"): {
        "name": "Tachometer Speed Discrepancy Error",
        "component": "Digital Optical Rotary Tachometer Sensor",
        "circuit": "Speed Feedback Pulse Encoder Circuit"
    },
    ("conveyor belt system", "e401"): {
        "name": "High Drive Gearbox Oil Temperature",
        "component": "Helical-Bevel Gearbox Sump & PT100 RTD Probe",
        "circuit": "Oil Sump Thermal RTD Sensor Circuit"
    },
    ("conveyor belt system", "e502"): {
        "name": "Photoelectric Infeed Jam Sensor Timeout",
        "component": "Retro-Reflective Optical Photo-Eye PE-01",
        "circuit": "Optical Transceiver PE-01 Detection Circuit"
    },
    ("hydraulic press", "h201"): {
        "name": "Main Ram Proportional Pressure Loss",
        "component": "Proportional Relief Valve & Pressure Sensor PT-01",
        "circuit": "High-Pressure Hydraulic Proportional Valve Circuit"
    },
    ("hydraulic press", "h205"): {
        "name": "Hydraulic Oil High Temperature Shutdown",
        "component": "Shell-and-Tube Heat Exchanger & Reservoir TT-02",
        "circuit": "Fluid Temperature Transducer TT-02 Protective Loop"
    },
    ("hydraulic press", "h312"): {
        "name": "High-Pressure Duplex Filter Differential Clog",
        "component": "Duplex Basket Strainer & Delta-P Indicator",
        "circuit": "Duplex Filter Differential Pressure Sensor Circuit"
    },
    ("hydraulic press", "h420"): {
        "name": "Main Cylinder Piston Seal Internal Leakage",
        "component": "Main Ram Cylinder Piston Packing Seals",
        "circuit": "Tonnage Holding Pressure Monitoring Circuit"
    },
    ("hydraulic press", "h515"): {
        "name": "Hydraulic Prefill Valve Poppet Jam",
        "component": "Pilot Prefill Check Poppet & Pilot Valve",
        "circuit": "Prefill Valve Pilot Actuation Circuit"
    },
    ("hydraulic press", "h622"): {
        "name": "Safety Light Curtain Optical Barrier Interruption",
        "component": "Optical Safety Light Curtain Pillars (TX/RX)",
        "circuit": "Dual-Channel Safety Relay SR-2 Optical Loop"
    },
    ("cnc-100", "e101"): {
        "name": "Spindle Motor Overtemperature",
        "component": "Spindle Motor Cooling & Fan Assembly",
        "circuit": "Motor Thermal Switch & Ventilation Circuit"
    },
    ("cnc-100", "e102"): {
        "name": "Spindle Axis Overload",
        "component": "Spindle Drive & Cutting Tool",
        "circuit": "Spindle Drive Current Monitoring Circuit"
    },
    ("cnc-100", "e103"): {
        "name": "Coolant Low Pressure Fault",
        "component": "Coolant Pump & Intake Filter",
        "circuit": "Coolant Pressure Switch Circuit"
    },
    ("press-200", "e101"): {
        "name": "Hydraulic Oil Low Pressure Shutdown",
        "component": "Main Hydraulic Pump & Pressure Line",
        "circuit": "Low Pressure Interlock Switch Circuit"
    },
    ("press-200", "e202"): {
        "name": "Main Ram Position Drift",
        "component": "Hydraulic Ram Cylinder & Linear Scale",
        "circuit": "Linear Position Transducer Circuit"
    },
    ("press-200", "e203"): {
        "name": "Hydraulic Fluid High Temperature",
        "component": "Reservoir Oil Cooling System",
        "circuit": "Thermal Overheat Cutout Circuit"
    },
    ("robotarm-300", "r101"): {
        "name": "Joint 3 Rotational Deviation Error",
        "component": "Harmonic Drive Gearbox & Joint 3 Encoder",
        "circuit": "Joint 3 Optical Position Encoder Feedback Loop"
    }
}

SYMPTOM_CATALOG = {
    "sym-squeal-startup": ("Drive Belt Slippage & Lagging Wear", "Drive Drum Rubber Lagging & Tail Pulley"),
    "sym-belt-jerking": ("Conveyor Belt Jerking & Spider Cushion Wear", "Flexible Shaft Jaw Coupling & Bed Rollers"),
    "sym-rail-vibration": ("Side Rail Vibration & Roller Eccentricity", "Floor Anchor Studs & Carrying Idler Rollers"),
    "sym-edge-fraying": ("Belt Edge Fraying & Skirtboard Rubbing", "Polyurethane Infeed Skirtboard Sealing Strips"),
    "sym-chatter-marks": ("Machining Chatter Marks & Spindle Runout", "Spindle Bearings & Tool Clamping Vise"),
    "sym-spindle-whining": ("Spindle Bearing Wear & Whining Vibration", "Hybrid Ceramic Spindle Bearing Pack"),
    "sym-bore-accuracy": ("Bore Dimension Drift & Ballscrew Backlash", "Ballscrew Thrust Bearings & Axis Scale"),
    "sym-mist-leakage": ("Coolant Mist Collector Saturation & Seal Leakage", "Electrostatic Mist Collector & Door Gasket"),
    "sym-hydraulic-hammer": ("Hydraulic Shock Hammer & Decompression Jolt", "Digital Proportional Decompression Poppet"),
    "sym-ram-jerking": ("Ram Cylinder Stutter & Trapped Air Entrainment", "Cylinder Air Bleed Petcocks & Tie-Rod Bushings"),
    "sym-pump-cavitation": ("Main Hydraulic Pump Suction Cavitation", "Axial Piston Pump & 100-Mesh Suction Strainer"),
    "sym-tonnage-hold": ("Tonnage Loss Drift & Cartridge Valve Leakage", "Tonnage Manifold Pilot Check Valve Cartridge")
}

print("Catalog loaded successfully")
