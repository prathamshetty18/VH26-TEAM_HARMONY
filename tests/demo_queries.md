# MachineAssist — Demo Queries & Evaluation Suite

## Part 1: Quick Core Demo Queries
These 5 core test cases correspond directly to `tests/test_all_demos.py` for rapid end-to-end smoke testing.

### Demo 1: Exact Error Code (Machine-Specified)
- **Query:** `"What does E101 mean on CNC-100?"`
- **Expected Result:** Machine-specific troubleshooting answer for CNC-100's E101 (Motor overheating) with manual citations.

### Demo 2: Natural Language Symptom
- **Query:** `"Why is my Press-200 machine stopping due to oil pressure?"`
- **Expected Result:** Semantic retrieval identifies Press-200 hydraulic pressure issue and returns troubleshooting steps.

### Demo 3: Cross-Manual Ambiguity
- **Query:** `"What does error code E101 mean?"`
- **Expected Result:** System detects E101 in multiple manuals and asks for clarification (`ambiguous: true`), returning options.

### Demo 4: Insufficient Information (Pre-Filter Gate)
- **Query:** `"How do I replace the spindle bearing on CNC-100?"`
- **Expected Result:** System recognizes that this procedure is not covered in the manuals and refuses to answer without hallucinating.

### Demo 5: Second-Line LLM Self-Refusal (Pre-Filter Bypass Case)
- **Query:** `"What is the exact electrical torque specification for resetting E101 motor on CNC-100?"`
- **Expected Result:** System refuses to answer rather than hallucinating torque numbers.

---

## Part 2: Comprehensive Benchmark Suite & Running Test Matrix

> **Note for Teammate B & Evaluators:**  
> This is a living test document. Reuse this log for every test cycle (CLI, FastAPI `/docs`, Postman, and React UI). As you run each query against the backend, record the actual result, citation validity, and pass/fail status in the Running Test Log table at the bottom.

---

## 1. Exact-Code Queries (Targeted Retrieval & Citation)
*Expected Behavior:* Explicit machine identified. System must fetch the exact error code block, quote or paraphrase the exact mechanical/electrical causes, provide step-by-step corrective actions, and cite `Manual`, `Section`, and `[Page X]`.

### Query 1.1: `"E101 on CB-4400"`
- **Variant:** `"How do I fix error E101 on the CB-4400 conveyor belt?"`
- **Target Machine:** Conveyor Belt System — Model CB-4400
- **Target Citation:** `Conveyor Belt System — Model CB-4400 Troubleshooting Manual, Section 2: Error Codes, [Page 2]`
- **Expected Output:**
  - **Meaning:** Drive Motor Overcurrent Fault (VFD current draw > 125% FLA for > 3.5s).
  - **Probable Causes:** Excessive belt tension, jammed carrying/return idler roller, foreign debris under belt, gearbox binding.
  - **Corrective Steps:** LOTO switch at CP-1, inspect carrying deck/rollers for debris, measure belt tension with sonic tensiometer (25 mm deflection under 15 kg load), spin idler rollers by hand, check VFD parameter P-042.
  - **Negative Constraint:** Must **never** mention coolant, fluid filters, or spindle pumps.

### Query 1.2: `"What does error E101 mean on the CNC Milling Machine MX-7 Precision?"`
- **Variant:** `"What is the fix for E101 on the MX-7 CNC mill?"`
- **Target Machine:** CNC Milling Machine — Model MX-7 Precision
- **Target Citation:** `CNC Milling Machine — Model MX-7 Precision Troubleshooting Manual, Section 2: Error Codes, [Page 2]`
- **Expected Output:**
  - **Meaning:** Spindle Coolant Flow Failure (flow sensor FL-10 < 3.8 L/min while spindle > 1,000 RPM).
  - **Probable Causes:** Clogged 25-micron inline coolant filter cartridge, coolant pump failure/cavitation, low reservoir level (< 300L), kinked braided hose in Z-axis drag chain.
  - **Corrective Steps:** Check coolant sight gauge (8% water-soluble emulsion), check filter differential pop-up indicator, replace 25-micron cartridge (Part No. MX-FLT-025), inspect Z-axis hose, verify pump pressure (45–70 bar), run `M08;` macro.
  - **Negative Constraint:** Must **never** mention conveyor rollers, belt deflection, or motor overcurrent.

### Query 1.3: `"What is the corrective action for fault H205 on the HP-2200 hydraulic press?"`
- **Variant:** `"The hydraulic press HP-2200 tripped on code H205."`
- **Target Machine:** Hydraulic Press — Model HP-2200
- **Target Citation:** `Hydraulic Press — Model HP-2200 Troubleshooting Manual, Section 2: Error Codes, [Page 2]`
- **Expected Output:**
  - **Meaning:** Hydraulic Oil High Temperature Shutdown (reservoir transmitter TT-02 > 65°C).
  - **Probable Causes:** Fouled/scaled shell-and-tube heat exchanger, cooling water supply < 60 L/min, relief valve continuously bypassing, degraded ISO VG 46 fluid.
  - **Corrective Steps:** Run auxiliary pump in low-pressure idle mode, verify cooling water pressure (min 3.5 bar, < 22°C), clean duplex basket strainer, FLIR thermal scan for manifold bypass hot spots (> 75°C), test fluid viscosity (min 38 cSt at 40°C).

