import os
import sys
from dotenv import load_dotenv

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

load_dotenv()

try:
    from src.safety import REFUSAL_MESSAGE
except ImportError:
    from safety import REFUSAL_MESSAGE

SYSTEM_PROMPT = f"""You are MachineAssist, an expert factory troubleshooting assistant. Your task is to answer user queries using ONLY the provided manual sources.

Format your answer using the following 4 sections:
1. Error meaning: Explain the error code or symptom as specified in the sources.
2. Probable causes: List the causes provided in the sources (or state None if not listed).
3. Step-by-step corrective action: List the troubleshooting steps from the sources (or state None if not listed).
4. Sources: State the manual file and section name.

Important: If the provided sources do NOT contain any information about the query, reply with ONLY:
"{REFUSAL_MESSAGE}"
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

        model_name = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
        response = client.models.generate_content(
            model=model_name,
            contents=user_content,
            config=config
        )

        # Guard: response may be blocked or empty (safety filters / empty generation)
        if not response.candidates:
            return REFUSAL_MESSAGE

        candidate = response.candidates[0]

        # finish_reason values: STOP=1 (normal), SAFETY=3 (blocked), OTHER non-1 = abnormal
        finish_reason = getattr(candidate, "finish_reason", None)
        # finish_reason is an enum; value 1 == STOP (normal completion)
        if finish_reason is not None and hasattr(finish_reason, "value"):
            reason_val = finish_reason.value
        else:
            reason_val = finish_reason  # may already be int or None

        if reason_val not in (None, 1):
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
        # Fallback if API call fails e.g. quota limit (429) or connection error
        # Construct structured answer from context so system remains operational during rate limits
        return f"1. Error meaning (Context Fallback):\n{context}\n2. Probable causes: See context above\n3. Step-by-step corrective action: Follow manual steps in context\n4. Sources: Manual sections cited above"

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
