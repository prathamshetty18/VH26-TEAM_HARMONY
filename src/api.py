from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from src.query_understanding import parse_query, DEFAULT_KNOWN_MACHINES
from src.retrieval import retrieve
from src.disambiguation import check_ambiguity
from src.safety import is_sufficient, REFUSAL_MESSAGE
from src.llm_answer import assemble_context, generate_answer
from src.memory import memory_store

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

class QueryRequest(BaseModel):
    message: str
    session_id: str = "default_session"

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

@app.get("/")
def read_root():
    return {"message": "MachineAssist Backend API running", "status": "ok"}

@app.get("/machines")
def get_machines():
    """Returns list of known machine names for UI dropdown."""
    return {"machines": DEFAULT_KNOWN_MACHINES}

@app.post("/query", response_model=QueryResponse)
def handle_query(req: QueryRequest):
    session_id = req.session_id
    raw_message = req.message

    if not raw_message.strip():
        raise HTTPException(status_code=400, detail="Query message cannot be empty")

    # Step 1: Augment query using session memory if vague
    augmented_message = memory_store.resolve_query_with_memory(session_id, raw_message)

    # Step 2: Query Understanding (Extract machine & error_code)
    parsed_q = parse_query(augmented_message)

    # Step 3: Retrieval
    retrieved_chunks = retrieve(parsed_q, k=5)

    # Step 4: Disambiguation Check
    ambiguity_result = check_ambiguity(parsed_q, retrieved_chunks)
    if ambiguity_result.get("ambiguous"):
        return QueryResponse(
            answer="Multiple machines match this error code. Please select which machine you are operating:",
            sources=[],
            ambiguous=True,
            options=ambiguity_result.get("options", [])
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
    # If the LLM self-refused (second-line defense), clear sources — no phantom citations.
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
