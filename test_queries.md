# Test Queries for MachineAssist RAG Evaluation

This document outlines benchmark test queries designed to evaluate the 4 critical capabilities of the MachineAssist industrial RAG troubleshooting pipeline against the three authored manuals:
- **Manual 1:** Conveyor Belt System — Model CB-4400 (`manual_1_conveyor_belt.md`)
- **Manual 2:** CNC Milling Machine — Model MX-7 Precision (`manual_2_cnc_milling.md`)
- **Manual 3:** Hydraulic Press — Model HP-2200 (`manual_3_hydraulic_press.md`)

---

## 1. Exact-Code Queries (Targeted Retrieval & Citation)

In this demo case, the technician provides a specific machine identifier and an explicit error code. The system must retrieve the exact error code subsection and output authoritative corrective actions with precise manual, section, and page citations.

### Query 1.1
- **Prompt:** `"How do I fix error E101 on the CB-4400 conveyor belt?"`
- **Target Machine:** Conveyor Belt System — Model CB-4400
- **Target Citation:** `Conveyor Belt System — Model CB-4400 Troubleshooting Manual, Section 2: Error Codes, [Page 2]`
- **Expected Behavior:** 
  - Identifies `E101` as **Drive Motor Overcurrent Fault**.
  - Identifies causes: excessive belt tension, jammed carrying or return idler roller, debris under belt.
  - Steps: LOTO panel CP-1, check belt deflection tension (25 mm under 15 kg load), inspect rollers for stiff rotation/bearing play, inspect VFD parameter P-042.
  - Must **not** mention coolant, filters, or pumps.

### Query 1.2
- **Prompt:** `"What is causing error E101 on the CNC Milling Machine MX-7 Precision?"`
- **Target Machine:** CNC Milling Machine — Model MX-7 Precision
- **Target Citation:** `CNC Milling Machine — Model MX-7 Precision Troubleshooting Manual, Section 2: Error Codes, [Page 2]`
- **Expected Behavior:** 
  - Identifies `E101` as **Spindle Coolant Flow Failure** (flow sensor FL-10 < 3.8 L/min).
  - Identifies causes: clogged 25-micron inline coolant filter cartridge, pump failure/cavitation, low reservoir level.
  - Steps: Check coolant sight gauge (8% emulsion), inspect filter differential pop-up indicator, replace 25-micron cartridge (Part No. MX-FLT-025), check line pressure (45–70 bar).
  - Must **not** mention conveyor belt tension, idler rollers, or motor overcurrent.

### Query 1.3
- **Prompt:** `"The hydraulic press HP-2200 is throwing fault code H312. What should I do?"`
- **Target Machine:** Hydraulic Press — Model HP-2200
- **Target Citation:** `Hydraulic Press — Model HP-2200 Troubleshooting Manual, Section 2: Error Codes, [Page 3]`
- **Expected Behavior:** 
  - Identifies `H312` as **Nitrogen Accumulator Pre-Charge Pressure Low** (switch AP-03 < 110 bar).
  - Steps: Lower platen to BDC, dump pressure to 0 bar, inspect Schrader gas valve for oil (indicating ruptured bladder kit Part No. HP-ACC-B50), recharge dry industrial nitrogen (99.99%) to 130 bar pre-charge at 20°C.

---

## 2. Natural-Language Symptom Queries (Semantic / Concept Matching)

In this demo case, the technician does not know or provide an error code. They describe an acoustic, physical, or visual symptom in natural language. The system must perform semantic vector retrieval to match the descriptive text in Section 3 of the relevant manual.

### Query 2.1
- **Prompt:** `"The conveyor belt is making a loud squealing and chirping noise whenever we start it up in the morning."`
- **Target Machine:** Conveyor Belt System — Model CB-4400
- **Target Citation:** `Conveyor Belt System — Model CB-4400 Troubleshooting Manual, Section 3: Common Symptoms, [Page 5]`
- **Expected Behavior:** 
  - Matches symptom: **Squealing or Chirping Sound During Startup**.
  - Explains cause: glazed or worn rubber lagging on the drive drum, insufficient tension allowing initial slippage, dry snub roller bearings.
  - Corrective action: Tighten tail pulley take-up screws by 2 full turns, scuff glazed lagging with 40-grit emery cloth, apply grip conditioning spray, grease snub roller bearings with NLGI Grade 2 lithium grease.

### Query 2.2
- **Prompt:** `"Our CNC milled parts are coming out with severe high-pitched chatter marks along the finished vertical surfaces."`
- **Target Machine:** CNC Milling Machine — Model MX-7 Precision
- **Target Citation:** `CNC Milling Machine — Model MX-7 Precision Troubleshooting Manual, Section 3: Common Symptoms, [Page 5]`
- **Expected Behavior:** 
  - Matches symptom: **High-Pitched Chatter Marks on Finished Milled Surfaces**.
  - Explains cause: excessive tool stickout/overhang, worn ceramic spindle bearings, low vise clamping pressure, harmonic resonance.
  - Corrective action: Limit tool stickout to max 3:1 length-to-diameter ratio, check hydraulic vise pressure (25 bar), measure spindle runout (must not exceed 0.003 mm TIR), adjust spindle speed by +/- 12% to exit resonant frequency pocket.

