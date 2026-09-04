# MachineAssist — Python Codebase In-Depth Architectural Walkthrough

This document provides a comprehensive, function-by-function and line-by-line architectural walkthrough of all Python (`.py`) files in the **MachineAssist** repository. It excludes markdown files and focuses strictly on code architecture, algorithmic logic, data structures, safety mechanisms, and inter-module interactions.

---

## 1. System Architecture & End-to-End Pipeline

```
                              [ Technician / Client ]
                                         │
                                         ▼ (HTTP POST /query)
                            ┌────────────────────────┐
                            │      src/api.py        │ ◄── FastAPI Router & CORS
                            └────────────┬───────────┘
                                         │
                 ┌───────────────────────┼────────────────────────┐
                 │ Step 1                │ Step 2                 │ Step 3
                 ▼                       ▼                        ▼
       ┌──────────────────┐    ┌───────────────────┐    ┌──────────────────┐
       │  src/memory.py   │    │src/query_under... │    │ src/retrieval.py │
       │ (SessionMemory)  │    │  (parse_query)    │    │   (retrieve)     │
       │ Pronoun & context│    │ Alias & regex     │    │ Dynamic k-NN &   │
       │ resolution       │    │ extraction        │    │ machine filter   │
       └──────────────────┘    └───────────────────┘    └────────┬─────────┘
                                                                 │
                                                       ┌─────────▼────────┐
                                                       │src/embed_store.py│
                                                       │(SentenceTransf.  │
                                                       │ + ChromaDB)      │
                                                       └─────────┬────────┘
                                                                 │ Chunks
                                         ┌───────────────────────┘
                                         │
                                         ▼ Step 4
                               ┌───────────────────┐
                               │src/disambiguation │ ◄── Ambiguity Check
                               │ (check_ambiguity) │     (cross-machine E-code)
                               └─────────┬─────────┘
                                         │ If unambiguous
                                         ▼ Step 5
                               ┌───────────────────┐
                               │   src/safety.py   │ ◄── 3-Gate Safety Barrier
                               │  (is_sufficient)  │     (Floor, Error Code, Overlap)
                               └─────────┬─────────┘
                                         │ If sufficient
                                         ▼ Step 6
                               ┌───────────────────┐
                               │ src/llm_answer.py │ ◄── Google GenAI SDK
                               │ (generate_answer) │     (Gemini 3.6 Flash)
                               └─────────┬─────────┘     + Second-Line Defense
                                         │
                                         ▼ Step 7 & 8
                         ┌────────────────────────────────┐
                         │ Format Citations & Update      │
                         │ Session Memory (src/api.py)    │
                         └────────────────────────────────┘
```

---

## 2. File-by-File Technical Deep Dive

---

