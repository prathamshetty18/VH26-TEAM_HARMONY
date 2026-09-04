import os
import sys
import re
from typing import Optional
from dotenv import load_dotenv

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

load_dotenv()

try:
    from src.safety import REFUSAL_MESSAGE
except ImportError:
    from safety import REFUSAL_MESSAGE

# Single unified source of truth for model name
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

SYSTEM_PROMPT = f"""You are MachineAssist, an expert factory troubleshooting assistant. Your task is to answer user queries using ONLY the provided manual sources.

Format your answer using the following 4 sections:
1. Error meaning: Explain the error code or symptom as specified in the sources.
2. Probable causes: List the causes provided in the sources (or state None if not listed).
3. Step-by-step corrective action: List the troubleshooting steps from the sources (or state None if not listed).
4. Sources: State the manual file and section name.

Important: If the provided sources do NOT contain any information about the query, reply with ONLY:
"{REFUSAL_MESSAGE}"
"""

PDF_STRUCTURING_SYSTEM_PROMPT = """You are a technical document parser. Your job is to convert unstructured industrial machine manual text into a standardized structure conforming to the specification below.

Do NOT invent any information, causes, error codes, or steps that are not present in the source text.
Preserve exact error codes, numbers, parameters, and descriptions.

The structure MUST follow this exact format:
MACHINE: <Machine Name>
MODEL: <Model Name>

ERROR CODE: <Code or Symptom ID e.g. E101 or SYM-OVERHEAT>
SECTION: <Descriptive Section Title>
PAGE: <Page number if known, or 1>
MEANING: <One or two sentences explaining the error/symptom>
CAUSES:
- <Cause 1>
- <Cause 2>

SECTION: <Troubleshooting Section Title>
PAGE: <Page number if known, or 1>
STEPS:
1. <Action Step 1>
2. <Action Step 2>

...Repeat for each error code or symptom block in the manual.
Output ONLY the structured plain text with no markdown code fences, no extra preamble, and no commentary.
"""

def assemble_context(chunks):
    """
    Formats retrieved chunks into a labeled block for LLM prompt.
    """
    context_blocks = []
    for i, chunk in enumerate(chunks, 1):
        block = f"[Source {i}]\n"
        block += f"Machine: {chunk.get('machine', 'Unknown')}\n"
        block += f"Manual: {chunk.get('manual', 'Unknown')}\n"
        block += f"Section: {chunk.get('section', 'General')}\n\n"
        block += f"{chunk.get('text', '')}\n"
        context_blocks.append(block)
    return "\n---\n".join(context_blocks)

def generate_answer(query, context, api_key=None):
    """
    Calls the Google GenAI SDK (google-genai) directly to generate a structured answer.
    """
    load_dotenv(override=True)
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        # Fallback placeholder if no API key is provided yet
        return f"System Prompt Context:\n{context}\n\n[Placeholder Response - Please set GEMINI_API_KEY in .env to generate live responses via Gemini Flash API]\n1. Error meaning: Extracted from manuals\n2. Probable causes: Listed in manual sections\n3. Corrective action: Follow step-by-step manual instructions"

    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key)

        user_content = f"--- SOURCES ---\n{context}\n\n--- USER QUERY ---\n{query}"

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT
        )

        model_name = os.getenv("GEMINI_MODEL", GEMINI_MODEL)
        response = client.models.generate_content(
            model=model_name,
            contents=user_content,
            config=config
        )

        # Guard: response may be blocked or empty (safety filters / empty generation)
        if not response.candidates:
            return REFUSAL_MESSAGE

        candidate = response.candidates[0]

        finish_reason = getattr(candidate, "finish_reason", None)
        is_stop = False
        if finish_reason is None:
            is_stop = True
        elif hasattr(finish_reason, "name") and finish_reason.name == "STOP":
            is_stop = True
        elif hasattr(finish_reason, "value") and finish_reason.value in ("STOP", 1):
            is_stop = True
        elif "STOP" in str(finish_reason).upper():
            is_stop = True

        if not is_stop:
            # Blocked by safety filters or other abnormal stop — do not hallucinate
            return REFUSAL_MESSAGE

        # Safely extract text — .text raises if parts are empty
        text = None
        try:
            text = response.text
        except Exception:
            pass

        if not text or not text.strip():
            return REFUSAL_MESSAGE

        return text

    except Exception as e:
        print(f"[generate_answer error]: {type(e).__name__}: {e}")
        # Fallback if API call fails e.g. quota limit (429) or connection error
        # Construct structured answer from context so system remains operational during rate limits
        return f"1. Error meaning (Context Fallback):\n{context}\n2. Probable causes: See context above\n3. Step-by-step corrective action: Follow manual steps in context\n4. Sources: Manual sections cited above"

def structure_pdf_text_with_llm(raw_text: str, api_key: Optional[str] = None) -> str:
    """
    Calls Gemini to format raw extracted PDF text into MANUAL_FORMAT_SPEC.md standard.
    """
    load_dotenv(override=True)
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is required to structure PDF content with Gemini.")

    from google import genai
    from google.genai import types
    client = genai.Client(api_key=api_key)

    config = types.GenerateContentConfig(
        system_instruction=PDF_STRUCTURING_SYSTEM_PROMPT,
        temperature=0.1
    )

    model_name = os.getenv("GEMINI_MODEL", GEMINI_MODEL)
    response = client.models.generate_content(
        model=model_name,
        contents=raw_text,
        config=config
    )

    if not response or not response.text:
        raise RuntimeError("Gemini returned empty structured text.")

    text = response.text.strip()
    text = re.sub(r"^```[a-zA-Z]*\n", "", text)
    text = re.sub(r"\n```$", "", text).strip()
    return text

if __name__ == "__main__":
    test_chunks = [
        {
            "machine": "CNC-100",
            "manual": "cnc100.txt",
            "section": "E101 Troubleshooting",
            "text": "E101 MEANING: Excessive motor temperature.\nCAUSES:\n- Cooling fan failure\n- Blocked ventilation\nSTEPS:\n1. Switch off the machine.\n2. Inspect cooling fan.\n3. Clean ventilation openings."
        }
    ]
    ctx = assemble_context(test_chunks)
    ans = generate_answer("What should I do for E101 on CNC-100?", ctx)
    print("Generated Answer:\n", ans)
