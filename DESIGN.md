# DESIGN.md — Phased Build Plan for MachineAssist

## How to use this document

This project is broken into **9 phases (Phase 0 → Phase 8)**. Each phase:
- Has a single, narrow goal
- Produces one working file/module
- Has an **acceptance criteria** checklist — do not proceed to the next phase until every box is true
- Assumes all previous phases are complete and working

If you are an IDE coding agent: implement phases **in order**, one at a time. After finishing a phase, run its acceptance test before starting the next phase. Do not jump ahead to later phases or add bonus features (OCR, reranking, hybrid search, multilingual, voice) until Phase 8 is done and confirmed working — those are optional and listed separately at the end.

---

## Phase 0 — Environment & Skeleton

**Goal:** A runnable, empty project skeleton with dependencies installed.

**Tasks:**
1. Create the folder structure exactly as in README.md (`data/manuals/`, `src/`, `tests/`)
2. Create `requirements.txt`:
   ```
   langchain
   langchain-community
   chromadb
   pypdf
   streamlit
   openai
   python-dotenv
   ```
3. Create empty stub files for every module listed in the project structure (`ingest.py`, `embed_store.py`, etc.) with just a `# TODO Phase X` comment
4. Set up `.env` loading for API keys

**Acceptance criteria:**
- [ ] `pip install -r requirements.txt` succeeds with no errors
- [ ] All stub files exist and import without error
- [ ] API key loads successfully from `.env`

---

## Phase 1 — Author Test Manuals (Data, not code)

**Goal:** Create the source data that will make the demos work. This is deliberately done before any retrieval code, because the retrieval code will be tested against this data.

**Tasks:**
1. In `data/manuals/`, create 3-4 plain text files, one per machine: `cnc100.txt`, `press200.txt`, `robotarm300.txt`, etc.
2. Each manual must use a **consistent heading structure** so the parser in Phase 2 can rely on it:
   ```
   MACHINE: CNC-100
   MODEL: X200

   ERROR CODE: E101
   SECTION: Error Codes
   MEANING: Excessive motor temperature.
   CAUSES:
   - Cooling fan failure
   - Blocked ventilation
   - Excessive load

   SECTION: E101 Troubleshooting
   STEPS:
   1. Switch off the machine.
   2. Inspect cooling fan.
   3. Check ventilation openings.
   4. Allow motor to cool before restarting.
   ```
3. **Deliberately duplicate one error code across two machines with a different meaning** — e.g. `E101` = motor overheating on CNC-100, but `E101` = hydraulic pressure low on Press-200. This is required for Demo 3.
4. **Deliberately leave one topic undocumented** in every manual (e.g. no manual mentions "bearing replacement") — this is required for Demo 4.
5. Add 2-3 more error codes per machine so retrieval has more than one thing to distinguish between.

**Acceptance criteria:**
- [ ] At least 3 manuals exist with consistent heading structure
- [ ] Exactly one error code appears in 2+ manuals with clearly different meanings
- [ ] At least one topic is guaranteed absent from all manuals
- [ ] A human can read the manuals and understand them without ambiguity (this matters — poorly written test data will silently break every later phase)

---

## Phase 2 — Ingestion, Chunking & Metadata

**Goal:** Turn the manual text files into chunks tagged with metadata.

**File:** `src/ingest.py`

**Tasks:**
1. Write a parser that reads each manual file and splits it by `SECTION:` blocks (not by fixed character count — structure-aware chunking beats blind chunking here)
2. For each chunk, extract and attach metadata:
   ```python
   {
       "text": "...",
       "machine": "CNC-100",
       "model": "X200",
       "manual": "cnc100.txt",
       "section": "E101 Troubleshooting",
       "error_code": "E101"   # None if the section has no associated code
   }
   ```
3. Chunks should be small enough to be semantically focused (roughly one `SECTION:` block per chunk) but not so small that a single fact is split mid-sentence
4. Return a list of these chunk dictionaries for all manuals combined

**Acceptance criteria:**
- [ ] Running `ingest.py` on the Phase 1 data prints a list of chunks with correct metadata for every manual
- [ ] Every chunk has a non-null `machine` field
- [ ] The duplicated error code (e.g. E101) appears in chunks from 2+ different `machine` values with different `text`

---

## Phase 3 — Embeddings & Vector Store

