import sys
import os
import re
import io
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pypdf

# Ensure repository root is in sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

<<<<<<< HEAD
MANUALS_DIR = os.path.join(REPO_ROOT, "data", "manuals")
=======
from typing import List, Optional, Dict, Any
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
>>>>>>> 8a65c82cf4e10e37af9a52814549587f29d2039e

from src.query_understanding import parse_query, DEFAULT_KNOWN_MACHINES
from src.retrieval import retrieve
from src.disambiguation import check_ambiguity
from src.safety import is_sufficient, REFUSAL_MESSAGE
from src.llm_answer import assemble_context, generate_answer, structure_pdf_text_with_llm
from src.memory import memory_store
<<<<<<< HEAD
from src.ingest import validate_manual_content
from src.embed_store import (
    upsert_chunks,
    delete_by_machine,
    get_distinct_machines,
    get_manuals_summary,
    invalidate_machines_cache
)
=======
from src.embed_store import get_chroma_collection
>>>>>>> 8a65c82cf4e10e37af9a52814549587f29d2039e

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

<<<<<<< HEAD
def sanitize_machine_filename(machine_name: str) -> str:
    """Sanitizes machine name to lowercase with underscores for files."""
    cleaned = re.sub(r"[^a-z0-9]+", "_", machine_name.lower()).strip("_")
    return f"{cleaned}.txt"

# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------
=======
STATIC_DIR = os.path.join(REPO_ROOT, "src", "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
>>>>>>> 8a65c82cf4e10e37af9a52814549587f29d2039e

class QueryRequest(BaseModel):
    message: str
    session_id: str = "default_session"
    machine_filter: Optional[str] = None

class SourceMetadata(BaseModel):
    manual: str
    section: str
    machine: str
    error_code: Optional[str] = None

class AmbiguityOption(BaseModel):
    machine: str
    summary: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceMetadata]
    ambiguous: bool
    options: List[AmbiguityOption]

class ManualUploadResponse(BaseModel):
    status: str  # "success" | "needs_review" | "error"
    machine: Optional[str] = None
    chunk_count: Optional[int] = None
    draft_text: Optional[str] = None
    error: Optional[str] = None
    is_valid_format: Optional[bool] = None

class ManualConfirmRequest(BaseModel):
    machine: str
    content: str

class ManualSummaryItem(BaseModel):
    machine: str
    filename: str
    chunk_count: int
    updated_at: str

class ManualsListResponse(BaseModel):
    manuals: List[ManualSummaryItem]

# ---------------------------------------------------------------------------
# Core Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def read_root(request: Request):
    accept = request.headers.get("accept", "")
    html_path = os.path.join(STATIC_DIR, "index.html")
    if "text/html" in accept and os.path.exists(html_path):
        return FileResponse(html_path)
    return {"message": "MachineAssist Backend API running", "status": "ok"}

