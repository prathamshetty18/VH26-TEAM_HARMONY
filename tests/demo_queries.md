# Demo Queries & Expected Behaviors

## Core Benchmark Suite (CNC-100 & Press-200)

### Demo 1: Exact Error Code
- **Query:** "What does E101 mean on CNC-100?"
- **Expected Result:** Machine-specific troubleshooting answer for CNC-100's E101 (Motor overheating).

### Demo 2: Natural Language Symptom
- **Query:** "Why is my Press-200 machine stopping due to oil pressure?"
- **Expected Result:** Semantic retrieval identifies Press-200 E101 (Low hydraulic pressure) and returns troubleshooting steps.

### Demo 3: Cross-Manual Ambiguity
- **Query:** "What does error code E101 mean?"
- **Expected Result:** System identifies E101 in multiple manuals (CNC-100 and Press-200) and asks for clarification (`ambiguous: true`).

### Demo 4: Insufficient Information
- **Query:** "How do I replace the spindle bearing on CNC-100?"
- **Expected Result:** System recognizes that this topic is not covered in the manuals and refuses to answer without hallucinating.

---

## Extended Industrial Machine Benchmark Suite (CB-4400, MX-7 Precision, HP-2200)

### 1. Exact-Code Queries (Targeted Retrieval & Citation)

#### Query 1.1: Conveyor Belt CB-4400 Motor Overcurrent
- **Prompt:** "How do I fix error E101 on the CB-4400 conveyor belt?"
- **Target Machine:** Conveyor Belt System — Model CB-4400
- **Target Citation:** Conveyor Belt System — Model CB-4400 Troubleshooting Manual, Section 2: Error Codes, [Page 2]
- **Expected Output:**
  - Identifies E101 as Drive Motor Overcurrent Fault.
  - Causes: excessive belt tension, jammed idler roller, debris under belt.
  - Steps: LOTO CP-1, check belt deflection tension (25 mm under 15 kg load), inspect rollers for stiff rotation/bearing play, inspect VFD parameter P-042.

#### Query 1.2: CNC MX-7 Spindle Coolant Flow Failure
- **Prompt:** "What is causing error E101 on the CNC Milling Machine MX-7 Precision?"
- **Target Machine:** CNC Milling Machine — Model MX-7 Precision
- **Target Citation:** CNC Milling Machine — Model MX-7 Precision Troubleshooting Manual, Section 2: Error Codes, [Page 2]
- **Expected Output:**
  - Identifies E101 as Spindle Coolant Flow Failure (flow sensor FL-10 < 3.8 L/min).
  - Causes: clogged 25-micron inline coolant filter cartridge, pump failure/cavitation, low reservoir level.
  - Steps: Check coolant sight gauge (8% emulsion), inspect filter differential pop-up indicator, replace 25-micron cartridge (Part No. MX-FLT-025), check line pressure (45–70 bar).

#### Query 1.3: Hydraulic Press HP-2200 Accumulator Pressure Low
- **Prompt:** "The hydraulic press HP-2200 is throwing fault code H312. What should I do?"
- **Target Machine:** Hydraulic Press — Model HP-2200
- **Target Citation:** Hydraulic Press — Model HP-2200 Troubleshooting Manual, Section 2: Error Codes, [Page 3]
- **Expected Output:**
  - Identifies H312 as Nitrogen Accumulator Pre-Charge Pressure Low (switch AP-03 < 110 bar).
  - Steps: Lower platen to BDC, dump pressure to 0 bar, inspect Schrader gas valve for oil (indicating ruptured bladder kit Part No. HP-ACC-B50), recharge dry industrial nitrogen (99.99%) to 130 bar pre-charge at 20°C.

### 2. Natural-Language Symptom Queries (Semantic Vector Search)

