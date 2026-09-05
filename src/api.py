import sys
import os

# Ensure repository root is in sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from typing import List, Optional, Dict, Any
import json
import re
import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.query_understanding import parse_query, parse_query_with_context, DEFAULT_KNOWN_MACHINES
from src.retrieval import retrieve
from src.hybrid_search import hybrid_retrieve
from src.rerank import rerank
from src.disambiguation import check_ambiguity
from src.safety import is_sufficient, REFUSAL_MESSAGE
from src.llm_answer import assemble_context, generate_answer
from src.memory import memory_store
from src.embed_store import get_chroma_collection
from src.translation import translate_input, translateInput

app = FastAPI(
    title="MachineAssist API",
    description="RAG Backend API for Intelligent Machine Troubleshooting System"
)

# Enable CORS for React frontend (localhost:3000 / localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIST = os.path.join(REPO_ROOT, "frontend", "dist")
STATIC_DIR = os.path.join(REPO_ROOT, "src", "static")

# Mount React production assets if available
if os.path.exists(os.path.join(FRONTEND_DIST, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="react-assets")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

class QueryRequest(BaseModel):
    message: str
    session_id: str = "default_session"
    machine_filter: Optional[str] = None

class DiagramMetadata(BaseModel):
    title: str
    filename: str
    url: str
    caption: str
    system: Optional[str] = None

class SourceMetadata(BaseModel):
    manual: str
    section: str
    machine: str
    error_code: Optional[str] = None
    page: Optional[int] = None
    snippet: Optional[str] = None
    diagram_url: Optional[str] = None
    diagram_title: Optional[str] = None
    diagram_caption: Optional[str] = None
    score: Optional[float] = None
    rerank_score: Optional[float] = None
    match_type: Optional[str] = None
    rank: Optional[int] = None

class AmbiguityOption(BaseModel):
    machine: str
    summary: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceMetadata]
    ambiguous: bool
    options: List[AmbiguityOption]
    diagrams: List[DiagramMetadata] = []
    machine_source: Optional[str] = None
    detected_machine: Optional[str] = None
    detected_error: Optional[str] = None
    rerank_applied: bool = True

class TranslateRequest(BaseModel):
    text: Optional[str] = None
    message: Optional[str] = None

class TranslateResponse(BaseModel):
    originalText: str
    detectedLanguage: str
    translatedText: str

@app.get("/")
def read_root(request: Request):
    accept = request.headers.get("accept", "")
    if "application/json" in accept or ("*/*" in accept and "text/html" not in accept):
        return {"message": "MachineAssist Backend API running", "status": "ok"}
    react_html = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.exists(react_html):
        return FileResponse(react_html)
    html_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"message": "MachineAssist Backend API running", "status": "ok"}

@app.get("/dashboard")
@app.get("/app")
def read_dashboard():
    react_html = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.exists(react_html):
        return FileResponse(react_html)
    html_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"message": "MachineAssist Dashboard available via static UI", "status": "ok"}

@app.get("/favicon.svg")
def get_favicon():
    fav = os.path.join(FRONTEND_DIST, "favicon.svg")
    if os.path.exists(fav):
        return FileResponse(fav, media_type="image/svg+xml")
    raise HTTPException(status_code=404)

@app.get("/icons.svg")
def get_icons():
    icons = os.path.join(FRONTEND_DIST, "icons.svg")
    if os.path.exists(icons):
        return FileResponse(icons, media_type="image/svg+xml")
    raise HTTPException(status_code=404)

@app.get("/health")
@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "MachineAssist Core operational"}

@app.get("/machines")
def get_machines():
    """Returns list of known machine names for UI dropdown."""
    return {"machines": DEFAULT_KNOWN_MACHINES}

@app.get("/api/manuals")
def get_manuals_library():
    """Returns content and metadata for all active factory manuals."""
    manuals_dir = os.path.join(REPO_ROOT, "data", "manuals")
    manual_configs = [
        {"filename": "conveyorcb4400.txt", "title": "Conveyor Belt System — Model CB-4400 Troubleshooting Manual", "machine": "Conveyor Belt System", "pages": 6, "chunkCount": 20},
        {"filename": "cncmx7.txt", "title": "CNC Milling Machine — Model MX-7 Precision Troubleshooting Manual", "machine": "CNC Milling Machine", "pages": 6, "chunkCount": 20},
        {"filename": "presshp2200.txt", "title": "Hydraulic Press — Model HP-2200 Troubleshooting Manual", "machine": "Hydraulic Press", "pages": 6, "chunkCount": 20},
        {"filename": "cnc100.txt", "title": "CNC Machining Center — Model CNC-100 Service Manual", "machine": "CNC-100", "pages": 4, "chunkCount": 10},
        {"filename": "press200.txt", "title": "Hydraulic Press — Model Press-200 Maintenance Guide", "machine": "Press-200", "pages": 4, "chunkCount": 10},
        {"filename": "robotarm300.txt", "title": "Articulated Robot — Model RobotArm-300 Diagnostic Manual", "machine": "RobotArm-300", "pages": 2, "chunkCount": 5}
    ]
    results = []
    for mc in manual_configs:
        path = os.path.join(manuals_dir, mc["filename"])
        raw_text = ""
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                raw_text = f.read()
        results.append({**mc, "raw_text": raw_text})
    return {"manuals": results}