### `src/__init__.py`
- **Location:** [`src/__init__.py`](file:///d:/VCET_Mumbai/src/__init__.py)
- **Role:** Package Marker
- **Summary:**
  Defines the `src` directory as an importable Python package. Ensures that modules such as `src.api`, `src.retrieval`, and `src.safety` can be imported cleanly across test suites, scripts, and production servers without relative path errors.

---

### `src/ingest.py`
- **Location:** [`src/ingest.py`](file:///d:/VCET_Mumbai/src/ingest.py)
- **Role:** Data Ingestion & Boundary-Aware Chunking Pipeline
- **Dependencies:** `os`, `re`

#### Purpose & Architectural Responsibilities:
Standard naive chunking (splitting by fixed character count or token sliding windows) ruins technical manuals by tearing apart error codes, causes, and corrective action steps. `src/ingest.py` implements **structure-aware chunking**: it parses files by logical document boundaries (`SECTION:` markers) and extracts critical metadata tags directly into structured Python dictionaries.

#### Key Functions & Logic:

1. **`load_and_chunk_manuals(manuals_dir="data/manuals") -> List[Dict[str, Any]]`**:
   - **File Filtering:** Scans `manuals_dir` and processes only `.txt` and `.pdf` files.
   - **Global Metadata Extraction:**
     - Uses regex `^MACHINE:\s*(.+)$` and `^MODEL:\s*(.+)$` in multiline mode to capture machine names that apply to the entire document.
   - **Section Splitting:**
     - Uses `re.split(r"(?=SECTION:)", content)` — a positive lookahead regex that splits chunks on `SECTION:` while keeping the `SECTION:` header attached to the following chunk.
   - **Chunk-Level Metadata Resolution:**
     - Extracts section title with `^SECTION:\s*(.+)$` (default: `"General"`).
     - Overrides global machine/model if chunk-specific `MACHINE:` or `MODEL:` tags are encountered within that section.
     - Extracts explicit error codes with `^ERROR CODE:\s*(.+)$`.
     - **Fallback Regex:** If no explicit error code line exists, executes fallback `\b(E\d{3})\b` on the section title to capture error codes embedded in headings (e.g. `"SECTION: E101 Troubleshooting"`).
   - **Chunk Dictionary Schema:**
     ```python
     {
         "text": sec_text,             # Complete section content
         "machine": sec_machine,       # e.g. "CNC-100" or "Unknown"
         "model": sec_model,           # e.g. "MX-7 Precision"
         "manual": filename,           # e.g. "cnc100.txt"
         "section": section_title,     # e.g. "E101 Overview"
         "error_code": error_code      # e.g. "E101" or None
     }
     ```

#### CLI Execution Mode:
When executed as `__main__`, it executes `load_and_chunk_manuals()`, prints total parsed chunk counts, and displays diagnostic text previews for each extracted chunk.

---

### `src/embed_store.py`
- **Location:** [`src/embed_store.py`](file:///d:/VCET_Mumbai/src/embed_store.py)
- **Role:** Local Vector Database & Dense Embedding Interface
- **Dependencies:** `chromadb`, `sentence-transformers` via `chromadb.utils.embedding_functions`, `os`, `typing`

#### Purpose & Architectural Responsibilities:
Manages persistent local vector storage using ChromaDB. Crucially, all embeddings are computed **locally** via `sentence-transformers` using the `all-MiniLM-L6-v2` model. No external network requests or third-party APIs are required for embedding generation or semantic similarity computation.

#### Core Constants & Configuration:
- `model_name="all-MiniLM-L6-v2"`: 384-dimensional dense semantic embedding model.
- `DB_DIR="./chroma_db"`: Local persistent directory for Chroma storage.
- Distance metric: `{"hnsw:space": "cosine"}` configured during collection creation.

#### Key Functions & Logic:

1. **`get_chroma_collection(collection_name: str = "machine_manuals") -> chromadb.Collection`**:
   - Instantiates a persistent Chroma client via `chromadb.PersistentClient(path=DB_DIR)`.
   - Creates or loads the collection using the shared `SentenceTransformerEmbeddingFunction`.

2. **`index_chunks(chunks: List[Dict[str, Any]], collection_name: str = "machine_manuals") -> int`**:
   - Transforms the dictionaries output by `src/ingest.py` into ChromaDB's three primary arrays: `ids`, `documents`, and `metadatas`.
   - Generates deterministic IDs: `f"chunk_{i}_{manual}_{error_code}"`.
   - Populates metadata fields: `machine`, `model`, `manual`, `section`, and `error_code`.
   - Inserts records into the vector index using `collection.add(...)`.

3. **`search(query: str, k: int = 5, filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]`**:
   - Performs k-NN nearest-neighbor search.
   - **Dynamic Metadata Filtering:** Translates `filter_metadata={"machine": "CNC-100"}` into Chroma's `$eq` query filter. Supports multi-key filtering using Chroma's `{"$and": [...]}` syntax.
   - **Distance-to-Similarity Inversion:** Chroma returns cosine distances ($D_{cosine} \in [0, 2]$). This function converts distance to similarity:
     $$\text{sim\_score} = \max(0.0, 1.0 - \text{distance})$$
     This guarantees bounded scores $\in [0.0, 1.0]$ where $1.0$ is an exact semantic match.
   - Standardizes output records with keys: `text`, `machine`, `model`, `manual`, `section`, `error_code`, `score`, `distance`, and `score_type`.

4. **`query_store = search`**:
   - Backward-compatible alias allowing other modules to invoke the vector store via `query_store`.

---

### `src/query_understanding.py`
- **Location:** [`src/query_understanding.py`](file:///d:/VCET_Mumbai/src/query_understanding.py)
- **Role:** Natural Language Intent & Entity Extraction
- **Dependencies:** `re`

#### Purpose & Architectural Responsibilities:
Parses raw technician input to extract operational entities before retrieval. Specifically detects whether the user provided an explicit machine name (or colloquial alias) and whether an alphanumeric industrial error code is present.

#### Key Structures & Logic:

1. **`DEFAULT_KNOWN_MACHINES`**:
   - Reference list: `["CNC-100", "Press-200", "RobotArm-300"]`.

2. **`MACHINE_ALIASES`**:
   - Dictionary mapping colloquial factory slang and shorthand to canonical machine identifiers:
     - `"machine a"`, `"cnc 100"`, `"cnc100"` $\to$ `"CNC-100"`
     - `"machine b"`, `"press 200"`, `"press200"` $\to$ `"Press-200"`
     - `"machine c"`, `"robot arm 300"`, `"robotarm300"` $\to$ `"RobotArm-300"`

3. **`parse_query(query: str, known_machines=None, known_error_codes=None) -> Dict[str, Any]`**:
   - **Machine Extraction:** Case-insensitively checks `MACHINE_ALIASES` first; falls back to matching names in `known_machines`.
   - **Error Code Extraction:** Applies regex `\b(E\d{3})\b` with `re.IGNORECASE` to extract 3-digit standard error codes (e.g. `E101`). Converted to uppercase.
   - **Output Contract:**
     ```python
     {
         "machine": detected_machine,     # str or None
         "error_code": detected_error_code, # str or None
         "raw_query": query              # original query str
     }
     ```

---

### `src/disambiguation.py`
- **Location:** [`src/disambiguation.py`](file:///d:/VCET_Mumbai/src/disambiguation.py)
- **Role:** Cross-Manual Ambiguity Detection & Clarification Dispatcher
- **Dependencies:** Pure Python (no external dependencies)

#### Purpose & Architectural Responsibilities:
In multi-machine manufacturing facilities, the same error code often exists across completely different equipment (e.g. `E101` means "Spindle Coolant Loss" on a CNC mill, but "Motor Overcurrent" on a conveyor). If a technician asks "How do I fix E101?" without specifying the machine, silently guessing would be catastrophic. This module halts execution and produces interactive clarification prompts.

#### Key Functions & Logic:

1. **`check_ambiguity(parsed_query, retrieved_chunks) -> Dict[str, Any]`**:
   - **Fast Bail-Out:**
     - If `parsed_query["machine"]` is already present, the query is unambiguous $\to$ returns `{"ambiguous": False, "options": []}`.
     - If no `error_code` was extracted, cross-code ambiguity does not apply $\to$ returns `{"ambiguous": False, "options": []}`.
   - **Cross-Machine Grouping:**
     - Iterates through `retrieved_chunks`. Filters for chunks where `chunk["error_code"] == error_code`.
     - Groups unique machines and extracts a short human-readable summary of the error code on each machine by inspecting `MEANING:` or `SECTION:` lines in the chunk text.
   - **Ambiguity Decision:**
     - If $\ge 2$ distinct machines are matched for that error code:
       Returns `{"ambiguous": True, "options": [{"machine": ..., "summary": ...}, ...]}`.
     - Otherwise returns `{"ambiguous": False, "options": []}`.

---

### `src/retrieval.py`
- **Location:** [`src/retrieval.py`](file:///d:/VCET_Mumbai/src/retrieval.py)
- **Role:** Retrieval Coordinator & Search Strategy Builder
- **Dependencies:** [`src/embed_store.py`](file:///d:/VCET_Mumbai/src/embed_store.py)

#### Purpose & Architectural Responsibilities:
Coordinates vector retrieval based on entities identified by query understanding. It applies hard metadata filters when the machine is known and augments semantic search strings with error codes when necessary.

#### Key Functions & Logic:

1. **`retrieve(parsed_query: Dict[str, Any], k: int = 5) -> List[Dict[str, Any]]`**:
   - **Query String Augmentation:** If an `error_code` was extracted but is not explicitly in `raw_query`, prefixes it to the search text (`f"{error_code} {raw_query}"`) to bolster token weighting.
   - **Scoped Filtering:** If `parsed_query["machine"]` is present, passes `filter_metadata={"machine": machine}` to `search()`, preventing irrelevant chunks from competing for top-$k$.
   - Returns top-$k$ chunks enriched with similarity scores and metadata.

---

### `src/safety.py`
- **Location:** [`src/safety.py`](file:///d:/VCET_Mumbai/src/safety.py)
- **Role:** Deterministic Pre-LLM Hallucination Barrier (Three-Gate Safety System)
- **Dependencies:** `re`

#### Purpose & Architectural Responsibilities:
This is the core anti-hallucination layer. Before any text is passed to an LLM, `safety.py` deterministically checks whether the retrieved documentation actually supports answering the question. If evidence is insufficient, it refuses immediately without invoking the LLM, achieving zero hallucinations and saving API costs.

#### Key Structures & Logic:

1. **`REFUSAL_MESSAGE` Constant:**
   ```python
   REFUSAL_MESSAGE = "The available manuals do not provide sufficient information to answer this. I won't provide an unsupported answer."
   ```
   A fixed constant returned across all refusal pathways to ensure exact API contract compliance.

2. **`STOPWORDS` & `MACHINE_PATTERNS`**:
   - Standard stopwords plus domain stopwords (`"machine"`, `"manual"`, `"section"`).
   - Machine tokens (`"cnc"`, `"press"`, `"robotarm"`, `"100"`, `"200"`, `"300"`, etc.) are filtered out so that merely mentioning the machine name does not trick the overlap calculator into believing content was matched.

3. **`_extract_content_tokens(text: str) -> Set[str]`**:
   - Tokenizes text, removes stopwords and machine tokens, splits hyphenated words, and returns a set of normalized content keywords.

4. **`is_sufficient(retrieved_chunks, query="", threshold=0.35) -> Tuple[bool, Any]`**:
   - **Gate 1 — Score Floor:**
     $$\text{score}_{\text{top}} \ge 0.35$$
     If top chunk similarity is $< 0.35$ or no chunks are returned, immediate refusal.
   - **Gate 2 — Explicit Error Code Verification:**
     - If the user query contains an error code (e.g. `E101`, `E999`), that exact code **must exist** in the top 3 retrieved chunks.
     - Prevents answering unindexed error codes or cross-machine code mismatches.
   - **Gate 3 — Hybrid Semantic / Keyword Overlap Gate:**
     - **High Semantic Similarity ($\ge 0.50$):** Automatically passes. Trusted as a valid semantic match or paraphrase (e.g., "drive motor is running hot" matching "Excessive motor temperature").
     - **Borderline Similarity ($0.35 \le \text{score} < 0.50$):** Requires at least **40% query content token overlap** in the retrieved chunks:
       $$\frac{|\text{Query Tokens} \cap \text{Chunk Tokens}|}{|\text{Query Tokens}|} \ge 0.40$$
       Filters out incidental semantic drift where a single unrelated word (e.g. "bearing" in "spindle bearing") produces a borderline score against general maintenance text.
   - **Return Signature:** Returns `(True, retrieved_chunks)` on pass; `(False, REFUSAL_MESSAGE)` on fail.

---

### `src/memory.py`
- **Location:** [`src/memory.py`](file:///d:/VCET_Mumbai/src/memory.py)
- **Role:** Stateful Multi-Turn Conversation Memory
- **Dependencies:** `re`

#### Purpose & Architectural Responsibilities:
Enables contextual technician dialogues (e.g., Turn 1: "What does E101 mean on CNC-100?", Turn 2: "What if that doesn't work?"). Maintains session-isolated history in memory and resolves vague pronouns before query understanding and retrieval.

#### Key Classes & Methods:

1. **`SessionMemory`**:
   - **`self.sessions`**: Dictionary keyed by `session_id`.
   - **`get_session(session_id)`**: Initializes or fetches a session state dictionary:
     ```python
     {
         "last_machine": None,
         "last_error_code": None,
         "last_answer": None
     }
     ```
   - **`update_session(session_id, machine=None, error_code=None, last_answer=None)`**: Updates session variables after an answer is generated.
   - **`resolve_query_with_memory(session_id, query) -> str`**:
     - Scans `query` for vague terms: `["that", "it", "this", "what if", "how about"]`.
     - If vague terms are detected, checks if the query already mentions the machine or error code.
     - Injects missing context:
       ```python
       f"{query} (regarding machine {last_m} error code {last_e})"
       ```
     - Enables downstream modules (`query_understanding`, `retrieval`) to operate as if the technician typed a fully specified query.

2. **`memory_store = SessionMemory()`**:
   - Module-level singleton instance shared across requests.

---

### `src/llm_answer.py`
- **Location:** [`src/llm_answer.py`](file:///d:/VCET_Mumbai/src/llm_answer.py)
- **Role:** LLM Prompt Assembly, Generation & Second-Line Defense
- **Dependencies:** `os`, `dotenv`, `google.genai`, [`src.safety.py`](file:///d:/VCET_Mumbai/src/safety.py)

#### Purpose & Architectural Responsibilities:
Communicates with Google's Gemini LLM (`gemini-3.6-flash`) using the modern `google-genai` SDK. It formats grounded context, enforces a four-section response schema, and implements a second-line defense where the LLM itself refuses to answer if the context does not contain the specific answer.

#### Key Functions & Logic:

1. **`SYSTEM_PROMPT`**:
   - Instructs the model to act as `MachineAssist`.
   - Mandates answering using **ONLY** provided manual sources.
   - Enforces 4 structured headings:
     1. `Error meaning`
     2. `Probable causes`
     3. `Step-by-step corrective action`
     4. `Sources`
   - Explicitly commands: If sources do NOT contain sufficient information, output **ONLY** the exact `REFUSAL_MESSAGE`.

2. **`assemble_context(chunks: List[Dict[str, Any]]) -> str`**:
   - Formats chunks into clean, labeled citation blocks:
     ```
     [Source 1]
     Machine: CNC-100
     Manual: cnc100.txt
     Section: E101 Troubleshooting
     
     <Text content>
     ---
     ```

3. **`generate_answer(query: str, context: str, api_key=None) -> str`**:
   - **Environment Loading:** Reads `GEMINI_API_KEY` via `load_dotenv(override=True)`.
   - **Fallback Placeholder:** If no API key is provided, returns a structured offline template rather than crashing.
   - **Client Execution:** Instantiates `genai.Client(api_key=api_key)`.
   - **Retry Loop:** Implements a 3-attempt loop with `time.sleep(5)` specifically intercepting `429` / `RESOURCE_EXHAUSTED` errors.
   - **Safety & Completion Checks:**
     - Verifies `response.candidates` is non-empty.
     - Inspects `candidate.finish_reason`: normal completion (`STOP = 1`) accepted; safety blocks or abnormal stops return `REFUSAL_MESSAGE`.
     - Checks `response.text` safely with exception handling for empty response parts.
   - **Fail-Closed Architecture:** Outer `except Exception` ensures that network timeouts, quota limits, or API crashes always default safely to `REFUSAL_MESSAGE`.

---

### `src/api.py`
- **Location:** [`src/api.py`](file:///d:/VCET_Mumbai/src/api.py)
- **Role:** FastAPI HTTP Application & Orchestration Controller
- **Dependencies:** `fastapi`, `pydantic`, `src.*` modules

#### Purpose & Architectural Responsibilities:
The primary HTTP entry point for web browsers, React frontends, and API clients. Orchestrates the execution sequence across all 8 pipeline phases, validates schemas via Pydantic, and returns JSON responses.

#### Pydantic Data Models:
- `QueryRequest`:
  - `message: str`
  - `session_id: str = "default_session"`
- `SourceMetadata`:
  - `manual: str`, `section: str`, `machine: str`, `error_code: Optional[str]`
- `AmbiguityOption`:
  - `machine: str`, `summary: str`
- `QueryResponse`:
  - `answer: str`
  - `sources: List[SourceMetadata]`
  - `ambiguous: bool`
  - `options: List[AmbiguityOption]`

#### Routes & Orchestration Flow:

1. **`GET /`**: Health-check endpoint returning `{"message": "MachineAssist Backend API running", "status": "ok"}`.
2. **`GET /machines`**: Returns known machine list (`DEFAULT_KNOWN_MACHINES`) for frontend dropdown menus.
3. **`POST /query` (The Master Controller)**:
   - **Validation:** Rejects empty or whitespace-only messages with `HTTP 400`.
   - **Step 1:** Resolves query pronouns via `memory_store.resolve_query_with_memory(session_id, raw_message)`.
   - **Step 2:** Parses machine and error code via `parse_query(augmented_message)`.
   - **Step 3:** Fetches top chunks via `retrieve(parsed_q, k=5)`.
   - **Step 4:** Evaluates `check_ambiguity(...)`. If ambiguous, short-circuits immediately with `ambiguous=True` and available options.
   - **Step 5:** Evaluates deterministic safety barrier `is_sufficient(...)`. If insufficient, short-circuits with `REFUSAL_MESSAGE` and empty sources.
   - **Step 6:** Assembles context and invokes `generate_answer(raw_message, context_text)`.
   - **Step 7 (No Phantom Citations):** Deduplicates source citations. Crucially, if the LLM self-refused (second-line defense), `sources` is cleared to `[]`.
   - **Step 8:** Updates `memory_store` with the current machine, error code, and answer text.
   - Returns structured `QueryResponse`.

---

### `tests/test_all_demos.py`
- **Location:** [`tests/test_all_demos.py`](file:///d:/VCET_Mumbai/tests/test_all_demos.py)
- **Role:** End-to-End Live Demo Validation Script
- **Dependencies:** `fastapi.testclient.TestClient`, [`src.api.app`](file:///d:/VCET_Mumbai/src/api.py)

#### Purpose & Architectural Responsibilities:
A standalone executable script used for rapid visual smoke-testing across the 5 core demo categories:
1. **Demo 1 (Exact Code):** `"What does E101 mean on CNC-100?"` $\to$ Validates non-ambiguous answer with manual citations.
2. **Demo 2 (Symptom):** `"Why does Press-200 show hydraulic oil pressure low?"` $\to$ Validates semantic retrieval without error codes.
3. **Demo 3 (Ambiguity):** `"What does E101 mean?"` $\to$ Validates `ambiguous=True` and multi-machine selection options.
4. **Demo 4 (First-Line Refusal):** `"How do I replace spindle bearing on CNC-100?"` $\to$ Validates Gate 3 pre-filter refusal on undocumented maintenance.
5. **Demo 5 (Second-Line Refusal):** `"What is the exact electrical torque specification for resetting E101 motor on CNC-100?"` $\to$ Validates LLM self-refusal when general E101 context is present but specific torque specs are absent.

---

### `tests/test_rigorous.py`
- **Location:** [`tests/test_rigorous.py`](file:///d:/VCET_Mumbai/tests/test_rigorous.py)
- **Role:** Comprehensive Pytest Regression Suite (63 Tests)
- **Dependencies:** `pytest`, `starlette.testclient.TestClient`, all `src.*` modules

#### Purpose & Architectural Responsibilities:
The formal regression test suite for MachineAssist. Contains 63 tests split into 57 fast unit tests (zero LLM calls, mocked chunk dicts) and 6 slow integration tests (invoking the live Gemini API).

#### Layer Breakdown & Classes:

1. **`TestSafetyGates` (15 fast tests):**
   - Tests Gate 1 score boundary flips at exactly $0.35$.
   - Tests Gate 2 error code verification (rejects unindexed codes like `E999`, machine mismatches, malformed two-digit codes like `E10`, and OCR errors like `E1O1`).
   - Tests Gate 3 semantic bypass (score $\ge 0.50$) vs. borderline overlap requirement (score $0.42$ with $< 40\%$ overlap rejected; $\ge 40\%$ accepted).
   - Validates that all refusal paths return byte-identical `REFUSAL_MESSAGE`.

2. **`TestDisambiguation` (8 fast tests):**
   - Tests multi-machine detection when `machine` is `None`.
   - Tests that explicitly specifying a machine suppresses ambiguity flags.
   - Tests summary extraction from `MEANING:` and `SECTION:` lines.
   - Tests single-machine error code queries.

3. **`TestQueryUnderstanding` (16 fast tests):**
   - Tests alias mapping (`"machine a"` $\to$ `"CNC-100"`, `"press200"` $\to$ `"Press-200"`).
   - Tests punctuation, casing, and symbol variations.
   - Tests regex boundary extraction of error codes.

4. **`TestMemory` (7 fast tests):**
   - Tests pronoun resolution (`"that"`, `"it"`, `"what if that doesn't work"`).
   - Tests session isolation across different `session_id` UUIDs.
   - Tests multi-turn conversation context augmentation.

5. **`TestLLMRefusal` (6 slow tests, marked with `@pytest.mark.slow`):**
   - Tests second-line LLM self-refusal against adversarial queries (e.g. asking for unmentioned torque specs or unmentioned wire gauge specs).
   - Includes positive control `test_llm_answers_genuinely_sufficient_context`.

6. **`TestAPIContract` (11 fast tests):**
   - Tests FastAPI response shapes, CORS headers, Pydantic field schemas, empty query handling, and invariant source-clearing on refusal.

---

### `write_tests.py`
- **Location:** [`write_tests.py`](file:///d:/VCET_Mumbai/write_tests.py)
- **Role:** Developer Utility Script
- **Summary:**
  A utility helper script in the workspace root used for test scaffold generation.

---

## 3. Data Flow Traces for Core Scenarios

### Trace A: Disambiguation Trigger
1. **Technician Query:** `"What does E101 mean?"`
2. `src/api.py`: Calls `parse_query("What does E101 mean?")` $\to$ `{"machine": None, "error_code": "E101"}`.
3. `src/retrieval.py`: Searches vector DB without machine filter; retrieves chunks from both `CNC-100` and `Press-200`.
4. `src/disambiguation.py`: Detects `E101` matching 2 distinct machines without a specified machine.
5. `src/api.py`: Returns `ambiguous=True` with options for `CNC-100` and `Press-200`. **Pipeline halts; LLM is never called.**

### Trace B: Undocumented Question (Safety Pre-Filter Refusal)
1. **Technician Query:** `"How do I replace the spindle bearing on CNC-100?"`
2. `src/api.py`: Calls `parse_query(...)` $\to$ `{"machine": "CNC-100", "error_code": None}`.
3. `src/retrieval.py`: Searches vector DB scoped to `CNC-100`. Top chunk is general maintenance with similarity score $0.41$.
4. `src/safety.py`:
   - Gate 1: $0.41 \ge 0.35$ (Passes floor).
   - Gate 2: No error code in query (Skipped).
   - Gate 3: Score $< 0.50$ (Borderline). Content tokens: `{"replace", "spindle", "bearing"}`. Retrieved chunk only contains the word `"spindle"`. Overlap ratio = $1/3 \approx 33.3\% < 40\%$.
   - **Gate 3 FAILS.**
5. `src/api.py`: Returns `REFUSAL_MESSAGE` and `sources=[]`. **Zero hallucination; LLM is never called.**

### Trace C: Second-Line Defense (Pre-Filter Bypass Refusal)
1. **Technician Query:** `"What is the exact electrical torque specification for resetting E101 motor on CNC-100?"`
2. `src/safety.py`: E101 matches the chunk, score $\ge 0.50$ $\to$ Passes pre-filter.
3. `src/llm_answer.py`: Context is assembled and sent to Gemini 3.6 Flash.
4. Gemini inspects the manual excerpt. The excerpt explains causes and corrective steps, but contains **no torque specs**.
5. Gemini follows `SYSTEM_PROMPT` constraint and responds with `REFUSAL_MESSAGE`.
6. `src/api.py`: Detects refusal in LLM response, clears `sources` to `[]` to prevent phantom citations, and returns response to user.