---

## 2. Natural-Language Symptom Queries (Semantic Vector Search)
*Expected Behavior:* No error code is supplied. Technician describes physical, acoustic, or visual symptoms. The vector retrieval engine must match the descriptive text in Section 3 of the relevant manual and retrieve the correct procedure.

### Query 2.1: `"Why is the conveyor overheating?"`
- **Variant:** `"Why is the conveyor belt drive gearbox running extremely hot?"`
- **Target Machine:** Conveyor Belt System — Model CB-4400
- **Target Citation:** `Conveyor Belt System — Model CB-4400 Troubleshooting Manual, Section 2: Error Codes, [Page 4]` (and Section 3)
- **Expected Output:**
  - Identifies RTD probe detecting lubricant temperature > 92°C.
  - Identifies low oil level from shaft seal leaks, degraded ISO VG 320 synthetic oil, or mechanical payload overload.
  - Corrective action instructs shutting down to cool to 40°C, checking sight glass red dot, inspecting viton seals, draining degraded oil, refilling 4.5 liters of Mobilgear SHC 320.

### Query 2.2: `"The conveyor belt is squealing and chirping during morning startup."`
- **Variant:** `"Conveyor makes high-pitched chirping sounds when starting up."`
- **Target Machine:** Conveyor Belt System — Model CB-4400
- **Target Citation:** `Conveyor Belt System — Model CB-4400 Troubleshooting Manual, Section 3: Common Symptoms, [Page 5]`
- **Expected Output:**
  - **Likely Cause:** Glazed/worn rubber lagging on drive drum, loose belt tension causing initial slippage before steady state, or dry snub roller bearings.
  - **Corrective Action:** Tighten tail pulley take-up bolts by 2 full turns, scuff glazed lagging with 40-grit emery cloth, spray belt grip conditioner, grease snub bearings with NLGI Grade 2 lithium grease.

### Query 2.3: `"Our CNC milled parts show high-pitched chatter marks along the finished vertical surfaces."`
- **Variant:** `"Why is the CNC mill vibrating and leaving severe chatter marks on parts?"`
- **Target Machine:** CNC Milling Machine — Model MX-7 Precision
- **Target Citation:** `CNC Milling Machine — Model MX-7 Precision Troubleshooting Manual, Section 3: Common Symptoms, [Page 5]`
- **Expected Output:**
  - **Likely Cause:** Excessive tool stickout/overhang, worn hybrid ceramic spindle bearings, low hydraulic vise clamping pressure, harmonic resonance.
  - **Corrective Action:** Reduce tool stickout to max 3:1 length-to-diameter ratio, increase vise pressure to 25 bar, check spindle radial runout with 300 mm test arbor (max 0.003 mm TIR), adjust spindle RPM by +/- 12% to escape resonance frequency.

### Query 2.4: `"The hydraulic press main pump is making a loud cavitation whining sound."`
- **Variant:** `"Hydraulic pump whining and shrieking under load."`
- **Target Machine:** Hydraulic Press — Model HP-2200
- **Target Citation:** `Hydraulic Press — Model HP-2200 Troubleshooting Manual, Section 3: Common Symptoms, [Page 6]`
- **Expected Output:**
  - **Likely Cause:** Suction line restriction from silted strainer, cold hydraulic fluid (< 20°C), or atmospheric air entering pump shaft seal.
  - **Corrective Action:** Verify reservoir temp is at least 32°C (engage immersion heaters if below 20°C), verify suction butterfly valve is 100% open, wash 100-mesh suction wire cloth strainer in mineral spirits, check driveshaft lip seal for air hissing.

---

## 3. Ambiguous Queries with No Machine Specified (Disambiguation Trigger)
*Expected Behavior:* The prompt contains `E101` but omits the machine model. Because `E101` means **Motor Overcurrent** on CB-4400 and **Spindle Coolant Loss** on MX-7 Precision, the system **must not guess**. It must set `ambiguous: true` and return clarification options.

### Query 3.1: `"E101"`
- **Target Machine:** None / Ambiguous (Matches both CB-4400 and MX-7)
- **Target Citation:** None (Ambiguity detected prior to answer generation)
- **Expected System Response:**
  - `ambiguous: true`
  - `options: ["Conveyor Belt System (CB-4400)", "CNC Milling Machine (MX-7 Precision)"]`
  - **Clarification Message:** *"Error code E101 exists on multiple machines with different meanings: (1) Conveyor Belt Model CB-4400: Drive Motor Overcurrent Fault, or (2) CNC Milling Machine Model MX-7 Precision: Spindle Coolant Flow Failure. Please specify which machine you are servicing."*

### Query 3.2: `"What does error E101 mean?"`
- **Target Machine:** None / Ambiguous
- **Expected System Response:**
  - Detects multi-manual conflict.
  - Prompts user to select the machine before displaying causes or corrective actions.

