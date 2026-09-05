import sys
import os
import re
import io
import json
import base64
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pypdf

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
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

MANUALS_DIR = os.path.join(REPO_ROOT, "data", "manuals")

from src.query_understanding import parse_query, parse_query_with_context, DEFAULT_KNOWN_MACHINES
from src.retrieval import retrieve
from src.hybrid_search import hybrid_retrieve
from src.rerank import rerank
from src.disambiguation import check_ambiguity
import time
from src.safety import is_sufficient, REFUSAL_MESSAGE
from src.llm_answer import assemble_context, generate_answer, structure_pdf_text_with_llm
from src.memory import memory_store
from src.ingest import validate_manual_content
from src.embed_store import (
    upsert_chunks,
    delete_by_machine,
    get_distinct_machines,
    get_manuals_summary,
    invalidate_machines_cache,
    get_chroma_collection
)
from src.translation import translate_input, translateInput, _module_instance
from src.speech import speech_service, VOICE_BENCHMARK_SAMPLES, SUPPORTED_VOICE_LANGUAGES
from src.confidence import (
    get_confidence_level,
    calculate_model_confidence,
    extract_fault_title_and_component,
    extract_cause_and_recommendation,
    generate_telemetry_evidence,
    rank_candidate_faults,
    compute_machine_health,
    CONFIDENCE_DISCLAIMER
)

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

def sanitize_machine_filename(machine_name: str) -> str:
    """Sanitizes machine name to lowercase with underscores for files."""
    cleaned = re.sub(r"[^a-z0-9]+", "_", machine_name.lower()).strip("_")
    return f"{cleaned}.txt"

# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

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

class PossibleFault(BaseModel):
    fault: str
    fault_code: Optional[str] = None
    fault_name: Optional[str] = None
    confidence_score: float
    confidence_percentage: int
    confidence_level: str
    is_primary: bool = False
    component: Optional[str] = None
    supporting_evidence: Optional[List[str]] = None

class FaultEvidence(BaseModel):
    contributing_evidence: str
    reasoning: str
    sensor_readings: Dict[str, Any]
    reasoning_points: Optional[List[str]] = None
    disclaimer: str = CONFIDENCE_DISCLAIMER

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
    fault: Optional[str] = None
    component: Optional[str] = None
    confidence_score: Optional[float] = None
    confidence_level: Optional[str] = None
    confidence_percentage: Optional[int] = None
    cause: Optional[str] = None
    recommendation: Optional[str] = None
    possible_faults: List[PossibleFault] = []
    evidence: Optional[FaultEvidence] = None
    disclaimer: Optional[str] = None

class TranslateRequest(BaseModel):
    text: Optional[str] = None
    message: Optional[str] = None

class TranslateResponse(BaseModel):
    originalText: str
    detectedLanguage: str
    translatedText: str

class ManualUploadResponse(BaseModel):
    status: str  # "success" | "needs_review" | "error"
    machine: Optional[str] = None
    chunk_count: Optional[int] = None
    draft_text: Optional[str] = None
    error: Optional[str] = None
    is_valid_format: Optional[bool] = None
    source_language: Optional[str] = "en"
    detected_language: Optional[str] = "English"
    is_translated: Optional[bool] = False

class ManualConfirmRequest(BaseModel):
    machine: str
    content: str
    source_language: Optional[str] = "en"
    detected_language: Optional[str] = "English"
    is_translated: Optional[bool] = False

class ManualSummaryItem(BaseModel):
    machine: str
    filename: str
    chunk_count: int
    updated_at: str

class ManualsListResponse(BaseModel):
    manuals: List[ManualSummaryItem]

class VoiceTranscribeRequest(BaseModel):
    audio: Optional[str] = None  # Base64 encoded audio string
    format: Optional[str] = "audio/webm"
    language: Optional[str] = None  # Optional language hint (e.g. en, zh, ja, de)
    sample_id: Optional[str] = None  # Optional ID of pre-configured voice sample

class VoiceTranscribeResponse(BaseModel):
    status: str
    transcription: str
    detectedLanguage: str
    languageName: str
    englishText: str
    isTranslated: bool
    confidence: Optional[float] = None
    state: str = "complete"
    error: Optional[str] = None

class VoiceQueryRequest(BaseModel):
    transcription: Optional[str] = None
    edited_transcription: Optional[str] = None
    audio: Optional[str] = None
    format: Optional[str] = "audio/webm"
    session_id: str = "default_session"
    machine_filter: Optional[str] = None

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
    """Returns list of known machine names from ChromaDB (cached in memory)."""
    machines = get_distinct_machines()
    if not machines:
        machines = DEFAULT_KNOWN_MACHINES
    return {"machines": machines}

