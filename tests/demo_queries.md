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
- **Prompt:** `"How do I fix error E101 on the CB-4400 conveyor belt?"`
- **Target Machine:** Conveyor Belt System — Model CB-4400
- **Target Citation:** `Conveyor Belt System — Model CB-4400 Troubleshooting Manual, Section 2: Error Codes, [Page 2]`
- **Expected Output:**
  - Identifies E101 as Drive Motor Overcurrent Fault (VFD current draw > 125% FLA for > 3.5s).
  - Probable causes: excessive belt tension, jammed idler roller, debris under belt.
  - Steps: LOTO panel CP-1, check belt deflection tension (25 mm under 15 kg load), inspect rollers for stiff rotation/bearing play, inspect VFD parameter P-042.

#### Query 1.2: CNC MX-7 Spindle Coolant Flow Failure
- **Prompt:** `"What does error E101 mean on the CNC Milling Machine MX-7 Precision?"`
- **Target Machine:** CNC Milling Machine — Model MX-7 Precision
- **Target Citation:** `CNC Milling Machine — Model MX-7 Precision Troubleshooting Manual, Section 2: Error Codes, [Page 2]`
- **Expected Output:**
  - Identifies E101 as Spindle Coolant Flow Failure (flow sensor FL-10 < 3.8 L/min).
  - Probable causes: clogged 25-micron inline coolant filter cartridge, pump failure/cavitation, low reservoir level.
  - Steps: Check coolant sight gauge (8% emulsion), inspect filter differential pop-up indicator, replace 25-micron cartridge (Part No. MX-FLT-025), check line pressure (45–70 bar).

#### Query 1.3: Hydraulic Press HP-2200 High Fluid Temperature
- **Prompt:** `"What is the corrective action for fault H205 on the HP-2200 hydraulic press?"`
- **Target Machine:** Hydraulic Press — Model HP-2200
- **Target Citation:** `Hydraulic Press — Model HP-2200 Troubleshooting Manual, Section 2: Error Codes, [Page 2]`
- **Expected Output:**
  - Identifies H205 as Hydraulic Oil High Temperature Shutdown (reservoir transmitter TT-02 > 65°C).
  - Probable causes: heat exchanger fouling, cooling water supply < 60 L/min, relief valve bypass.
  - Steps: Run auxiliary pump in low-pressure idle mode, verify cooling water pressure (min 3.5 bar, < 22°C), clean duplex basket strainer, FLIR thermal scan.

### 2. Natural-Language Symptom Queries (Semantic Vector Search)

#### Query 2.1: Conveyor Overheating
- **Prompt:** `"Why is the conveyor overheating?"`
- **Target Machine:** Conveyor Belt System — Model CB-4400
- **Target Citation:** `Conveyor Belt System — Model CB-4400 Troubleshooting Manual, Section 2: Error Codes, [Page 4]`
- **Expected Output:**
  - Matches high drive gearbox oil temperature (E401 > 92°C).
  - Details oil cooldown to 40°C, checking sight glass, replacing viton seals, refilling Mobilgear SHC 320.

#### Query 2.2: Conveyor Startup Squeal
- **Prompt:** `"The conveyor belt is squealing and chirping during morning startup."`
- **Target Machine:** Conveyor Belt System — Model CB-4400
- **Target Citation:** `Conveyor Belt System — Model CB-4400 Troubleshooting Manual, Section 3: Common Symptoms, [Page 5]`
- **Expected Output:**
  - Matches symptom: Squealing or Chirping Sound During Startup.
  - Causes: glazed lagging on drive drum, loose tension, dry snub roller bearings.
  - Steps: Tighten take-up screws by 2 full turns, scuff glazed lagging with 40-grit emery cloth, grease snub bearings.

#### Query 2.3: CNC Surface Chatter Marks
- **Prompt:** `"Our CNC milled parts show high-pitched chatter marks along the finished vertical surfaces."`
- **Target Machine:** CNC Milling Machine — Model MX-7 Precision
- **Target Citation:** `CNC Milling Machine — Model MX-7 Precision Troubleshooting Manual, Section 3: Common Symptoms, [Page 5]`
- **Expected Output:**
  - Matches symptom: High-Pitched Chatter Marks on Finished Milled Surfaces.
  - Causes: excessive tool stickout, worn ceramic bearings, low vise clamping pressure.
  - Steps: Limit tool stickout to max 3:1 ratio, check vise pressure (25 bar), test spindle runout (under 0.003 mm TIR), adjust RPM by +/- 12%.

#### Query 2.4: Hydraulic Pump Cavitation Whine
- **Prompt:** `"The hydraulic press main pump is making a loud cavitation whining sound."`
- **Target Machine:** Hydraulic Press — Model HP-2200
- **Target Citation:** `Hydraulic Press — Model HP-2200 Troubleshooting Manual, Section 3: Common Symptoms, [Page 6]`
- **Expected Output:**
  - Matches symptom: Hydraulic Pump Emitting Loud Cavitation Whine.
  - Causes: restricted suction line from silted strainer, cold oil (< 20°C), air entering pump shaft seal.
  - Steps: Verify oil temp is at least 32°C, verify suction valve is 100% open, clean 100-mesh suction wire cloth strainer, inspect shaft seal.

