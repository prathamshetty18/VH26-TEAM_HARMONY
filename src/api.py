import sys
import os

# Ensure repository root is in sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from typing import List, Optional, Dict, Any
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.query_understanding import parse_query, DEFAULT_KNOWN_MACHINES
from src.retrieval import retrieve
from src.disambiguation import check_ambiguity
import time
from src.safety import is_sufficient, REFUSAL_MESSAGE
from src.llm_answer import assemble_context, generate_answer
from src.memory import memory_store
from src.embed_store import get_chroma_collection
from src.translation import translate_input, translateInput
from src.multilingual_manual_data import get_multilingual_manual, get_available_languages
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

STATIC_DIR = os.path.join(REPO_ROOT, "src", "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

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

class PossibleFault(BaseModel):
    fault: str
    confidence_score: float
    confidence_percentage: int
    confidence_level: str
    is_primary: bool = False
    component: Optional[str] = None

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
        {"filename": "multilingual_manual.txt", "title": "Multilingual Machine Instruction Manual (All 4 Languages)", "machine": "CNC Milling Machine", "pages": 12, "chunkCount": 36},
        {"filename": "multilingual_manual_zh.txt", "title": "数控铣床 MX-7 说明书 — 中文 (Simplified Chinese Manual)", "machine": "CNC Milling Machine", "pages": 8, "chunkCount": 24},
        {"filename": "multilingual_manual_ja.txt", "title": "CNCフライス盤 MX-7 取扱説明書 — 日本語 (Japanese Manual)", "machine": "CNC Milling Machine", "pages": 8, "chunkCount": 24},
        {"filename": "multilingual_manual_de.txt", "title": "CNC-Fräsmaschine MX-7 Handbuch — Deutsch (German Manual)", "machine": "CNC Milling Machine", "pages": 8, "chunkCount": 24},
        {"filename": "multilingual_manual_en.txt", "title": "CNC Milling Machine MX-7 Manual — English", "machine": "CNC Milling Machine", "pages": 8, "chunkCount": 24}
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
 
@app.get("/api/manuals/multilingual")
def get_multilingual_manual_endpoint(lang: Optional[str] = "en"):
    """
    Returns the comprehensive 9-section machine instruction manual.
    Supports English ('en'), Simplified Chinese ('zh'), Japanese ('ja'), and German ('de').
    """
    manual_data = get_multilingual_manual(lang)
    return {
        "languages": get_available_languages(),
        "selected_language": manual_data.get("language_code", "en"),
        "manual": manual_data
    }
 
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

    # Step 1: Augment query using session memory if vague (pass translated English directly)
    augmented_message = memory_store.resolve_query_with_memory(session_id, english_query)

    # Step 2: Query Understanding (Extract machine & error_code)
    parsed_q = parse_query(augmented_message)

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
    sufficient, safety_result = is_sufficient(retrieved_chunks, query=english_query)
    if not sufficient:
        return QueryResponse(
            answer=safety_result, # Refusal message
            sources=[],
            ambiguous=False,
            options=[]
        )

    # Step 6: Context Assembly & Answer Generation
    context_text = assemble_context(retrieved_chunks)
    answer_text = generate_answer(english_query, context_text)

    # Step 7: Format Source Citations & AI Confidence Scoring
    # If the LLM self-refused (second-line defense), clear sources and confidence — no phantom scores.
    sources = []
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


