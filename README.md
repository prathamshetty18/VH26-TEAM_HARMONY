# MachineAssist — RAG-Based Intelligent Machine Troubleshooting System

A retrieval-augmented troubleshooting assistant for factory technicians. It ingests multiple machine manuals, resolves conflicting/overlapping error codes across machines, retrieves the right information with citations, and refuses to answer when the manuals don't support an answer.

This is **not** a basic "chat with PDF" app. It is explicitly designed to handle:
- The same error code meaning different things across different machines
- Ambiguous queries that need clarification before answering
- Hallucination control — never inventing a troubleshooting step that isn't documented
- Full traceability: every answer cites manual, section, and page

## Tech Stack

| Component | Choice |
|---|---|
| Language | Python 3.10+ |
| PDF/text ingestion | `pypdf` |
| Orchestration | `langchain` |
| Embeddings | `sentence-transformers` (local, free, no API key — e.g. `all-MiniLM-L6-v2`) |
| Vector DB | Chroma (local, file-based) |
| LLM | Claude or GPT via API |
| Backend API | FastAPI (serves the pipeline to the frontend over HTTP) |
| Frontend UI | React (built separately by another teammate — see "Frontend integration" below) |

Note: embeddings are local (sentence-transformers), but the LLM generation step (Phase 7) still needs an API key (Claude or GPT) since generation quality matters more than embedding quality here.

## Project Structure

```
machineassist/
├── data/
│   └── manuals/              # source manuals (txt/pdf), one per machine
├── src/
│   ├── ingest.py             # Phase 1: load + chunk + metadata tagging
│   ├── embed_store.py        # Phase 2: sentence-transformers embeddings + Chroma vector store
│   ├── query_understanding.py# Phase 3: extract machine/error_code from query
│   ├── retrieval.py          # Phase 3: filtered + scored retrieval
│   ├── disambiguation.py     # Phase 4: detect + resolve ambiguous queries
│   ├── safety.py             # Phase 5: relevance threshold / insufficient-info check
│   ├── memory.py             # Phase 6: conversation state (last machine/error)
│   ├── llm_answer.py         # Phase 7: context assembly + prompted generation
│   └── api.py                # Phase 8: FastAPI backend, exposes the pipeline over HTTP
├── frontend/                  # React app — built separately, see "Frontend integration"
├── tests/
│   └── demo_queries.md       # the 4 required demo scripts + expected behavior
├── DESIGN.md                 # full phased build plan for the IDE/agent to follow
├── requirements.txt
└── README.md
```

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...    # or OPENAI_API_KEY — only needed for LLM generation, not embeddings
```

`sentence-transformers` will download its model (e.g. `all-MiniLM-L6-v2`) automatically on first run — no API key required for embeddings.

## Running

```bash
uvicorn src.api:app --reload --port 8000
```

This starts the backend API. The React frontend (in `frontend/`) runs separately and calls this API — see "Frontend integration" below.

## Frontend integration

The frontend is a separate React app, built by another teammate, that talks to the Python backend over HTTP. To keep the two sides decoupled and easy to build in parallel:

- The backend (`src/api.py`) should expose a small number of simple JSON endpoints, for example:
  - `POST /query` — body: `{"message": "...", "session_id": "..."}` → returns `{"answer": "...", "sources": [...], "ambiguous": false, "options": []}`
  - `GET /machines` — returns the list of known machines, for populating a dropdown in the UI
- `session_id` lets the backend track conversation memory (Phase 6) per user/tab without the frontend needing to manage any RAG state itself
- Enable CORS in FastAPI so the React dev server (typically `localhost:3000` or `5173`) can call the backend (typically `localhost:8000`) during development
- Agree on the exact JSON shape above with your frontend teammate early — once it's fixed, you can build the backend and frontend fully in parallel

## How to build this

See **DESIGN.md**. It breaks the system into sequential phases (Phase 0 → Phase 8). Each phase is self-contained, has a clear acceptance test, and should be fully working before moving to the next phase. Do not skip ahead — each phase depends on the previous one being correct. If you are an IDE agent building this: implement one phase, verify its acceptance criteria, then stop and move to the next phase.

## The 4 required demo cases

1. **Exact error code** — `E101` → correct machine-specific answer, or clarification if ambiguous
2. **Natural language symptom** — "why is Machine A overheating?" → semantic retrieval finds the right chunk despite no exact keyword match
3. **Cross-manual ambiguity** — `E101` with no machine specified, where 2+ machines define it differently → system asks which machine instead of guessing
4. **Insufficient information** — a question with no documented answer → system explicitly says the manuals don't cover it, and does not invent an answer

See `tests/demo_queries.md` for the exact scripted queries once Phase 1 data is authored.