**Goal:** Make chunks searchable by meaning, not just keyword.

**File:** `src/embed_store.py`

**Tasks:**
1. Take the chunk list from Phase 2, embed each chunk's text using the chosen embedding model
2. Store embeddings + text + metadata in a local Chroma collection (persisted to disk so you don't re-embed every run)
3. Write a `search(query, k=5, filter_metadata=None)` function that:
   - Embeds the query
   - Runs similarity search against Chroma
   - Optionally filters by metadata (e.g. `{"machine": "CNC-100"}`) before or after search
   - Returns top-k chunks **with their similarity/distance scores**

**Acceptance criteria:**
- [ ] `search("why is my motor overheating")` returns the CNC-100 E101 chunk near the top, even though the query never says "E101"
- [ ] `search("E101", filter_metadata={"machine": "Press-200"})` returns only Press-200's E101 chunk, not CNC-100's
- [ ] Every returned result includes a numeric relevance score

---

## Phase 4 — Query Understanding

**Goal:** Before searching, figure out what the user is actually asking for.

**File:** `src/query_understanding.py`

**Tasks:**
1. Write a function `parse_query(query, known_machines, known_error_codes)` that extracts, using simple string/regex matching (no ML needed):
   - `machine`: matched against a known list of machine names (case-insensitive, allow partial matches like "Machine A" vs "CNC-100" if you set up aliases)
   - `error_code`: regex pattern like `E\d{3}` or similar to your manual's format
   - `raw_query`: the original text, for semantic search
2. Return a structured dict:
   ```python
   {"machine": "CNC-100", "error_code": "E101", "raw_query": "..."}
   ```
   Fields are `None` when not detected.

**Acceptance criteria:**
- [ ] `parse_query("What does E101 mean on Machine A?")` correctly extracts both the machine and the error code
- [ ] `parse_query("the motor is making a weird noise")` correctly returns `machine=None, error_code=None` (pure semantic case)

---

## Phase 5 — Retrieval + Disambiguation

**Goal:** Combine query understanding with search, and detect when the system should ask a clarifying question instead of answering.

**File:** `src/retrieval.py` and `src/disambiguation.py`

**Tasks (`retrieval.py`):**
1. Write `retrieve(parsed_query)`:
   - If `machine` is known → filter search to that machine
   - Else → search across all manuals
   - Return top-k chunks with scores

**Tasks (`disambiguation.py`):**
1. Write `check_ambiguity(parsed_query, retrieved_chunks)`:
   - If `error_code` is set, `machine` is NOT set, and the retrieved chunks span 2+ different machines with meaningfully different content → return an ambiguity object:
     ```python
     {
         "ambiguous": True,
         "options": [
             {"machine": "CNC-100", "summary": "Motor overheating"},
             {"machine": "Press-200", "summary": "Hydraulic pressure low"}
         ]
     }
     ```
   - Otherwise → `{"ambiguous": False}`

**Acceptance criteria:**
- [ ] Query `"E101"` with no machine specified returns `ambiguous: True` with both machine options listed correctly
- [ ] Query `"What does E101 mean on Machine A?"` returns `ambiguous: False` and retrieves only Machine A's content
- [ ] Query `"why is Machine A overheating"` retrieves the correct chunk via semantic match

---

## Phase 6 — Hallucination / Safety Control

**Goal:** Refuse to answer when the manuals don't support an answer, instead of letting the LLM guess.

**File:** `src/safety.py`

**Tasks:**
1. Pick a relevance-score threshold by testing a few queries and observing the score distribution (this number depends on your embedding model — tune it manually)
2. Write `is_sufficient(retrieved_chunks, threshold)`:
   - If the top chunk's relevance score is below the threshold → return `False`
   - Else → return `True`
3. When insufficient, the system should return a fixed response like:
   > "The available manuals do not provide sufficient information to answer this. I won't provide an unsupported answer."
   — and should **not** call the LLM at all in this case (saves cost and guarantees no hallucination)

**Acceptance criteria:**
- [ ] A query about the deliberately undocumented topic from Phase 1 (e.g. "how do I replace the motor bearing") returns the insufficient-information response
- [ ] A query with a clearly documented answer passes the threshold and proceeds to generation

---

## Phase 7 — Context Assembly & LLM Answer Generation

**Goal:** Turn retrieved chunks into a well-structured, cited answer.

**File:** `src/llm_answer.py`

**Tasks:**
1. Write `assemble_context(chunks)` that formats retrieved chunks into a labeled block:
   ```
   [Source 1]
   Machine: CNC-100
   Manual: cnc100.txt
   Section: Error Codes

   E101 indicates excessive motor temperature.

   [Source 2]
   ...
   ```
2. Write the system prompt (store as a constant, easy to edit):
   ```
   You are a factory troubleshooting assistant. Answer ONLY using the
   information in the provided sources below. Do not use outside
   knowledge. If the sources do not contain enough information to
   answer, say so explicitly and do not guess.

   Structure every answer as:
   1. Error meaning
   2. Probable causes
   3. Step-by-step corrective action
   4. Sources (manual name, section, and page/section reference)
   ```
3. Write `generate_answer(query, context)` that calls the LLM with the system prompt + assembled context + user query, and returns the structured response
4. Attach the source metadata separately as well (don't rely solely on the LLM to get citations right — pass through the actual metadata from retrieval alongside the generated text)

**Acceptance criteria:**
- [ ] A documented query returns an answer with all 4 sections (meaning, causes, steps, sources)
- [ ] The cited sources in the answer match the actual chunks that were retrieved (not invented ones)

---

## Phase 8 — Conversation Memory & Backend API

**Goal:** Tie everything together into a working backend with follow-up support, exposed over HTTP so the separately-built React frontend can call it. The React UI itself is out of scope for this backend build — coordinate the request/response shape with the frontend teammate early.

**Files:** `src/memory.py`, `src/api.py`

**Tasks (`memory.py`):**
1. A simple per-session state store keyed by `session_id`, holding: `last_machine`, `last_error_code`, `last_answer`. An in-memory Python dict (`{session_id: {...}}`) is enough for a hackathon — no database needed.
2. Before parsing a new query, if the new query is vague (e.g. contains "that", "it", "this" and lacks its own machine/error code), inject the stored `last_machine`/`last_error_code` for that `session_id` into the parsed query

**Tasks (`api.py`):**
1. Build a FastAPI app with CORS enabled (so the React dev server can call it from a different port during development)
2. Expose endpoints:
   - `POST /query` — body: `{"message": "...", "session_id": "..."}`. Runs the full pipeline in order:
     `parse_query → retrieve → check_ambiguity → (if ambiguous: return options, stop) → is_sufficient → (if insufficient: return refusal, stop) → assemble_context → generate_answer → update memory → return answer + sources`
     Response shape: `{"answer": "...", "sources": [{"manual": "...", "section": "...", "page": ...}], "ambiguous": false, "options": []}`
   - `GET /machines` — returns the list of known machine names, so the frontend can populate a dropdown
3. Test every endpoint with `curl` or FastAPI's built-in `/docs` page before handing off to the frontend teammate — the backend must work standalone first

**Acceptance criteria:**
- [ ] All 4 required demo cases work end-to-end by calling `POST /query` directly (via `curl` or `/docs`), independent of any frontend
- [ ] Sending a follow-up message like "what if that doesn't work?" with the same `session_id` correctly reuses the previous machine/error context
- [ ] `/query` responses always include structured `sources` (not just prose) so the frontend can render citations separately from the answer text
- [ ] CORS is configured and a simple fetch from a local React dev server successfully receives a response

---

## Optional / Bonus phases (only after Phase 8 is fully working)

Do not attempt these unless Phase 0–8 are complete and demoed successfully. Pick at most one or two if time remains.

- **Hybrid search:** add a keyword/regex pre-filter for exact error codes alongside vector search
- **Reranking:** re-score top-20 retrieved chunks with a cross-encoder before picking the top-5 to send to the LLM
- **OCR:** for scanned PDF manuals, run through Tesseract before chunking
- **Multilingual queries:** translate the query to English before parsing/retrieval
- **Voice input:** add speech-to-text on top of the Streamlit text input

---

## Design principles to hold onto throughout

1. **Retrieve first, generate second, never invent.** The LLM only writes prose; it never decides facts.
2. **Precision over recall.** A wrong-but-plausible chunk is worse than no chunk. When in doubt, refuse rather than guess.
3. **Every answer must be traceable** to a specific manual, section, and machine.
4. **Ambiguity is a feature, not a bug.** Asking "which machine?" is the correct behavior, not a failure state.