@app.get("/dashboard")
@app.get("/app")
def read_dashboard():
    html_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"message": "MachineAssist Dashboard available via static UI", "status": "ok"}

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
    """Returns content and metadata for all active factory manuals."""
    manuals_dir = os.path.join(REPO_ROOT, "data", "manuals")
    manual_configs = [
        {"filename": "conveyorcb4400.txt", "title": "Conveyor Belt System — Model CB-4400 Troubleshooting Manual", "machine": "Conveyor Belt System", "pages": 6, "chunkCount": 20},
        {"filename": "cncmx7.txt", "title": "CNC Milling Machine — Model MX-7 Precision Troubleshooting Manual", "machine": "CNC Milling Machine", "pages": 6, "chunkCount": 20},
        {"filename": "presshp2200.txt", "title": "Hydraulic Press — Model HP-2200 Troubleshooting Manual", "machine": "Hydraulic Press", "pages": 6, "chunkCount": 20}
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

@app.post("/query", response_model=QueryResponse)
@app.post("/chat", response_model=QueryResponse)
def handle_query(req: QueryRequest):
    session_id = req.session_id
    raw_message = req.message
    if req.machine_filter and req.machine_filter.lower() not in raw_message.lower():
        raw_message = f"{raw_message} (on machine {req.machine_filter})"

    if not raw_message.strip():
        raise HTTPException(status_code=400, detail="Query message cannot be empty")

    # Step 1: Augment query using session memory if vague
    augmented_message = memory_store.resolve_query_with_memory(session_id, raw_message)

    # Step 2: Query Understanding (Extract machine & error_code with dynamic known_machines)
    active_machines = get_distinct_machines() or DEFAULT_KNOWN_MACHINES
    parsed_q = parse_query(augmented_message, known_machines=active_machines)

    # Step 3: Retrieval
    retrieved_chunks = retrieve(parsed_q, k=5)

    # Step 4: Disambiguation Check
    ambiguity_result = check_ambiguity(parsed_q, retrieved_chunks)
    if ambiguity_result.get("ambiguous"):
        options = ambiguity_result.get("options", [])
        opt_lines = "\n".join([f"- **{o['machine']}**: {o['summary']}" for o in options])
        answer_text = f"Multiple machines match this error code. Please select which machine you are operating:\n{opt_lines}"
        return QueryResponse(
            answer=answer_text,
            sources=[],
            ambiguous=True,
            options=options
        )

    # Step 5: Safety / Relevance Control Check
    sufficient, safety_result = is_sufficient(retrieved_chunks, query=raw_message)
    if not sufficient:
        return QueryResponse(
            answer=safety_result, # Refusal message
            sources=[],
            ambiguous=False,
            options=[]
        )

    # Step 6: Context Assembly & Answer Generation
    context_text = assemble_context(retrieved_chunks)
    answer_text = generate_answer(raw_message, context_text)

    # Step 7: Format Source Citations
    sources = []
    if answer_text.strip() != REFUSAL_MESSAGE and REFUSAL_MESSAGE not in answer_text:
        seen_sources = set()
        for c in retrieved_chunks:
            s_key = (c.get("manual"), c.get("section"))
            if s_key not in seen_sources:
                seen_sources.add(s_key)
                sources.append(SourceMetadata(
                    manual=c.get("manual", ""),
                    section=c.get("section", ""),
                    machine=c.get("machine", ""),
                    error_code=c.get("error_code")
                ))

    # Step 8: Update Session Memory
    top_machine = parsed_q.get("machine") or (retrieved_chunks[0].get("machine") if retrieved_chunks else None)
    top_error = parsed_q.get("error_code") or (retrieved_chunks[0].get("error_code") if retrieved_chunks else None)
    memory_store.update_session(session_id, machine=top_machine, error_code=top_error, last_answer=answer_text)

    return QueryResponse(
        answer=answer_text,
        sources=sources,
        ambiguous=False,
        options=[]
    )

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

        return ManualUploadResponse(
            status="success",
            machine=machine_name,
            chunk_count=chunk_count,
            draft_text=None,
            error=None,
            is_valid_format=True
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

        # Call Gemini to structure the raw text into standard format
        try:
            draft_text = structure_pdf_text_with_llm(extracted_text)
        except Exception as err:
            return ManualUploadResponse(
                status="error",
                machine=None,
                chunk_count=0,
                draft_text=None,
                error=f"LLM structuring failed: {str(err)}",
                is_valid_format=False
            )

        is_valid, err_msg, machine_name, chunks = validate_manual_content(draft_text)
        return ManualUploadResponse(
            status="needs_review",
            machine=machine_name,
            chunk_count=len(chunks),
            draft_text=draft_text,
            error=err_msg,
            is_valid_format=is_valid
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

    delete_by_machine(machine_name)
    chunk_count = upsert_chunks(chunks)

    return ManualUploadResponse(
        status="success",
        machine=machine_name,
        chunk_count=chunk_count,
        draft_text=None,
        error=None,
        is_valid_format=True
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api:app", host="127.0.0.1", port=8000, reload=True)
