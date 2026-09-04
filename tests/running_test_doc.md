# MachineAssist — Running Test Document & Benchmark Suite

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

---

## Running Test Log (Reusable Test Matrix)

Use this table during Phase 3, Phase 5, and Phase 8 validation runs. Duplicate the table for each test cycle.

### Test Run Date: 2026-09-04 (Batch 1 — Backend v1 Evaluation) | Tested By: Teammate B / QA | Environment: [x] Code Inspection & Pipeline Trace

| # | Query Tested | Category | Expected Outcome | Actual Output & Citation | Pass / Fail | Notes / Discrepancies |
|---|---|---|---|---|---|---|
| 1 | `"How do I fix error E101 on the CB-4400 conveyor belt?"` | 1. Exact Code | CB-4400 Overcurrent, Page 2 | `parse_query` machine=None; unindexed in chroma | **FAIL** | "CB-4400" not in `DEFAULT_KNOWN_MACHINES` |
| 2 | `"What does error E101 mean on the CNC Milling Machine MX-7 Precision?"` | 1. Exact Code | MX-7 Coolant Loss, Page 2 | `parse_query` machine=None; unindexed in chroma | **FAIL** | "MX-7 Precision" not in `DEFAULT_KNOWN_MACHINES` |
| 3 | `"What is the corrective action for fault H205 on the HP-2200 hydraulic press?"` | 1. Exact Code | HP-2200 High Temp, Page 2 | `parse_query` error_code=None; machine=None | **FAIL** | `\b(E\d{3})\b` ignores `H205`; machine unmapped |
| 4 | `"Why is the conveyor overheating?"` | 2. Symptom | Gearbox temp E401 / Page 4 | Chroma search misses due to lack of CB-4400 index | **FAIL** | Requires re-indexing `conveyorcb4400.txt` |
| 5 | `"The conveyor belt is squealing and chirping during morning startup."` | 2. Symptom | Lagging / tension, Page 5 | Chroma search misses | **FAIL** | Requires re-indexing `conveyorcb4400.txt` |
| 6 | `"Our CNC milled parts show high-pitched chatter marks along the finished vertical surfaces."` | 2. Symptom | Tool stickout / runout, Page 5 | Chroma search misses | **FAIL** | Requires re-indexing `cncmx7.txt` |
| 7 | `"The hydraulic press main pump is making a loud cavitation whining sound."` | 2. Symptom | Suction strainer / cold oil, Page 6 | Chroma search misses | **FAIL** | Requires re-indexing `presshp2200.txt` |
| 8 | `"E101"` | 3. Ambiguous | Disambiguate: CB-4400 vs MX-7 | Disambiguates only CNC-100 vs Press-200 | **FAIL** | Only old `cnc100.txt`/`press200.txt` are in DB |
| 9 | `"What does error E101 mean?"` | 3. Ambiguous | Clarification prompt required | Prompts CNC-100 vs Press-200 | **FAIL** | Old manual definitions returned |
| 10 | `"How do I fix error E101?"` | 3. Ambiguous | Refuse repair steps without machine | Prompts CNC-100 vs Press-200 | **FAIL** | Needs new machine definitions |
| 11 | `"The status LED is flashing 3 short blinks followed by a long pause, what does this pattern mean?"` | 4. Undocumented | Honest refusal (not in manuals) | Gate 1 & Gate 3 trigger refusal | **PASS** | Refusal message triggered correctly |
| 12 | `"What causes the intermittent flickering pattern on the CNC MX-7 status LED?"` | 4. Undocumented | Honest refusal for MX-7 LED | Gate 1 triggers refusal | **PASS** | Zero LED text in corpus guarantees refusal |
| 13 | `"The hydraulic press HP-2200 status LED is blinking 3 times in a row. How do I clear it?"` | 4. Undocumented | Honest refusal for HP-2200 LED | Gate 1 triggers refusal | **PASS** | Refusal triggered |

---

## Batch 1 Bug Reports for Coder (Query / Expected / Actual)

### Bug 1: Machine Name Extraction Fails on All New Models
- **Query:** `"How do I fix error E101 on the CB-4400 conveyor belt?"` / `"What does error E101 mean on the CNC Milling Machine MX-7 Precision?"`
- **Expected:** `parse_query()` identifies `machine: "Conveyor Belt System"` (or `"CB-4400"`) and `machine: "CNC Milling Machine"` (or `"MX-7 Precision"`).
- **Actual:** `parse_query()` returns `machine: None` because `DEFAULT_KNOWN_MACHINES` in `src/query_understanding.py` is hardcoded to `["CNC-100", "Press-200", "RobotArm-300"]` and `MACHINE_ALIASES` lacks aliases for the new machines.
- **Coder Fix:** Expand `DEFAULT_KNOWN_MACHINES` and `MACHINE_ALIASES` in `src/query_understanding.py` to include:
  ```python
  DEFAULT_KNOWN_MACHINES = [
      "CNC-100", "Press-200", "RobotArm-300",
      "Conveyor Belt System", "CNC Milling Machine", "Hydraulic Press",
      "CB-4400", "MX-7 Precision", "HP-2200"
  ]
  ```

### Bug 2: Error Code Regex Ignores 'H' and 'SYM' Series Codes
- **Query:** `"What is the corrective action for fault H205 on the HP-2200 hydraulic press?"`
- **Expected:** `parse_query()` extracts `error_code: "H205"`.
- **Actual:** `parse_query()` returns `error_code: None` because regex is hardcoded to `\b(E\d{3})\b`.
- **Coder Fix:** Update regex in `src/query_understanding.py` (line 53) and `src/safety.py` (line 75) from `r"\b(E\d{3})\b"` to:
  ```python
  r"\b([EH]\d{3}|SYM-[A-Z0-9-]+)\b"
  ```

### Bug 3: Ingestion Parser Drops Error Code from Meaning/Causes Chunks
- **Query:** Semantic or exact search for error codes against `conveyorcb4400.txt`, `cncmx7.txt`, `presshp2200.txt`.
- **Expected:** Both the Meaning/Causes chunk and the Troubleshooting Steps chunk are tagged with `error_code: "E101"`.
- **Actual:** In `src/ingest.py`, `sections = re.split(r"(?=SECTION:)", content)` splits right at `SECTION:`. In the new manuals, `ERROR CODE: E101` precedes `SECTION: Error Codes`, so `ERROR CODE:` is lost in the first chunk, resulting in `error_code: None`.
- **Coder Fix:** In `src/ingest.py`, split sections by `r"(?=(?:ERROR CODE:[^\n]+\n)?SECTION:)"` or carry forward the active `ERROR CODE:` across sections within the file.

### Bug 4: ChromaDB Indexing Needs Refresh with New Manuals
- **Query:** Any query against CB-4400, MX-7, or HP-2200.
- **Expected:** ChromaDB returns chunks from `conveyorcb4400.txt`, `cncmx7.txt`, `presshp2200.txt`.
- **Actual:** `chroma_db/` only contains chunks from the original `cnc100.txt`, `press200.txt`, and `robotarm300.txt`.
- **Coder Fix:** Re-run `src/ingest.py` and `src/embed_store.py` indexing to ingest the new `.txt` files into `chroma_db/`.

---

## Batch 2 Re-Test Matrix (To be filled once coder confirms fixes)

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
<<<<<<< HEAD

=======
>>>>>>> 01c16fc279a072b15498729d2e1438b6e4551853