### Query 2.3
- **Prompt:** `"The hydraulic press main pump is emitting a loud cavitation whine during operation."`
- **Target Machine:** Hydraulic Press — Model HP-2200
- **Target Citation:** `Hydraulic Press — Model HP-2200 Troubleshooting Manual, Section 3: Common Symptoms, [Page 6]`
- **Expected Behavior:** 
  - Matches symptom: **Hydraulic Pump Emitting Loud Cavitation Whine**.
  - Explains cause: restricted pump suction line from silted strainer, high oil viscosity due to cold oil, or air ingress via pump shaft seal.
  - Corrective action: Verify oil temp is at least 32°C (enable immersion heaters if below 20°C), ensure suction butterfly valve is 100% open, remove and clean 100-mesh suction wire cloth strainer in mineral spirits, inspect shaft lip seal for air hissing.

---

## 3. Ambiguous Queries — The E101 Ambiguity Trap (Disambiguation)

In this demo case, the technician asks about `E101` without specifying the machine. Because `E101` exists in both Manual 1 (Conveyor) and Manual 2 (CNC) with completely contradictory repairs (mechanical belt tension vs. spindle coolant system), answering directly would risk giving dangerous, incorrect repair instructions. The system must detect this ambiguity and ask for clarification.

### Query 3.1
- **Prompt:** `"The machine stopped and is showing error code E101. How do I fix it?"`
- **Target Machine:** Ambiguous (Matches both Model CB-4400 and Model MX-7 Precision)
- **Target Citation:** None (Ambiguity Resolution Required)
- **Expected Behavior:** 
  - System flags query as ambiguous (`ambiguous: true`).
  - System refuses to output repair steps immediately.
  - Prompts technician to clarify: *"Error code E101 corresponds to two different machines: (1) Conveyor Belt System CB-4400 (Drive Motor Overcurrent Fault) or (2) CNC Milling Machine MX-7 Precision (Spindle Coolant Flow Failure). Which machine are you troubleshooting?"*

### Query 3.2
- **Prompt:** `"What is the meaning and probable causes of code E101?"`
- **Target Machine:** Ambiguous (Matches both Model CB-4400 and Model MX-7 Precision)
- **Target Citation:** None (Ambiguity Resolution Required)
- **Expected Behavior:** 
  - System detects multiple conflicting definitions across indexed manuals.
  - Returns options or a disambiguation prompt explicitly distinguishing:
    - **CB-4400:** Overcurrent caused by belt tension, jammed rollers, or debris.
    - **MX-7 Precision:** Coolant flow loss caused by clogged filters, pump failure, or low coolant level.

### Query 3.3
- **Prompt:** `"I have an active E101 fault on my line. Please give me the step-by-step troubleshooting checklist."`
- **Target Machine:** Ambiguous
- **Target Citation:** None (Ambiguity Resolution Required)
- **Expected Behavior:** 
  - System recognizes that executing CNC coolant pump procedures on a jammed conveyor belt (or vice versa) is invalid.
  - Holds execution and requests the equipment model name or ID before providing corrective actions.

---

## 4. Undocumented Gap Queries (Hallucination Control & Insufficient Info)

In this demo case, the technician queries about an intermittent status LED flickering/blinking pattern (e.g., 3 short blinks followed by a pause). None of the three manuals document status LED blink codes. The system must recognize that the retrieved manual chunks do not support an answer, and refuse to hallucinate an explanation.

### Query 4.1
- **Prompt:** `"The machine status LED is flashing 3 short blinks followed by a long pause, repeating continuously. What does this blink pattern mean?"`
- **Target Machine:** Unspecified or Any
- **Target Citation:** None (Undocumented Gap)
- **Expected Behavior:** 
  - System searches the vector database and finds no matching documentation or low relevance score below confidence threshold.
  - System responds honestly: *"The provided troubleshooting manuals do not contain information regarding status LED blink patterns or flash sequences. Please refer to the machine controller HMI diagnostic screen or contact the manufacturer's technical support."*
  - Must **not** invent a fake blink code chart or claim it means motor fault/coolant fault.

### Query 4.2
- **Prompt:** `"What does an intermittent flickering pattern on the CNC Milling Machine MX-7 status LED indicate?"`
- **Target Machine:** CNC Milling Machine — Model MX-7 Precision
- **Target Citation:** None (Undocumented Gap)
- **Expected Behavior:** 
  - Even though the CNC machine model is explicitly recognized, the system determines that LED flickering patterns are absent from `manual_2_cnc_milling.md`.
  - System acknowledges the machine model but states that LED blink patterns are not documented in the MX-7 manual.
  - Directs technician to check documented alphanumeric error codes (E101–E520) on the CNC operator pendant instead.

### Query 4.3
- **Prompt:** `"How do I interpret a recurring 3-blink pulse on the hydraulic press HP-2200 status LED?"`
- **Target Machine:** Hydraulic Press — Model HP-2200
- **Target Citation:** None (Undocumented Gap)
- **Expected Behavior:** 
  - System confirms that `manual_3_hydraulic_press.md` documents digital transducer and HMI error codes (H201–H622), but does **not** contain LED pulse diagnostic tables.
  - Refuses to hallucinate hydraulic failure modes tied to LED pulses.