#### Query 2.1: Conveyor Startup Squeal
- **Prompt:** "The conveyor belt is making a loud squealing and chirping noise whenever we start it up in the morning."
- **Target Machine:** Conveyor Belt System — Model CB-4400
- **Target Citation:** Conveyor Belt System — Model CB-4400 Troubleshooting Manual, Section 3: Common Symptoms, [Page 5]
- **Expected Output:**
  - Matches symptom: Squealing or Chirping Sound During Startup.
  - Explains cause: glazed/worn rubber lagging on drive drum, loose tension, dry snub roller bearings.
  - Corrective action: Tighten tail pulley take-up screws by 2 full turns, scuff glazed lagging with 40-grit emery cloth, apply grip conditioning spray, grease snub roller bearings.

#### Query 2.2: CNC Surface Chatter Marks
- **Prompt:** "Our CNC milled parts are coming out with severe high-pitched chatter marks along the finished vertical surfaces."
- **Target Machine:** CNC Milling Machine — Model MX-7 Precision
- **Target Citation:** CNC Milling Machine — Model MX-7 Precision Troubleshooting Manual, Section 3: Common Symptoms, [Page 5]
- **Expected Output:**
  - Matches symptom: High-Pitched Chatter Marks on Finished Milled Surfaces.
  - Explains cause: excessive tool stickout, worn ceramic bearings, low vise clamping pressure, harmonic resonance.
  - Corrective action: Limit tool overhang to max 3:1 ratio, check vise pressure (25 bar), test spindle runout (under 0.003 mm TIR), adjust RPM by +/- 12%.

#### Query 2.3: Hydraulic Pump Cavitation Whine
- **Prompt:** "The hydraulic press main pump is emitting a loud cavitation whine during operation."
- **Target Machine:** Hydraulic Press — Model HP-2200
- **Target Citation:** Hydraulic Press — Model HP-2200 Troubleshooting Manual, Section 3: Common Symptoms, [Page 6]
- **Expected Output:**
  - Matches symptom: Hydraulic Pump Emitting Loud Cavitation Whine.
  - Explains cause: restricted pump suction line from silted strainer, cold oil (< 20°C), air ingress via pump shaft seal.
  - Corrective action: Verify oil temp is at least 32°C, verify suction butterfly valve is 100% open, clean 100-mesh suction wire cloth strainer in mineral spirits, inspect shaft lip seal.

### 3. Ambiguous Queries (The E101 Ambiguity Trap)

#### Query 3.1: Ambiguous Code E101
- **Prompt:** "The machine stopped and is showing error code E101. How do I fix it?"
- **Target Machine:** Ambiguous (Matches CB-4400 and MX-7)
- **Expected Output:**
  - System flags query as ambiguous (`ambiguous: true`).
  - Refuses to output repair steps immediately.
  - Prompts technician to clarify between CB-4400 (Drive Motor Overcurrent) and MX-7 Precision (Spindle Coolant Flow Failure).

#### Query 3.2: Meaning of E101
- **Prompt:** "What is the meaning and probable causes of code E101?"
- **Target Machine:** Ambiguous
- **Expected Output:**
  - Detects conflicting definitions across indexed manuals.
  - Returns options or a disambiguation prompt distinguishing conveyor overcurrent vs. CNC coolant flow failure.

### 4. Undocumented Gap Queries (Hallucination Control & Insufficient Info)

#### Query 4.1: Status LED Flash Pattern
- **Prompt:** "The machine status LED is flashing 3 short blinks followed by a long pause, repeating continuously. What does this blink pattern mean?"
- **Target Machine:** Unspecified or Any
- **Target Citation:** None (Undocumented Gap)
- **Expected Output:**
  - System checks manuals, finds no documentation on status LED blink patterns, and honestly refuses: "The provided troubleshooting manuals do not contain information regarding status LED blink patterns or flash sequences."
  - Does not invent or hallucinate a diagnosis.

#### Query 4.2: CNC Status LED Flickering
- **Prompt:** "What does an intermittent flickering pattern on the CNC Milling Machine MX-7 status LED indicate?"
- **Target Machine:** CNC Milling Machine — Model MX-7 Precision
- **Target Citation:** None (Undocumented Gap)
- **Expected Output:**
  - System acknowledges the machine model but states that LED blink patterns are not documented in the MX-7 manual.
  - Directs technician to check documented alphanumeric error codes (E101–E520) on the CNC operator pendant instead.