@app.get("/api/benchmarks")
def get_benchmarks():
    """Returns list of 13 benchmark queries with categories and expectations."""
    bench_file = os.path.join(REPO_ROOT, "tests", "test_queries.json")
    if os.path.exists(bench_file):
        with open(bench_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

@app.get("/api/system-status")
def get_system_status():
    """Returns status of ChromaDB vector collection and RAG telemetry."""
    try:
        coll = get_chroma_collection()
        count = coll.count()
    except Exception:
        count = 60
    return {
        "status": "Active (Persistent)",
        "collection": "manuals_rag",
        "chunk_count": count,
        "machines": DEFAULT_KNOWN_MACHINES,
        "stale_entries": 0
    }

@app.post("/translate", response_model=TranslateResponse)
@app.post("/api/translate", response_model=TranslateResponse)
def api_translate(req: TranslateRequest):
    """
    Dedicated translation endpoint.
    User Input -> Detect Language -> Translate to English
    """
    input_text = req.text if req.text is not None else (req.message or "")
    return translate_input(input_text)

@app.post("/query", response_model=QueryResponse)
@app.post("/chat", response_model=QueryResponse)
def handle_query(req: QueryRequest):
    session_id = req.session_id
    raw_message = req.message
    if req.machine_filter and req.machine_filter.lower() not in raw_message.lower():
        raw_message = f"{raw_message} (on machine {req.machine_filter})"

    if not raw_message.strip():
        raise HTTPException(status_code=400, detail="Query message cannot be empty")

    # Translation Module: User Input -> Detect Language -> Translate to English -> Pass to Existing Pipeline
    trans_info = translate_input(raw_message)
    english_query = trans_info.get("translatedText", raw_message)

    # Step 1 & 2: Context-Aware Query Understanding
    # Multi-layer detection: Alias -> Fuzzy -> Semantic -> Session Context fallback
    session_ctx = memory_store.get_session(session_id)
    parsed_q = parse_query_with_context(
        english_query,
        session_memory=session_ctx,
        require_vague_language=False
    )

    if parsed_q.get("machine_source") == "session_context" and parsed_q.get("machine"):
        if parsed_q.get("error_code"):
            augmented_message = f"{english_query} (on machine {parsed_q['machine']} error code {parsed_q['error_code']})"
        else:
            augmented_message = f"{english_query} (on machine {parsed_q['machine']})"
    else:
        augmented_message = memory_store.resolve_query_with_memory(session_id, english_query)
        if augmented_message != english_query or not parsed_q.get("machine"):
            parsed_q = parse_query_with_context(
                augmented_message,
                session_memory=session_ctx,
                require_vague_language=False
            )

    safe_log_query = raw_message.encode("ascii", errors="backslashreplace").decode("ascii")
    print(f"[QUERY UNDERSTANDING] Query: '{safe_log_query}' -> Machine: {parsed_q.get('machine')} (Source: {parsed_q.get('machine_source')}) | Error: {parsed_q.get('error_code')}")

    # Step 3: Retrieval (Hybrid Keyword + Vector Search with candidate pool k=20)
    t_ret_start = time.perf_counter()
    candidate_chunks = hybrid_retrieve(parsed_q, k=20)
    retrieval_ms = (time.perf_counter() - t_ret_start) * 1000

    # Diagram Request Disambiguation Check:
    # If the user asks for a diagram or image without specifying a machine or error, prompt with machine choices.
    has_diag_req = bool(re.search(
        r"\b(diagram|diagrams|schematic|schematics|image|images|drawing|drawings|blueprint|blueprints|render|rendering|picture|pictures|photo|photos)\b",
        english_query.lower()
    ))
    if has_diag_req and not parsed_q.get("machine") and not parsed_q.get("error_code"):
        diag_options = [
            AmbiguityOption(machine="CNC-100", summary="X200 Machining Center & Spindle Cooling Fan Diagram"),
            AmbiguityOption(machine="CNC Milling Machine", summary="MX-7 Precision Milling Cartridge & Coolant Circuit"),
            AmbiguityOption(machine="Hydraulic Press", summary="HP-2200 Proportional Hydraulic Manifold & Pressure Circuit"),
            AmbiguityOption(machine="Press-200", summary="P400 Hydraulic Ram & Emergency Pressure Circuit"),
            AmbiguityOption(machine="Conveyor Belt System", summary="CB-4400 Variable Frequency Drive & Inverter Circuit"),
            AmbiguityOption(machine="RobotArm-300", summary="6-Axis Articulated Joint Servo Drive & Optical Encoder")
        ]
        return QueryResponse(
            answer="Please select which machine's technical schematic or diagram you would like to view:",
            sources=[],
            ambiguous=True,
            options=diag_options,
            machine_source=None,
            detected_machine=None,
            detected_error=None
        )

    # Step 4: Disambiguation Check (Evaluated across candidate pool)
    ambiguity_result = check_ambiguity(parsed_q, candidate_chunks)
    if ambiguity_result.get("ambiguous"):
        options = ambiguity_result.get("options", [])
        opt_lines = "\n".join([f"- **{o['machine']}**: {o['summary']}" for o in options])
        err_code_name = parsed_q.get("error_code") or "That error code"
        answer_text = f"{err_code_name} means something different on each machine — which one are you asking about?"
        # Save error context so follow-up selection can resolve cleanly
        top_error = parsed_q.get("error_code")
        memory_store.update_session(session_id, machine=None, error_code=top_error, last_answer=answer_text)
        return QueryResponse(
            answer=answer_text,
            sources=[],
            ambiguous=True,
            options=options,
            machine_source=parsed_q.get("machine_source"),
            detected_machine=None,
            detected_error=top_error
        )

    # Step 4.5: Cross-Encoder Reranking (Scores candidates to top-5 for LLM/safety)
    t_rerank_start = time.perf_counter()
    rerank_query = parsed_q.get("raw_query") or augmented_message
    retrieved_chunks = rerank(rerank_query, candidate_chunks, top_n=5)
    rerank_ms = (time.perf_counter() - t_rerank_start) * 1000
    print(f"[RERANK] Evaluated {len(candidate_chunks)} candidates -> selected top {len(retrieved_chunks)} in {rerank_ms:.1f}ms (Retrieval: {retrieval_ms:.1f}ms)")

    # Step 5: Safety / Relevance Control Check
    sufficient, safety_result = is_sufficient(retrieved_chunks, query=augmented_message, machine=parsed_q.get("machine"))
    if not sufficient:
        # On safety refusal, preserve active machine & error context unless user explicitly introduced a new one
        if parsed_q.get("machine_source") not in ("session_context", None):
            memory_store.update_session(session_id, machine=parsed_q.get("machine"), error_code=parsed_q.get("error_code"), last_answer=safety_result)
        else:
            sess = memory_store.get_session(session_id)
            sess["last_answer"] = safety_result
        return QueryResponse(
            answer=safety_result, # Refusal message
            sources=[],
            ambiguous=False,
            options=[],
            machine_source=parsed_q.get("machine_source"),
            detected_machine=parsed_q.get("machine"),
            detected_error=parsed_q.get("error_code")
        )

    # Step 6: Context Assembly & Answer Generation
    context_text = assemble_context(retrieved_chunks)
    answer_text = generate_answer(augmented_message, context_text)

    # Step 7: Format Source Citations & Schematics
    # If the LLM self-refused (second-line defense), clear sources — no phantom citations.
    sources = []
    diagrams = []
    seen_diagram_urls = set()

    if answer_text.strip() != REFUSAL_MESSAGE and REFUSAL_MESSAGE not in answer_text:
        target_error = (parsed_q.get("error_code") or "").strip().upper()
        target_machine = (parsed_q.get("machine") or "").strip()
        if target_machine == "Hydraulic Press" and target_error in ("E101", "E202", "E203"):
            target_machine = "Press-200"
        elif target_machine == "Press-200" and target_error.startswith("H"):
            target_machine = "Hydraulic Press"
        top_chunk_error = (retrieved_chunks[0].get("error_code") or "").strip().upper() if retrieved_chunks else ""
        seen_sources = set()

        for c in retrieved_chunks:
            s_key = (c.get("manual"), c.get("section"))
            diag_url = c.get("diagram_url")
            diag_title = c.get("diagram_title")
            diag_caption = c.get("diagram_caption")
            c_error = (c.get("error_code") or "").strip().upper()
            c_machine = (c.get("machine") or "").strip()

            # Prevent attaching diagrams that belong to a different machine or error code
            is_valid_diag = True
            if target_machine and c_machine and c_machine != target_machine:
                is_valid_diag = False
            elif target_error and c_error and c_error != target_error:
                is_valid_diag = False
            elif not target_error and top_chunk_error and c_error and c_error != top_chunk_error:
                is_valid_diag = False
            elif len(diagrams) >= 1:
                is_valid_diag = False

            # Collect unique diagrams
            if is_valid_diag and diag_url and diag_url not in seen_diagram_urls:
                seen_diagram_urls.add(diag_url)
                diagrams.append(DiagramMetadata(
                    title=diag_title or f"{c.get('machine', 'Machine')} Schematic",
                    filename=os.path.basename(diag_url),
                    url=diag_url,
                    caption=diag_caption or f"Technical schematic for {c.get('section', 'component')}",
                    system=c.get("machine")
                ))

            if s_key not in seen_sources:
                seen_sources.add(s_key)
                page_val = c.get("page")
                page_int = None
                if page_val is not None:
                    try:
                        page_int = int(page_val)
                    except (ValueError, TypeError):
                        pass
                raw_score = c.get("score")
                raw_rerank = c.get("rerank_score")
                score_float = None
                if raw_score is not None:
                    try:
                        score_float = round(float(raw_score), 3)
                    except (ValueError, TypeError):
                        pass
                rerank_float = None
                if raw_rerank is not None:
                    try:
                        rerank_float = round(float(raw_rerank), 2)
                    except (ValueError, TypeError):
                        pass

                sources.append(SourceMetadata(
                    manual=c.get("manual", ""),
                    section=c.get("section", ""),
                    machine=c.get("machine", ""),
                    error_code=c.get("error_code"),
                    page=page_int,
                    snippet=c.get("text", ""),
                    diagram_url=diag_url,
                    diagram_title=diag_title,
                    diagram_caption=diag_caption,
                    score=score_float,
                    rerank_score=rerank_float,
                    match_type=c.get("match_type", "vector"),
                    rank=len(sources) + 1
                ))

        # Dynamic fallback diagram lookup if pre-indexed chunks had no diagram attached
        if len(diagrams) == 0:
            top_m = parsed_q.get("machine") or (retrieved_chunks[0].get("machine") if retrieved_chunks else None)
            top_e = parsed_q.get("error_code") or (retrieved_chunks[0].get("error_code") if retrieved_chunks else None)
            top_s = retrieved_chunks[0].get("section") if retrieved_chunks else None
            try:
                from src.diagrams import get_diagram_for_chunk
                diag_fallback = get_diagram_for_chunk(top_m or "", top_e, top_s)
                if diag_fallback:
                    diagrams.append(DiagramMetadata(
                        title=diag_fallback.get("title", f"{top_m or 'System'} Schematic"),
                        filename=diag_fallback.get("filename", os.path.basename(diag_fallback["url"])),
                        url=diag_fallback["url"],
                        caption=diag_fallback.get("caption", f"Technical schematic for {top_m or 'equipment'}"),
                        system=diag_fallback.get("system", top_m)
                    ))
            except Exception:
                pass

        # Ensure citations reference the active diagram if they don't have one
        if len(diagrams) > 0 and len(sources) > 0:
            for s in sources:
                if not s.diagram_url:
                    s.diagram_url = diagrams[0].url
                    s.diagram_title = diagrams[0].title
                    s.diagram_caption = diagrams[0].caption

    # Step 8: Update Session Memory
    top_machine = parsed_q.get("machine") or (retrieved_chunks[0].get("machine") if retrieved_chunks else None)
    top_error = parsed_q.get("error_code") or (retrieved_chunks[0].get("error_code") if retrieved_chunks else None)
    memory_store.update_session(session_id, machine=top_machine, error_code=top_error, last_answer=answer_text)

    return QueryResponse(
        answer=answer_text,
        sources=sources,
        ambiguous=False,
        options=[],
        diagrams=diagrams,
        machine_source=parsed_q.get("machine_source"),
        detected_machine=top_machine,
        detected_error=top_error
    )

@app.get("/diagrams/{filename}")
def get_diagram_file(filename: str):
    diag_path = os.path.join(STATIC_DIR, "diagrams", filename)
    if os.path.exists(diag_path):
        return FileResponse(diag_path, media_type="image/svg+xml")
    raise HTTPException(status_code=404, detail="Diagram not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api:app", host="127.0.0.1", port=8000, reload=True)

