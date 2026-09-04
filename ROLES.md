# ROLES.md — Team Assignments for MachineAssist

Team of 4. Roles are split so that everyone has clear ownership and can work in parallel without blocking each other. All code merges go through you (main coder) — teammates push to their own branches, you review and merge.

---

## You — Lead Coder / Backend & Integration

**Owns:** everything in `src/` (Phases 0–8 in DESIGN.md), the RAG pipeline, the FastAPI backend, and final integration of all pieces (backend + React frontend + manuals + prompt text).

**Responsibilities:**
- Build ingestion, chunking, embeddings, retrieval, disambiguation, safety checks, memory, and the `/query` and `/machines` API endpoints
- Define and communicate the API's request/response JSON shape to the frontend teammate early (Phase 8 in DESIGN.md has the exact shape)
- Review and merge all teammate contributions (manual files, prompt text, frontend PRs)
- Own the final working demo build

---

## Teammate A — Frontend Developer (React)

**Owns:** `frontend/` — the React chat UI that calls your backend.

**Responsibilities:**
- Build a chat-style interface: message history, text input, a machine dropdown (populated from `GET /machines`), and a citations/sources display under each answer
- Call `POST /query` with `{message, session_id}` and render the response (`answer`, `sources`, `ambiguous`, `options`)
- When `ambiguous: true`, render the `options` as clickable choices (e.g. buttons for "Machine A" / "Machine B") rather than plain text
- Generate and persist a `session_id` per browser tab/session so follow-up questions carry context

**Simple tasks to start immediately (don't need the backend running yet):**
- Build the UI with mocked/hardcoded JSON responses matching the agreed shape, so frontend work isn't blocked waiting on the backend
- Design the layout for how citations should visually appear (e.g. small cards under each answer with manual name + page)

---

## Teammate B — Manual Author & Data / Testing

**Owns:** `data/manuals/` content and ongoing testing of the running system.

**Responsibilities:**
- Write the 3-4 fake manual text files per Phase 1 in DESIGN.md, using the required consistent heading structure (`MACHINE:`, `ERROR CODE:`, `SECTION:`, `CAUSES:`, `STEPS:`)
- Deliberately create the overlapping-error-code scenario (same code, 2+ machines, different meaning) and the deliberately undocumented topic
- Once any version of the backend is running, test it via the FastAPI `/docs` page or `curl` — no coding needed, just typing queries and reporting what breaks
- Keep a running log (a simple text/Markdown file) of "query tried → expected result → actual result" for all 4 demo types

**Simple tasks that can start immediately:**
- Manual writing can start on day one, in parallel with your Phase 0 setup — this is the biggest single time sink if left too late, so front-load it
- Once manuals exist, this teammate can also propose the exact 10-15 test queries per demo type (feeds directly into `tests/demo_queries.md`)

---

## Teammate C — Prompt/UX Writer & Pitch Lead

**Owns:** the wording layer of the product and the final presentation.

**Responsibilities:**
- Draft the LLM system prompt wording (Phase 7 in DESIGN.md already has a starting version — this teammate refines the tone and structure once real answers start coming back)
- Write the exact copy for: the ambiguity clarification message, the "insufficient information" refusal message, and how source citations should read to a technician (plain and clear, not robotic)
- Build the slide deck: problem statement, why it's hard, what makes this solution different (lead with cross-manual disambiguation and hallucination control)
- Script the live demo order — which query to type for each of the 4 required demos, in a sequence that flows naturally for judges
- Near the end, rehearse the live demo (can pair with Teammate B, who knows exactly which queries reliably work)

**Simple tasks that can start immediately:**
- Prompt and message wording can be drafted against the *example* outputs already written in DESIGN.md, before the backend is even running — you swap in the real wording once generation is live
- Deck skeleton and narrative structure can be built in parallel from day one, filled in with real screenshots later

---

## Workflow & Git

- Everyone works on their own branch (`frontend`, `data`, `prompts-pitch`) and opens a PR into `main`
- You review and merge all PRs — this keeps the backend pipeline consistent and avoids conflicting changes to shared files (like the manual format or the API contract)
- Agree on the API JSON shape (Phase 8, DESIGN.md) with Teammate A **before** either of you starts building, so backend and frontend can proceed fully in parallel without waiting on each other
- Teammate B's manuals and Teammate C's prompt wording are just text files — low risk of merge conflicts, safe to iterate on continuously

## Suggested timeline

| Hours | You | Teammate A (Frontend) | Teammate B (Manuals/Test) | Teammate C (Prompt/Pitch) |
|---|---|---|---|---|
| 0–2 | Env setup, Phase 0 | Scaffold React app, mock data | Start writing manuals | Draft prompt v1, deck outline |
| 2–10 | Phases 1–4 (ingest, embed, retrieval, query understanding) using B's manuals | Build chat UI against mocked responses | Finish manuals, start testing as soon as backend runs | Refine prompt wording against early real outputs |
| 10–18 | Phases 5–8 (disambiguation, safety, memory, API) | Wire real API calls in, handle ambiguous/insufficient states in UI | Stress-test all 4 demo types, log bugs | Finalize refusal/clarification copy, lock demo script |
| 18–24 | Bug fixes, final integration | Polish UI, citation display | Full rehearsal, drive live demo queries | Lead pitch delivery |