### Query 3.3: `"How do I fix error E101?"`
- **Target Machine:** None / Ambiguous
- **Expected System Response:**
  - System refuses to output repair steps immediately.
  - Prevents dangerous cross-machine instruction (e.g. telling a conveyor technician to purge a CNC coolant pump).

---

## 4. Queries Hitting the Undocumented Gap (Honest Refusal / Zero Hallucination)
*Expected Behavior:* The technician asks about status LED blinking/flickering patterns (e.g., 3 short blinks followed by a pause). This failure mode is deliberately omitted from all three manuals. The system must verify that retrieved chunk confidence is below threshold, refuse to invent an answer, and state clearly that the manuals do not cover it.

### Query 4.1: `"The status LED is flashing 3 short blinks followed by a long pause, what does this pattern mean?"`
- **Target Machine:** Unspecified / Any
- **Target Citation:** None (Undocumented Gap)
- **Expected System Response:**
  - `insufficient_info: true` (or confidence score < threshold)
  - **Refusal Message:** *"The provided machine manuals do not document status LED blink patterns or flash codes. Please inspect the alphanumeric error code on the machine's digital display / HMI console or contact equipment technical support."*
  - **Negative Constraint:** Must **never** invent blink explanations or tie it to motors, coolant, or pressure.

### Query 4.2: `"What causes the intermittent flickering pattern on the CNC MX-7 status LED?"`
- **Target Machine:** CNC Milling Machine — Model MX-7 Precision
- **Target Citation:** None (Undocumented Gap)
- **Expected System Response:**
  - Recognizes machine model MX-7 Precision.
  - Confirms the MX-7 manual covers codes E101–E520 and physical symptoms, but contains **no documentation** for status LED blink or flicker sequences.
  - Refuses to hallucinate an explanation.

### Query 4.3: `"The hydraulic press HP-2200 status LED is blinking 3 times in a row. How do I clear it?"`
- **Target Machine:** Hydraulic Press — Model HP-2200
- **Target Citation:** None (Undocumented Gap)
- **Expected System Response:**
  - States that while hydraulic error codes H201–H622 are documented, status LED blink codes are not present in the HP-2200 manual.
  - Directs operator to check transducer readouts and HMI screen alarms instead.
=======
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

Use this table during Phase 3, Phase 5, and Phase 8 validation runs. Duplicate the table for each test cycle.

### Test Run Date: _________________ | Tested By: _________________ | Environment: [ ] CLI / [ ] FastAPI / [ ] React UI

| # | Query Tested | Category | Expected Outcome | Actual Output & Citation | Pass / Fail | Notes / Discrepancies |
|---|---|---|---|---|---|---|
| 1 | `"How do I fix error E101 on the CB-4400 conveyor belt?"` | 1. Exact Code | CB-4400 Overcurrent, Page 2 | | [ ] Pass<br>[ ] Fail | |
| 2 | `"What does error E101 mean on the CNC Milling Machine MX-7 Precision?"` | 1. Exact Code | MX-7 Coolant Loss, Page 2 | | [ ] Pass<br>[ ] Fail | |
| 3 | `"What is the corrective action for fault H205 on the HP-2200 hydraulic press?"` | 1. Exact Code | HP-2200 High Temp, Page 2 | | [ ] Pass<br>[ ] Fail | |
| 4 | `"Why is the conveyor overheating?"` | 2. Symptom | Gearbox temp E401 / Page 4 | | [ ] Pass<br>[ ] Fail | |
| 5 | `"The conveyor belt is squealing and chirping during morning startup."` | 2. Symptom | Lagging / tension, Page 5 | | [ ] Pass<br>[ ] Fail | |
| 6 | `"Our CNC milled parts show high-pitched chatter marks along the finished vertical surfaces."` | 2. Symptom | Tool stickout / runout, Page 5 | | [ ] Pass<br>[ ] Fail | |
| 7 | `"The hydraulic press main pump is making a loud cavitation whining sound."` | 2. Symptom | Suction strainer / cold oil, Page 6 | | [ ] Pass<br>[ ] Fail | |
| 8 | `"E101"` | 3. Ambiguous | Disambiguate: CB-4400 vs MX-7 | | [ ] Pass<br>[ ] Fail | |
| 9 | `"What does error E101 mean?"` | 3. Ambiguous | Clarification prompt required | | [ ] Pass<br>[ ] Fail | |
| 10 | `"How do I fix error E101?"` | 3. Ambiguous | Refuse repair steps without machine | | [ ] Pass<br>[ ] Fail | |
| 11 | `"The status LED is flashing 3 short blinks followed by a long pause, what does this pattern mean?"` | 4. Undocumented | Honest refusal (not in manuals) | | [ ] Pass<br>[ ] Fail | |
| 12 | `"What causes the intermittent flickering pattern on the CNC MX-7 status LED?"` | 4. Undocumented | Honest refusal for MX-7 LED | | [ ] Pass<br>[ ] Fail | |
| 13 | `"The hydraulic press HP-2200 status LED is blinking 3 times in a row. How do I clear it?"` | 4. Undocumented | Honest refusal for HP-2200 LED | | [ ] Pass<br>[ ] Fail | |
