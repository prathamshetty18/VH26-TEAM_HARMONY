# MachineAssist — RAG-Based Intelligent Machine Troubleshooting System

**VH26-TEAM_HARMONY · Application Data Management (RAG)**

A retrieval-augmented troubleshooting assistant for factory technicians. It ingests multiple machine manuals, resolves conflicting/overlapping error codes across machines, retrieves the right information with citations, and refuses to answer when the manuals don't support an answer.

This is **not** a basic "chat with PDF" app. It is explicitly designed to handle:
- **The same error code meaning different things across different machines**
- **Ambiguous queries** that need clarification before answering
- **Hallucination control** — a real, three-gate mechanism, not just a prompt instruction
- **Full traceability**: every answer cites manual, section, and machine

**Status:** Full-Stack Integrated (Phases 0–8 + Hybrid Search + Context Detection + SVG Schematics). Verified 100% (15/15 passed) against the comprehensive benchmark test suite.

---

## 1. System Architecture

```mermaid
flowchart TD
    A[Technician Query] --> B[FastAPI Endpoint /query & Web UI]
    B --> C[Query Understanding: 4-Layer Detection]
    C --> C1[1. Alias Match]
    C --> C2[2. Fuzzy Match - Typos]
    C --> C3[3. Semantic Match - Descriptions]
    C --> C4[4. Session Context Fallback]
    C --> D[Hybrid Retrieval Engine]
    D --> D1[ChromaDB Exact Keyword Pre-Filter]
    D --> D2[SentenceTransformer Dense Vector Search]
    D --> E{Cross-Manual Ambiguity Check}
    E -- Multi-Machine Conflict --> F[Return Clickable Machine Options Card]
    E -- Resolved or Scoped --> G{Safety Gatekeeper: 3 Gates}
    G -- Fails Similarity / Error-Code / Keyword Gate --> H[Hard Refusal: No LLM Call, Zero Guesswork]
    G -- Passes All 3 Gates --> I[Context Assembly & Grounding]
    I --> J[Gemini Flash LLM via google-genai]
    I --> K[Technical SVG Schematic Resolution]
    J --> L[Structured 4-Section Answer Card + Interactive Schematic + Citations]
    K --> L
```

**Pipeline order:**
`parse_query_with_context` → `hybrid_retrieve` → `check_ambiguity` → *(if ambiguous: return options, stop)* → `safety gates` → *(if insufficient: hard refusal, stop)* → `assemble_context` → `generate_answer` → `match_diagram` → `update memory` → `return answer + diagrams + sources`

> **The core design principle:** Retrieve first, generate second, never invent. The LLM only writes prose from grounded context — it never decides facts, and it is never called when safety gates fail.

---

## 2. Tech Stack