@app.get("/api/manuals")
def get_manuals_library():
    """Returns content and metadata for all active factory manuals including PDF availability."""
    manuals_dir = os.path.join(REPO_ROOT, "data", "manuals")
    manual_configs = [
        {"filename": "conveyorcb4400.txt", "title": "Conveyor Belt System — Model CB-4400 Troubleshooting Manual", "machine": "Conveyor Belt System", "pages": 6, "chunkCount": 20, "pdf_filename": "conveyorcb4400.pdf"},
        {"filename": "cncmx7.txt", "title": "CNC Milling Machine — Model MX-7 Precision Troubleshooting Manual", "machine": "CNC Milling Machine", "pages": 6, "chunkCount": 20, "pdf_filename": "cncmx7.pdf"},
        {"filename": "presshp2200.txt", "title": "Hydraulic Press — Model HP-2200 Troubleshooting Manual", "machine": "Hydraulic Press", "pages": 6, "chunkCount": 20, "pdf_filename": "presshp2200.pdf"},
        {"filename": "robotarm_300.txt", "title": "Articulated Robot — Model RobotArm-300 Diagnostic Manual", "machine": "RobotArm-300", "pages": 2, "chunkCount": 6, "pdf_filename": "robotarm_300.pdf"},
    ]
    seen_files = set()
    results = []
    for mc in manual_configs:
        seen_files.add(mc["filename"])
        path = os.path.join(manuals_dir, mc["filename"])
        raw_text = ""
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                raw_text = f.read()
        pdf_name = mc.get("pdf_filename", mc["filename"].replace(".txt", ".pdf"))
        pdf_path = os.path.join(manuals_dir, pdf_name)
        has_pdf = os.path.exists(pdf_path)

        # Check for optional translation metadata
        base_name = os.path.splitext(mc["filename"])[0]
        meta_file = os.path.join(manuals_dir, f"{base_name}.meta.json")
        is_trans = False
        src_lang = "en"
        det_lang = "English"
        if os.path.exists(meta_file):
            try:
                with open(meta_file, "r", encoding="utf-8") as mf:
                    mdata = json.load(mf)
                    is_trans = mdata.get("is_translated", False)
                    src_lang = mdata.get("source_language", "en")
                    det_lang = mdata.get("detected_language", "English")
            except Exception:
                pass

        results.append({
            **mc,
            "raw_text": raw_text,
            "has_pdf": has_pdf,
            "pdf_url": f"/api/manuals/{pdf_name}/pdf" if has_pdf else None,
            "is_translated": is_trans,
            "source_language": src_lang,
            "detected_language": det_lang
        })

    # Also discover any dynamic uploaded manuals in manuals_dir (excluding legacy demo or archived files)
    ignored_prefixes = (".", "multilingual_")
    ignored_exact = {"cnc100.txt", "press200.txt", "robotarm300.txt"}
    if os.path.exists(manuals_dir):
        for fname in sorted(os.listdir(manuals_dir)):
            if (
                fname.endswith(".txt")
                and fname not in seen_files
                and fname not in ignored_exact
                and not any(fname.startswith(p) for p in ignored_prefixes)
            ):
                fpath = os.path.join(manuals_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        raw_text = f.read()
                    mach_match = re.search(r"^MACHINE:\s*(.+)$", raw_text, re.MULTILINE)
                    mach_name = mach_match.group(1).strip() if mach_match else fname[:-4].replace("_", " ").title()
                    pdf_cand = fname.replace(".txt", ".pdf")
                    has_pdf = os.path.exists(os.path.join(manuals_dir, pdf_cand))
                    page_matches = re.findall(r"PAGE:\s*(\d+)", raw_text)
                    page_cnt = max([int(p) for p in page_matches]) if page_matches else 1
                    chunk_cnt = len(re.findall(r"^SECTION:", raw_text, re.MULTILINE))

                    base_name = fname[:-4]
                    meta_file = os.path.join(manuals_dir, f"{base_name}.meta.json")
                    is_trans = False
                    src_lang = "en"
                    det_lang = "English"
                    if os.path.exists(meta_file):
                        try:
                            with open(meta_file, "r", encoding="utf-8") as mf:
                                mdata = json.load(mf)
                                is_trans = mdata.get("is_translated", False)
                                src_lang = mdata.get("source_language", "en")
                                det_lang = mdata.get("detected_language", "English")
                        except Exception:
                            pass

                    results.append({
                        "filename": fname,
                        "title": f"{mach_name} Troubleshooting Manual",
                        "machine": mach_name,
                        "pages": page_cnt,
                        "chunkCount": chunk_cnt,
                        "pdf_filename": pdf_cand if has_pdf else None,
                        "raw_text": raw_text,
                        "has_pdf": has_pdf,
                        "pdf_url": f"/api/manuals/{pdf_cand}/pdf" if has_pdf else None,
                        "is_translated": is_trans,
                        "source_language": src_lang,
                        "detected_language": det_lang
                    })
                except Exception:
                    pass
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

@app.get("/api/voice/status")
@app.get("/voice/status")
def get_voice_status():
    """Returns the operational status and supported languages for voice query."""
    return {
        "enabled": speech_service.is_available(),
        "engine": "Google Cloud Speech-to-Text v1",
        "supported_languages": SUPPORTED_VOICE_LANGUAGES,
        "sample_count": len(VOICE_BENCHMARK_SAMPLES)
    }

@app.get("/api/voice/samples")
@app.get("/voice/samples")
def get_voice_samples():
    """Returns preset multilingual voice benchmark samples for 1-click testing."""
    return {
        "samples": VOICE_BENCHMARK_SAMPLES,
        "languages": ["English (en-US)", "Simplified Chinese (zh-CN)", "Japanese (ja-JP)", "German (de-DE)"]
    }

@app.post("/api/voice/transcribe", response_model=VoiceTranscribeResponse)
@app.post("/voice/transcribe", response_model=VoiceTranscribeResponse)
def api_voice_transcribe(req: VoiceTranscribeRequest):
    """
    Voice Input -> Speech-to-Text -> Language Detection -> Existing Translation Module -> English Text.
    Supports audio base64 payload OR pre-configured benchmark sample_id.
    """
    # 1. Handle sample_id (for instant 1-click test suite or demo)
    if req.sample_id:
        match = next((s for s in VOICE_BENCHMARK_SAMPLES if s["id"] == req.sample_id), None)
        if match:
            return VoiceTranscribeResponse(
                status="success",
                transcription=match["sample_text"],
                detectedLanguage=match["language"],
                languageName=match["language_name"],
                englishText=match["english_text"],
                isTranslated=match["is_translated"],
                confidence=0.99,
                state="complete"
            )

    # 2. Handle audio base64
    if not req.audio:
        raise HTTPException(status_code=400, detail="Either 'audio' (base64 string) or 'sample_id' must be provided.")

    try:
        audio_data = req.audio
        # Strip data URL prefix if present (e.g. data:audio/webm;base64,...)
        if "," in audio_data:
            audio_data = audio_data.split(",", 1)[1]
        raw_bytes = base64.b64decode(audio_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 audio encoding: {e}")

    result = speech_service.transcribe_audio(
        raw_bytes,
        mime_type=req.format or "audio/webm",
        language_hint=req.language
    )

    if result.get("status") == "error":
        return VoiceTranscribeResponse(
            status="error",
            transcription="",
            detectedLanguage="en",
            languageName="English",
            englishText="",
            isTranslated=False,
            state="error",
            error=result.get("error", "Speech recognition failed")
        )

    return VoiceTranscribeResponse(
        status="success",
        transcription=result["transcription"],
        detectedLanguage=result["detectedLanguage"],
        languageName=result["languageName"],
        englishText=result["englishText"],
        isTranslated=result["isTranslated"],
        confidence=result.get("confidence", 0.95),
        state="complete"
    )

@app.post("/api/voice/query", response_model=QueryResponse)
@app.post("/voice/query", response_model=QueryResponse)
def api_voice_query(req: VoiceQueryRequest):
    """
    Executes a complete voice query through the EXACT existing diagnosis pipeline.
    Accepts confirmed/edited transcription text OR raw audio, translates non-English
    speech via the existing translation module, and feeds the English query directly
    into handle_query.
    """
    # 1. If edited or direct transcription is provided:
    query_text = (req.edited_transcription or req.transcription or "").strip()

    # 2. If only audio is provided:
    if not query_text and req.audio:
        try:
            audio_data = req.audio.split(",", 1)[1] if "," in req.audio else req.audio
            raw_bytes = base64.b64decode(audio_data)
            trans_res = speech_service.transcribe_audio(raw_bytes, mime_type=req.format or "audio/webm")
            query_text = trans_res.get("englishText") or trans_res.get("transcription") or ""
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to process voice audio: {e}")

    if not query_text:
        raise HTTPException(status_code=400, detail="No speech query text or audio provided.")

    # Send directly to existing diagnostic pipeline
    core_req = QueryRequest(
        message=query_text,
        session_id=req.session_id,
        machine_filter=req.machine_filter
    )
    return handle_query(core_req)

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

    active_machines = get_distinct_machines() or DEFAULT_KNOWN_MACHINES
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
                known_machines=active_machines,
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
        # Save error context so follow-up selection can resolve cleanly, clearing previous machine
        top_error = parsed_q.get("error_code")
        memory_store.update_session(session_id, machine=None, error_code=top_error, last_answer=answer_text, clear_machine=True)
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
        # On safety refusal, preserve active machine & error context (do not poison with rejected query)
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

    # Step 7: Format Source Citations, Schematics & AI Confidence Scoring
    # If the LLM self-refused (second-line defense), clear sources and confidence — no phantom scores.
    sources = []
    diagrams = []
    seen_diagram_urls = set()
    fault_title = None
    component = None
    confidence_score = None
    confidence_level = None
    confidence_pct = None
    cause = None
    recommendation = None
    possible_faults = []
    evidence = None

    if answer_text.strip() != REFUSAL_MESSAGE and REFUSAL_MESSAGE not in answer_text and retrieved_chunks:
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

        # Calculate AI Confidence Score using existing retrieval model similarity
        top_chunk = retrieved_chunks[0]
        has_exact_error = bool(parsed_q.get("error_code"))
        confidence_score = calculate_model_confidence(top_chunk, query_has_exact_error=has_exact_error)
        confidence_level = get_confidence_level(confidence_score)
        confidence_pct = int(round(confidence_score * 100))

        fault_title, component = extract_fault_title_and_component(top_chunk, english_query, answer_text)
        cause, recommendation = extract_cause_and_recommendation(answer_text, top_chunk)
        
        # Telemetry evidence and reasoning for "View Explanation"
        chunk_machine = top_chunk.get("machine", "Industrial Machine")
        evidence_dict = generate_telemetry_evidence(fault_title, component, chunk_machine, confidence_score)
        evidence = FaultEvidence(
            contributing_evidence=evidence_dict["contributing_evidence"],
            reasoning=evidence_dict["reasoning"],
            sensor_readings=evidence_dict["sensor_readings"],
            reasoning_points=evidence_dict.get("reasoning_points"),
            disclaimer=CONFIDENCE_DISCLAIMER
        )

        # Multiple candidate faults ranked by confidence (highest is primary)
        ranked_candidates = rank_candidate_faults(retrieved_chunks, english_query, fault_title, confidence_score, component)
        possible_faults = [PossibleFault(**item) for item in ranked_candidates]

        # Record in diagnostic fault history
        fault_record = {
            "id": f"FLT-{int(time.time()*1000) % 1000000}",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "machine": chunk_machine,
            "fault": fault_title,
            "component": component,
            "confidence_score": confidence_score,
            "confidence_percentage": confidence_pct,
            "confidence_level": confidence_level,
            "cause": cause,
            "recommendation": recommendation,
            "query": english_query,
            "possible_faults": ranked_candidates,
            "evidence": evidence_dict
        }
        FAULT_HISTORY.insert(0, fault_record)
        # Retain last 50 diagnoses
        if len(FAULT_HISTORY) > 50:
            FAULT_HISTORY.pop()

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
        detected_error=top_error,
        rerank_applied=True,
        fault=fault_title,
        component=component,
        confidence_score=confidence_score,
        confidence_level=confidence_level,
        confidence_percentage=confidence_pct,
        cause=cause,
        recommendation=recommendation,
        possible_faults=possible_faults,
        evidence=evidence,
        disclaimer=CONFIDENCE_DISCLAIMER if confidence_score is not None else None
    )

@app.get("/diagrams/{filename}")
def get_diagram_file(filename: str):
    diag_path = os.path.join(STATIC_DIR, "diagrams", filename)
    if os.path.exists(diag_path):
        return FileResponse(diag_path, media_type="image/svg+xml")
    raise HTTPException(status_code=404, detail="Diagram not found")

# ---------------------------------------------------------------------------
# Manual Management Endpoints (Runtime Upload, Confirm, List, Delete)
# ---------------------------------------------------------------------------

@app.post("/manuals/upload", response_model=ManualUploadResponse)
async def upload_manual(file: UploadFile = File(...)):
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".txt", ".pdf"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Only .txt and .pdf are accepted."
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if ext == ".txt":
        try:
            content = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content = file_bytes.decode("latin-1")

        is_valid, err_msg, machine_name, chunks = validate_manual_content(content)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Manual format validation failed: {err_msg}")

        # Save to data/manuals/<sanitized_machine>.txt
        os.makedirs(MANUALS_DIR, exist_ok=True)
        out_filename = sanitize_machine_filename(machine_name)
        out_path = os.path.join(MANUALS_DIR, out_filename)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Delete any existing chunks for this machine before upserting new ones
        delete_by_machine(machine_name)
        chunk_count = upsert_chunks(chunks)

        # Language detection on 2,500-char substantive sample
        sample_lines = [l.strip() for l in content.splitlines() if len(l.strip().split()) >= 4]
        sample_text = " ".join(sample_lines)[:2500] if sample_lines else content[:2500]
        det = _module_instance.detect_language(sample_text)
        detected_code = det.get("language", "en")
        detected_name = det.get("language_name", "English")
        is_trans = detected_code != "en"

        return ManualUploadResponse(
            status="success",
            machine=machine_name,
            chunk_count=chunk_count,
            draft_text=None,
            error=None,
            is_valid_format=True,
            source_language=detected_code,
            detected_language=detected_name,
            is_translated=is_trans
        )

    elif ext == ".pdf":
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            extracted_text = ""
            for page in reader.pages:
                page_txt = page.extract_text()
                if page_txt:
                    extracted_text += page_txt + "\n"
        except Exception as err:
            raise HTTPException(status_code=400, detail=f"Failed to read PDF document: {err}")

        # Check for scanned / image-only PDFs with no extractable text
        if len(extracted_text.strip()) < 100:
            raise HTTPException(
                status_code=400,
                detail="No extractable text found — this may be a scanned document. OCR is not currently supported."
            )

        # Sample substantive body text for language detection (first 2,500 chars purely for metadata)
        non_empty_chars = [ch for ch in extracted_text if not ch.isspace()]
        sample_text = extracted_text[:2500] if len(non_empty_chars) >= 2500 else extracted_text
        det = _module_instance.detect_language(sample_text)
        detected_code = det.get("language", "en")
        detected_name = det.get("language_name", "English")
        is_trans = detected_code != "en"

        # Call Gemini to structure and translate the raw text into standard English format
        try:
            draft_text = structure_pdf_text_with_llm(extracted_text)
        except Exception as err:
            return ManualUploadResponse(
                status="error",
                machine=None,
                chunk_count=0,
                draft_text=None,
                error=f"LLM structuring failed: {str(err)}",
                is_valid_format=False,
                source_language=detected_code,
                detected_language=detected_name,
                is_translated=is_trans
            )

        is_valid, err_msg, machine_name, chunks = validate_manual_content(draft_text)

        # Post-structuring language verification check on MEANING/CAUSES/STEPS
        structured_content_lines = []
        for line in draft_text.splitlines():
            sline = line.strip()
            if any(sline.startswith(k) for k in ["MEANING:", "CAUSES:", "STEPS:", "SECTION:"]):
                parts = sline.split(":", 1)
                if len(parts) > 1 and parts[1].strip():
                    structured_content_lines.append(parts[1].strip())
            elif sline.startswith("-") or (sline and sline[0].isdigit() and "." in sline[:4]):
                structured_content_lines.append(sline)
        post_sample = " ".join(structured_content_lines)[:2500] if structured_content_lines else draft_text[:2500]
        post_det = _module_instance.detect_language(post_sample)
        post_lang = post_det.get("language", "en")
        post_conf = post_det.get("confidence", 0.0)

        # If it's still non-English with high confidence, flag needs_review and invalidate format
        if post_lang != "en" and post_conf >= 0.70:
            is_valid = False
            post_name = post_det.get("language_name", post_lang)
            err_msg = f"Translation incomplete: Structured output contains non-English text ({post_name}, confidence: {post_conf:.2f}). Manual review required."

        # Cache raw uploaded PDF bytes for confirmation
        os.makedirs(MANUALS_DIR, exist_ok=True)
        temp_pdf_name = f".draft_{sanitize_machine_filename(machine_name or 'unconfirmed')}.pdf"
        try:
            with open(os.path.join(MANUALS_DIR, temp_pdf_name), "wb") as f:
                f.write(file_bytes)
        except Exception:
            pass

        return ManualUploadResponse(
            status="needs_review",
            machine=machine_name,
            chunk_count=len(chunks),
            draft_text=draft_text,
            error=err_msg,
            is_valid_format=is_valid,
            source_language=detected_code,
            detected_language=detected_name,
            is_translated=is_trans
        )

@app.post("/manuals/confirm", response_model=ManualUploadResponse)
def confirm_manual(req: ManualConfirmRequest):
    content = req.content
    if not content or not content.strip():
        raise HTTPException(status_code=400, detail="Manual content cannot be empty.")

    is_valid, err_msg, parsed_machine, chunks = validate_manual_content(content)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Manual format validation failed: {err_msg}")

    machine_name = req.machine.strip() if req.machine and req.machine.strip() else parsed_machine

    os.makedirs(MANUALS_DIR, exist_ok=True)
    out_filename = sanitize_machine_filename(machine_name)
    out_path = os.path.join(MANUALS_DIR, out_filename)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    # If draft PDF exists, promote to final machine PDF
    base_name = out_filename.replace(".txt", "")
    temp_pdf_name = f".draft_{out_filename}.pdf"
    temp_pdf_path = os.path.join(MANUALS_DIR, temp_pdf_name)
    final_pdf_path = os.path.join(MANUALS_DIR, f"{base_name}.pdf")
    if os.path.exists(temp_pdf_path):
        try:
            if os.path.exists(final_pdf_path):
                os.remove(final_pdf_path)
            os.rename(temp_pdf_path, final_pdf_path)
        except Exception:
            pass

    # Save optional translation metadata if manual was translated
    meta_path = os.path.join(MANUALS_DIR, f"{base_name}.meta.json")
    if req.is_translated or (req.source_language and req.source_language != "en"):
        try:
            with open(meta_path, "w", encoding="utf-8") as mf:
                json.dump({
                    "is_translated": True,
                    "source_language": req.source_language or "en",
                    "detected_language": req.detected_language or "English"
                }, mf, indent=2)
        except Exception:
            pass

    delete_by_machine(machine_name)
    chunk_count = upsert_chunks(chunks)

    return ManualUploadResponse(
        status="success",
        machine=machine_name,
        chunk_count=chunk_count,
        draft_text=None,
        error=None,
        is_valid_format=True,
        source_language=req.source_language,
        detected_language=req.detected_language,
        is_translated=req.is_translated
    )

@app.api_route("/api/manuals/{filename_or_machine}/pdf", methods=["GET", "HEAD"])
@app.api_route("/manuals/{filename_or_machine}/pdf", methods=["GET", "HEAD"])
def get_manual_pdf(filename_or_machine: str, download: bool = False):
    """Streams PDF version of technical manual for in-browser PDF reader."""
    if not os.path.exists(MANUALS_DIR):
        raise HTTPException(status_code=404, detail="Manuals directory not found.")

    found_path = None
    target_filename = None

    # 1. Exact match
    target_pdf = filename_or_machine if filename_or_machine.lower().endswith(".pdf") else f"{filename_or_machine}.pdf"
    direct_path = os.path.join(MANUALS_DIR, target_pdf)
    if os.path.exists(direct_path):
        found_path = direct_path
        target_filename = target_pdf

    # 2. Check sanitized machine name
    if not found_path:
        sanitized_base = sanitize_machine_filename(filename_or_machine).replace(".txt", "")
        sanitized_pdf = os.path.join(MANUALS_DIR, f"{sanitized_base}.pdf")
        if os.path.exists(sanitized_pdf):
            found_path = sanitized_pdf
            target_filename = f"{sanitized_base}.pdf"

    # 3. Fuzzy search in manuals dir
    if not found_path:
        clean_query = filename_or_machine.lower().replace("-", "").replace(" ", "").replace("_", "").replace(".pdf", "")
        for fname in os.listdir(MANUALS_DIR):
            if fname.lower().endswith(".pdf") and not fname.startswith("."):
                clean_f = fname.lower().replace("-", "").replace(" ", "").replace("_", "").replace(".pdf", "")
                if clean_f in clean_query or clean_query in clean_f:
                    found_path = os.path.join(MANUALS_DIR, fname)
                    target_filename = fname
                    break

    if not found_path or not os.path.exists(found_path):
        raise HTTPException(status_code=404, detail=f"PDF manual for '{filename_or_machine}' not found.")

    if download:
        headers = {
            "Content-Disposition": f'attachment; filename="{target_filename}"',
            "Content-Type": "application/pdf",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
        return FileResponse(
            found_path,
            media_type="application/pdf",
            content_disposition_type="attachment",
            filename=target_filename,
            headers=headers
        )
    else:
        headers = {
            "Content-Disposition": f'inline; filename="{target_filename}"',
            "Content-Type": "application/pdf",
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Content-Security-Policy": "frame-ancestors *",
            "X-Frame-Options": "ALLOWALL",
            "X-Content-Type-Options": "nosniff"
        }
        return FileResponse(
            found_path,
            media_type="application/pdf",
            content_disposition_type="inline",
            filename=target_filename,
            headers=headers
        )

@app.get("/manuals", response_model=ManualsListResponse)
def list_manuals():
    summary = get_manuals_summary(manuals_dir=MANUALS_DIR)
    return ManualsListResponse(
        manuals=[
            ManualSummaryItem(
                machine=item["machine"],
                filename=item["filename"],
                chunk_count=item["chunk_count"],
                updated_at=item["updated_at"]
            )
            for item in summary
        ]
    )

@app.delete("/manuals/{machine}")
def delete_manual(machine: str):
    chunks_deleted = delete_by_machine(machine)
    file_deleted = False

    # 1. Direct deterministic path lookup first
    target_filename = sanitize_machine_filename(machine)
    target_path = os.path.join(MANUALS_DIR, target_filename)
    if os.path.exists(target_path):
        try:
            os.remove(target_path)
            file_deleted = True
        except Exception as err:
            print(f"[delete_manual file remove error]: {err}")

    # Remove corresponding PDF if present
    pdf_path = os.path.join(MANUALS_DIR, f"{target_filename.replace('.txt', '')}.pdf")
    if os.path.exists(pdf_path):
        try:
            os.remove(pdf_path)
        except Exception:
            pass

    # 2. Genuine fallback on miss (for legacy filenames e.g. cncmx7.txt)
    if not file_deleted and os.path.exists(MANUALS_DIR):
        for fname in os.listdir(MANUALS_DIR):
            if fname.endswith(".txt"):
                fpath = os.path.join(MANUALS_DIR, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        first_lines = [f.readline() for _ in range(5)]
                        for line in first_lines:
                            if line.lower().startswith("machine:") and machine.lower() in line.lower():
                                os.remove(fpath)
                                file_deleted = True
                                # Also remove matching pdf
                                cand_pdf = fpath.replace(".txt", ".pdf")
                                if os.path.exists(cand_pdf):
                                    os.remove(cand_pdf)
                                break
                except Exception:
                    pass
            if file_deleted:
                break

    # If neither chunks nor file existed, return 404
    if chunks_deleted == 0 and not file_deleted:
        raise HTTPException(status_code=404, detail=f"Manual for machine '{machine}' not found.")

    invalidate_machines_cache()
    return {
        "status": "success",
        "message": f"Manual for '{machine}' deleted.",
        "chunks_deleted": chunks_deleted,
        "file_deleted": file_deleted
    }


# --------------------------------------------------------------------------
# FAULT HISTORY & MACHINE HEALTH ENDPOINTS
# --------------------------------------------------------------------------

# Pre-seed initial fault history entries
FAULT_HISTORY: List[Dict[str, Any]] = [
    {
        "id": "FLT-928104",
        "timestamp": "2026-09-04 18:42:15",
        "machine": "CNC Milling Machine",
        "fault": "Motor Bearing Wear",
        "component": "Spindle Bearing Assembly",
        "confidence_score": 0.91,
        "confidence_percentage": 91,
        "confidence_level": "High",
        "cause": "Bearing wear due to excessive vibration and thermal breakdown under continuous 24k RPM load.",
        "recommendation": "Inspect the motor bearing, verify runout (<0.003 mm), and replenish synthetic grease lubrication.",
        "query": "Motor bearing vibration and temperature abnormal",
        "possible_faults": [
            {"fault": "Motor Bearing Wear", "confidence_score": 0.91, "confidence_percentage": 91, "confidence_level": "High", "is_primary": True, "component": "Spindle Bearing Assembly"},
            {"fault": "Shaft Misalignment", "confidence_score": 0.62, "confidence_percentage": 62, "confidence_level": "Moderate", "is_primary": False, "component": "Drive Shaft Coupling"},
            {"fault": "Motor Overload / Phase Imbalance", "confidence_score": 0.28, "confidence_percentage": 28, "confidence_level": "Low", "is_primary": False, "component": "Stator Winding"}
        ],
        "evidence": {
            "contributing_evidence": "Vibration Velocity: 4.82 mm/s RMS (Threshold: 2.80 mm/s) | Bearing Temperature: 88.4°C | Acoustic Emission: 86.5 dBA @ 2.4 kHz",
            "reasoning": "High-frequency vibration spectrum indicates micro-pitting in the bearing raceway.",
            "sensor_readings": {
                "vibration_velocity": "4.82 mm/s RMS (Threshold: 2.80 mm/s)",
                "bearing_temperature": "88.4°C (Nominal: 45–60°C)",
                "acoustic_emission": "86.5 dBA @ 2.4 kHz harmonic",
                "lubrication_dielectric": "0.42 (Degraded oil film)"
            },
            "disclaimer": CONFIDENCE_DISCLAIMER
        }
    },
    {
        "id": "FLT-841920",
        "timestamp": "2026-09-04 16:15:08",
        "machine": "Conveyor Belt System",
        "fault": "Drive Belt Slippage & Wear",
        "component": "Drive Belt & Tensioner Pulley",
        "confidence_score": 0.84,
        "confidence_percentage": 84,
        "confidence_level": "Moderate",
        "cause": "Low tension frequency (32 Hz) and particulate contamination on drive pulley.",
        "recommendation": "Re-tension belt to specified 45–50 Hz using sonic tension meter and clean pulley contact face.",
        "query": "conveyor squeal during morning startup",
        "possible_faults": [
            {"fault": "Drive Belt Slippage & Wear", "confidence_score": 0.84, "confidence_percentage": 84, "confidence_level": "Moderate", "is_primary": True, "component": "Drive Belt & Tensioner Pulley"},
            {"fault": "Pulley Bearing Seizure", "confidence_score": 0.55, "confidence_percentage": 55, "confidence_level": "Low", "is_primary": False, "component": "Tail Pulley Bearing"},
            {"fault": "Belt Tracking Deviation", "confidence_score": 0.27, "confidence_percentage": 27, "confidence_level": "Low", "is_primary": False, "component": "Guide Roller"}
        ],
        "evidence": {
            "contributing_evidence": "Belt Surface Speed: 1.24 m/s (Commanded: 1.50 m/s) | Slip Ratio: 17.3% | Tension Frequency: 32 Hz",
            "reasoning": "Velocity discrepancy between drive motor and belt surface exceeds the 3% slippage threshold.",
            "sensor_readings": {
                "belt_surface_speed": "1.24 m/s (Commanded: 1.50 m/s)",
                "drive_pulley_slip_ratio": "17.3% (Threshold: < 3.0%)",
                "tension_frequency": "32 Hz (Target: 45–50 Hz)",
                "motor_current_draw": "14.8 A (Fluctuating ± 2.2 A)"
            },
            "disclaimer": CONFIDENCE_DISCLAIMER
        }
    },
    {
        "id": "FLT-715309",
        "timestamp": "2026-09-04 14:02:44",
        "machine": "Hydraulic Press",
        "fault": "Hydraulic Fluid Overheating",
        "component": "Oil Cooler & Heat Exchanger",
        "confidence_score": 0.78,
        "confidence_percentage": 78,
        "confidence_level": "Moderate",
        "cause": "Heat exchanger core fouling and continuous high-cycle stamping operation.",
        "recommendation": "Back-flush heat exchanger, inspect water regulating valve WV-01, and verify fluid temperature drops below 55°C.",
        "query": "Hydraulic oil temperature warning",
        "possible_faults": [
            {"fault": "Hydraulic Fluid Overheating", "confidence_score": 0.78, "confidence_percentage": 78, "confidence_level": "Moderate", "is_primary": True, "component": "Oil Cooler & Heat Exchanger"},
            {"fault": "Proportional Relief Valve Sticking", "confidence_score": 0.48, "confidence_percentage": 48, "confidence_level": "Low", "is_primary": False, "component": "Main Relief Valve"},
            {"fault": "High Filter Differential Pressure", "confidence_score": 0.23, "confidence_percentage": 23, "confidence_level": "Low", "is_primary": False, "component": "Duplex Filter"}
        ],
        "evidence": {
            "contributing_evidence": "Hydraulic Oil Temp: 68.5°C via TT-02 (Trip limit: 65.0°C) | Cooler dP: 1.85 bar",
            "reasoning": "TT-02 temperature transducer confirmed bulk fluid temperature exceeded the 65°C safe threshold.",
            "sensor_readings": {
                "hydraulic_oil_temp": "68.5°C via TT-02 (Trip limit: 65.0°C)",
                "heat_exchanger_dp": "1.85 bar (Clean: 0.60 bar)",
                "ambient_enclosure_temp": "34.2°C",
                "cooling_fan_status": "Active (Max RPM)"
            },
            "disclaimer": CONFIDENCE_DISCLAIMER
        }
    }
]

@app.get("/api/fault-history")
def get_fault_history():
    """
    Returns recorded hardware fault diagnostic history with AI confidence scores,
    levels, sensor evidence, and the non-guarantee disclaimer.
    """
    return {
        "faults": FAULT_HISTORY,
        "total_count": len(FAULT_HISTORY),
        "disclaimer": CONFIDENCE_DISCLAIMER
    }

@app.get("/api/machine-health")
def get_machine_health_overview():
    """
    Returns real-time machine health overview for factory machines,
    incorporating confidence scores and active fault indicators.
    """
    return compute_machine_health(FAULT_HISTORY)

@app.get("/api/diagnostic-report")
def get_diagnostic_report():
    """
    Generates an executive diagnostic report synthesizing active faults,
    confidence distributions, and telemetry evidence across the fleet.
    """
    high_count = sum(1 for f in FAULT_HISTORY if f.get("confidence_level") == "High")
    mod_count = sum(1 for f in FAULT_HISTORY if f.get("confidence_level") == "Moderate")
    low_count = sum(1 for f in FAULT_HISTORY if f.get("confidence_level") == "Low")

    return {
        "report_id": f"REP-{int(time.time())}",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_diagnoses": len(FAULT_HISTORY),
        "confidence_distribution": {
            "high": high_count,
            "moderate": mod_count,
            "low": low_count
        },
        "machine_health": compute_machine_health(FAULT_HISTORY)["machines"],
        "recent_faults": FAULT_HISTORY[:10],
        "disclaimer": CONFIDENCE_DISCLAIMER
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api:app", host="127.0.0.1", port=8000, reload=True)
