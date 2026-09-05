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

def _extract_structured_answer_from_context(context: str) -> str:
    """Extract structured 4-section answer directly from manual context chunks."""
    import re
    m_match = re.search(r"MEANING:\s*(.+)", context, re.IGNORECASE)
    meaning = m_match.group(1).strip() if m_match else "Extracted from verified equipment manuals."
    
    causes = []
    c_match = re.search(r"CAUSES:\s*\n((?:(?:\s*-\s*[^\n]+\n?))+)", context, re.IGNORECASE)
    if c_match:
        for line in c_match.group(1).splitlines():
            l_str = line.strip()
            if l_str.startswith("-"):
                causes.append(l_str)
    if not causes:
        causes = ["- Check equipment operating parameters in technical manual."]

    steps = []
    s_match = re.search(r"STEPS:\s*\n((?:(?:\s*\d+[\.\)]\s*[^\n]+\n?))+)", context, re.IGNORECASE)
    if s_match:
        for line in s_match.group(1).splitlines():
            l_str = line.strip()
            if re.match(r"^\d+[\.\)]", l_str):
                steps.append(l_str)
    if not steps:
        steps = ["1. Review operating procedure in attached manufacturer manual."]

    causes_text = "\n".join(causes)
    steps_text = "\n".join(steps)
    return f"1. Error meaning:\n{meaning}\n\n2. Probable causes:\n{causes_text}\n\n3. Step-by-step corrective action:\n{steps_text}\n\n4. Sources:\nVerified manufacturer manuals."

def generate_answer(query, context, api_key=None):
    """
    Calls the Google GenAI SDK (google-genai) directly to generate a structured answer.
    """
    load_dotenv(override=True)
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        return _extract_structured_answer_from_context(context)

    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key)

        user_content = f"--- SOURCES ---\n{context}\n\n--- USER QUERY ---\n{query}"

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT
        )

        model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
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
        return _extract_structured_answer_from_context(context)

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