| Component | Choice |
|---|---|
| **Language** | Python 3.10+ |
| **Text/manual ingestion** | Custom parser, `SECTION:`-delimited (see `src/ingest.py`) |
| **Embeddings** | `sentence-transformers` (`all-MiniLM-L6-v2`) — local, free, no API key |
| **Vector DB** | ChromaDB, persistent, cosine distance, stored at `./chroma_db` |
| **LLM** | Gemini 2.5 Flash via the `google-genai` SDK (`GEMINI_API_KEY` required) |
| **Backend API** | FastAPI (`src/api.py`) |
| **Frontend UI** | React (built separately — see [Section 8: Frontend Integration](#8-frontend-integration)) |
| **Session memory** | In-memory per-`session_id` store (`src/memory.py`) |

> **Note:** Embeddings are local and free; only the generation step needs an API key, since answer quality matters more than embedding quality here.

---

## 2.1 Supported Factory Machinery

The factory environment operates 6 distinct physical machine units with dedicated technical documentation:

| Machine Name | Model Code | Manual Source | Subsystems Covered | Distinct Identity Notes |
|---|---|---|---|---|
| **`CNC-100`** | `X200` | `cnc100.txt` | Spindle motor, cooling fan, spindle axis load, coolant tank | Compact machining center (distinct from MX-7) |
| **`CNC Milling Machine`** | `MX-7 Precision` | `cncmx7.txt` | Through-spindle coolant (TSC), RTD thermistor, Heidenhain optical scale | Heavy 5-axis vertical machining center |
| **`Press-200`** | `P400` | `press200.txt` | Main cylinder, E-stop interlock, guide pillars | Workshop hydraulic press (distinct from HP-2200) |
| **`Hydraulic Press`** | `HP-2200` | `presshp2200.txt` | 280-bar ram, proportional valve PV-01, water chiller, accumulators | Heavy industrial production stamping press |
| **`Conveyor Belt System`** | `CB-4400` | `conveyorcb4400.txt` | VFD inverter drive, optical pulse tachometer, helical-bevel gearbox | Automated material handling transfer line |
| **`RobotArm-300`** | `R300` | `robotarm300.txt` | Brushless AC servo, harmonic drive reducer, optical resolver | 6-axis articulated assembly manipulator |

---

## 3. Project Structure

```
machineassist/
├── data/
│   └── manuals/              # source manuals (txt), one per machine
│       ├── cnc100.txt         # CNC-100 (Model X200)
│       ├── cncmx7.txt         # CNC Milling Machine (Model MX-7 Precision)
│       ├── conveyorcb4400.txt # Conveyor Belt System (Model CB-4400)
│       ├── press200.txt       # Press-200 (Model P400)
│       ├── presshp2200.txt    # Hydraulic Press (Model HP-2200)
│       └── robotarm300.txt    # RobotArm-300 (Model R300)
├── src/
│   ├── ingest.py             # Phase 1: parse SECTION: blocks + metadata tagging
│   ├── embed_store.py        # Phase 2: sentence-transformers embeddings + Chroma store
│   ├── query_understanding.py# Phase 3: extract machine/error_code from query
│   ├── retrieval.py          # Phase 4: metadata-filtered, scored retrieval
│   ├── disambiguation.py     # Phase 5: detect + resolve cross-manual ambiguity
│   ├── safety.py             # Phase 6: three-gate hallucination control
│   ├── llm_answer.py         # Phase 7: context assembly + Gemini generation
│   ├── memory.py             # Phase 8: per-session conversation state
│   └── api.py                # Phase 8: FastAPI backend, exposes the pipeline over HTTP
├── chroma_db/                # persisted vector store (generated, not committed)
├── frontend/                 # React app — built separately, see Section 8
├── tests/
│   └── test_all_demos.py     # the 4 required demo cases, automated
├── DESIGN.md                 # full phased build plan for the IDE/agent to follow
├── requirements.txt
└── README.md
```

---

## 4. Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
export GEMINI_API_KEY=...       # Windows PowerShell: $env:GEMINI_API_KEY="..."
```

`sentence-transformers` downloads its model (`all-MiniLM-L6-v2`) automatically on first run — no API key required for embeddings or retrieval.

---

## 5. Running

### Option A: Unified Single-Port Application (Production Mode)
Start the FastAPI server; it automatically serves the complete production React web console, static assets, and API routes:
```bash
uvicorn src.api:app --reload --port 8000
```
Open **`http://localhost:8000/`** in your browser.

### Option B: Development Mode with Vite Hot-Reloading
Start the backend and frontend servers in separate terminals:
```bash
# Terminal 1: Backend API
uvicorn src.api:app --reload --port 8000

# Terminal 2: React Vite Dev Server (auto-proxies all API calls to port 8000)
cd frontend
npm run dev
```
Open **`http://localhost:5173/`** in your browser.

---

## 6. System Verification Matrix

All 15 core and edge benchmark scenarios pass with **100% success rate** (`tests/test_system_verification.py`):

| ID | Test Category | Query / Scenario | Target Machine | Pipeline Verification | Result |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **TC-01** | Exact Code | *"What does E101 mean on CNC-100?"* | CNC-100 | Keyword pre-filter (score 1.0) fetches E101; 4-section answer generated with diagram | ✅ PASS |
| **TC-02** | Exact Code | *"What is error code E101 on Press-200?"* | Press-200 | Filtered retrieval extracts Press-200 hydraulic pressure low chunks | ✅ PASS |
| **TC-03** | Exact Code | *"How do I fix error E101 on the CB-4400 conveyor belt?"* | Conveyor Belt | VFD current overload retrieved; step-by-step LOTO and tensioning instructions | ✅ PASS |
| **TC-04** | Exact Code | *"What is the corrective action for fault H205 on the HP-2200?"* | Hydraulic Press | Oil high temperature shutdown chunks retrieved with heat exchanger procedure | ✅ PASS |
| **TC-05** | Semantic Symptom | *"Why is Press-200 stopping due to oil pressure?"* | Press-200 | Dense vector search matches E101 symptoms without literal error code in prompt | ✅ PASS |
| **TC-06** | Semantic Symptom | *"Why is the conveyor overheating?"* | Conveyor Belt | Semantic match identifies drive gearbox RTD probe lubrication symptoms | ✅ PASS |
| **TC-07** | Semantic Symptom | *"Our CNC milled parts show high-pitched chatter marks..."* | CNC Milling | Dense vector match extracts tool stickout, arbor TIR runout, and RPM tuning | ✅ PASS |
| **TC-08** | Ambiguity Trigger | *"What does E101 mean?"* | None | Detects cross-manual conflict; prompts user to select target machine | ✅ PASS |
| **TC-09** | Ambiguity Resolution | User clicks *"Press-200"* option | Press-200 | Inherits active E101 error from memory; outputs Press-200 corrective actions | ✅ PASS |
| **TC-10** | Multi-Turn Memory | Follow-up: *"What if that doesn't work?"* | CNC-100 | Session memory inherits machine and error code; provides next diagnostic steps | ✅ PASS |
| **TC-11** | Honest Refusal | *"How do I replace spindle bearing on CNC-100?"* | CNC-100 | Undocumented topic; 0% keyword overlap on bearing; hard safety refusal returned | ✅ PASS |
| **TC-12** | Honest Refusal | *"Status LED flashing 3 short blinks followed by long pause"* | None | Undocumented pattern; score below threshold; hard safety refusal returned | ✅ PASS |
| **TC-13** | Honest Refusal | *"How do I bypass safety light curtain interlock on Press-200?"* | Press-200 | Critical safety bypass keyword detected; hard refusal returned without guessing | ✅ PASS |
| **TC-14** | Schema Integrity | Citation format & metadata integrity | Any | Citations verify non-empty `manual`, `section`, `page`, and grounded `snippet` | ✅ PASS |
| **TC-15** | Machine Scoping | Scoped Machine header filter validation | CNC-100 | Scoped filter isolates chunks strictly to the selected machine unit | ✅ PASS |

---

## 7. Hallucination Control — the Three-Gate Safety System

A plain *"please don't hallucinate"* instruction to the LLM isn't a real safeguard — it's a request the model can still ignore under pressure. Instead, `src/safety.py` gates every query through three independent checks before the LLM is ever invoked:

1. **Similarity score gate** — The top retrieved chunk's relevance score must be **≥ 0.40**. Below that, the manuals likely don't cover the topic.
2. **Error-code verification gate** — If the query names an explicit error code (e.g. `E101`), that code must actually appear in the retrieved chunks. Prevents the system from answering about a code it never actually found.
3. **Content keyword overlap gate** — At least **50%** of the query's core content tokens (e.g., `bearing`, `replace`) must appear in the retrieved manual text. Catches queries that are topically adjacent but not actually documented.

If any gate fails, the system short-circuits to a fixed refusal string and **does not call the LLM at all** — this both guarantees no invented answer and saves generation cost:

> *"The available manuals do not provide sufficient information to answer this. I won't provide an unsupported answer."*

---

## 8. Frontend Integration

The frontend is a separate React app that talks to the Python backend over HTTP:

- **`session_id`** lets the backend track conversation memory (Phase 8) per browser tab, so a follow-up like *"what if that doesn't work?"* reuses the previous machine/error context without the frontend managing any RAG state itself.
- **Enable CORS** in FastAPI so the React dev server (typically `localhost:3000` or `5173`) can call the backend (typically `localhost:8000`) during development.
- **Contract Agreement:** Agree on the exact JSON request/response shape with the frontend teammate early so backend and frontend can be built fully in parallel.
- See `FRONTEND_DESIGN.md` for the UI/UX spec — layout, component states (answer / ambiguity / refusal cards), and copy guidelines.

---

## 9. How to Build This

See [`DESIGN.md`](./DESIGN.md) for the full phased build plan (Phase 0 → Phase 8). Each phase has its own acceptance criteria and should be fully working before the next one starts — this is how the backend above was actually built and verified.

---

## 10. The 4 Required Demo Cases

1. **Exact error code** — `E101` on a named machine → correct machine-specific answer
2. **Natural language symptom** — *"why is Machine A overheating?"* → semantic retrieval finds the right chunk despite no exact keyword match
3. **Cross-manual ambiguity** — `E101` with no machine specified, where 2+ machines define it differently → system asks which machine instead of guessing
4. **Insufficient information** — a question with no documented answer → system explicitly refuses rather than inventing a fix

See `tests/test_all_demos.py` for the exact scripted queries and expected behavior.