### 3. Ambiguous Queries (The E101 Ambiguity Trap)

#### Query 3.1: Ambiguous Code E101
- **Prompt:** `"E101"`
- **Target Machine:** Ambiguous (Matches CB-4400 and MX-7)
- **Expected Output:**
  - `ambiguous: true`
  - System prompts user to clarify between Conveyor Belt CB-4400 (Motor Overcurrent) and CNC Milling Machine MX-7 Precision (Coolant Flow Loss).

#### Query 3.2: Meaning of E101
- **Prompt:** `"What does error E101 mean?"`
- **Target Machine:** Ambiguous
- **Expected Output:**
  - Flags query as ambiguous and requests equipment context before detailing causes or fixes.

#### Query 3.3: How to Fix E101
- **Prompt:** `"How do I fix error E101?"`
- **Target Machine:** Ambiguous
- **Expected Output:**
  - Refuses to output repair steps immediately, preventing cross-machine incorrect instructions.

### 4. Undocumented Gap Queries (Hallucination Control & Insufficient Info)

#### Query 4.1: Status LED Flash Pattern
- **Prompt:** `"The status LED is flashing 3 short blinks followed by a long pause, what does this pattern mean?"`
- **Target Machine:** Unspecified or Any
- **Target Citation:** None (Undocumented Gap)
- **Expected Output:**
  - `insufficient_info: true` (or low relevance refusal).
  - Honestly states status LED blink patterns are not documented in the manuals. Zero hallucinations.

#### Query 4.2: CNC Status LED Flickering
- **Prompt:** `"What causes the intermittent flickering pattern on the CNC MX-7 status LED?"`
- **Target Machine:** CNC Milling Machine — Model MX-7 Precision
- **Target Citation:** None (Undocumented Gap)
- **Expected Output:**
  - Acknowledges MX-7 model, but states LED blink/flicker patterns are not documented in the MX-7 manual.

#### Query 4.3: Hydraulic Press Status LED
- **Prompt:** `"The hydraulic press HP-2200 status LED is blinking 3 times in a row. How do I clear it?"`
- **Target Machine:** Hydraulic Press — Model HP-2200
- **Target Citation:** None (Undocumented Gap)
- **Expected Output:**
  - States that HP-2200 manual covers codes H201–H622 on the HMI screen, but contains no LED blink documentation.

---

## Running Test Log (Reusable Test Matrix)

### Test Run Date: _________________ | Tested By: _________________ | Environment: [ ] CLI / [ ] FastAPI / [ ] React UI

| # | Query Tested | Category | Expected Outcome | Actual Output & Citation | Pass / Fail | Notes / Discrepancies |
|---|---|---|---|---|---|---|
| 1 | `"What does E101 mean on CNC-100?"` | Core: Exact Code | CNC-100 Motor overheating | | [ ] Pass<br>[ ] Fail | |
| 2 | `"Why is my Press-200 machine stopping due to oil pressure?"` | Core: Symptom | Press-200 Low hydraulic pressure | | [ ] Pass<br>[ ] Fail | |
| 3 | `"What does error code E101 mean?"` | Core: Ambiguous | Disambiguate: CNC-100 vs Press-200 | | [ ] Pass<br>[ ] Fail | |
| 4 | `"How do I replace the spindle bearing on CNC-100?"` | Core: Undocumented | Refusal without hallucination | | [ ] Pass<br>[ ] Fail | |
| 5 | `"How do I fix error E101 on the CB-4400 conveyor belt?"` | Ext: Exact Code | CB-4400 Overcurrent, Page 2 | | [ ] Pass<br>[ ] Fail | |
| 6 | `"What does error E101 mean on the CNC Milling Machine MX-7 Precision?"` | Ext: Exact Code | MX-7 Coolant Loss, Page 2 | | [ ] Pass<br>[ ] Fail | |
| 7 | `"What is the corrective action for fault H205 on the HP-2200 hydraulic press?"` | Ext: Exact Code | HP-2200 High Temp, Page 2 | | [ ] Pass<br>[ ] Fail | |
| 8 | `"Why is the conveyor overheating?"` | Ext: Symptom | Gearbox temp E401 / Page 4 | | [ ] Pass<br>[ ] Fail | |
| 9 | `"The conveyor belt is squealing and chirping during morning startup."` | Ext: Symptom | Lagging / tension, Page 5 | | [ ] Pass<br>[ ] Fail | |
| 10 | `"Our CNC milled parts show high-pitched chatter marks along the finished vertical surfaces."` | Ext: Symptom | Tool stickout / runout, Page 5 | | [ ] Pass<br>[ ] Fail | |
| 11 | `"The hydraulic press main pump is making a loud cavitation whining sound."` | Ext: Symptom | Suction strainer / cold oil, Page 6 | | [ ] Pass<br>[ ] Fail | |
| 12 | `"E101"` | Ext: Ambiguous | Disambiguate: CB-4400 vs MX-7 | | [ ] Pass<br>[ ] Fail | |
| 13 | `"The status LED is flashing 3 short blinks followed by a long pause, what does this pattern mean?"` | Ext: Undocumented | Honest refusal (not in manuals) | | [ ] Pass<br>[ ] Fail | |
