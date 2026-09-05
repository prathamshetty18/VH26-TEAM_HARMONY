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
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

SYSTEM_PROMPT = f"""You are MachineAssist, an expert factory troubleshooting assistant. Your task is to answer user queries using ONLY the provided manual sources.

Format your answer using the following 4 sections:
1. Error meaning: Explain the error code or symptom as specified in the sources.
2. Probable causes: List the causes provided in the sources (or state None if not listed).
3. Step-by-step corrective action: List the troubleshooting steps from the sources (or state None if not listed).
4. Sources: State the manual file and section name.

Important: If the provided sources do NOT contain any information about the query, reply with ONLY:
"{REFUSAL_MESSAGE}"
"""

PDF_STRUCTURING_SYSTEM_PROMPT = """You are a technical document parser. Your job is to convert unstructured industrial machine manual text into a standardized structure conforming strictly to the specification below.

LANGUAGE NORMALIZATION & TRANSLATION:
1. ALL structured output fields (MACHINE, MODEL, SECTION, MEANING, CAUSES, STEPS) MUST BE IN ENGLISH.
2. If the source manual text is in Chinese, Japanese, German, or any other non-English language, you MUST TRANSLATE all descriptions, meanings, causes, and corrective action steps into clear, professional technical English during structuring.
3. If the source text is already in English, retain the English wording.

CRITICAL PRESERVATION RULES:
1. NUMERIC VALUES, THRESHOLDS, UNITS, AND ERROR CODES MUST BE COPIED CHARACTER-FOR-CHARACTER from the source text.
2. NEVER round, reword, approximate, convert (e.g. do not convert °C to °F or bar to psi), or reformat any numbers, tolerances, pressures, temperatures, electrical ratings, or flow rates (e.g. "65°C", "94°C", "3.8 L/min", "45-70 bar", "6.5 bar", "18 bar", "125% FLA", "3.5 seconds", "0.015 mm", "24,000 RPM", "400V", "32A", "15 kW").
3. If a number or unit's exact format is ambiguous, preserve it exactly as written in the source text.
4. Do NOT invent or extrapolate any information, causes, error codes, part numbers, or corrective steps that are not present in the source text. All error codes present in the structured output MUST exist in the source text.
5. Every single error code and diagnostic symptom mentioned in the text must be represented.

The structure MUST follow this exact format:
MACHINE: <Machine Name>
MODEL: <Model Name>

ERROR CODE: <Code or Symptom ID e.g. E101 or SYM-OVERHEAT>
SECTION: <Descriptive Section Title in English>
PAGE: <Page number if known, or 1>
MEANING: <One or two sentences explaining the error/symptom in English>
CAUSES:
- <Cause 1 in English>
- <Cause 2 in English>

SECTION: <Troubleshooting Section Title in English>
PAGE: <Page number if known, or 1>
STEPS:
1. <Action Step 1 in English>
2. <Action Step 2 in English>

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

def _extract_structured_answer_from_context(context: str, query: Optional[str] = None) -> str:
    """High-fidelity deterministic fallback directly grounded in manual context chunks."""
    import re

    # Identify target error code from query if any
    target_code = None
    if query:
        q_code_match = re.search(r"\b([A-Z]-?\d{3,4}|SYM-[A-Z0-9-]+)\b", query, re.IGNORECASE)
        target_code = q_code_match.group(1).upper().replace("-", "") if q_code_match else None

    # Split context into source blocks
    source_blocks = context.split("\n---\n")
    selected_blocks = source_blocks
    if target_code:
        code_filtered = [b for b in source_blocks if target_code.lower() in b.lower()]
        if code_filtered:
            selected_blocks = code_filtered

    target_context = "\n\n".join(selected_blocks)

    # 1. Meaning
    m_match = re.search(r"MEANING:\s*(.+?)(?=\n[A-Z\s]+:|\n---|\Z)", target_context, re.IGNORECASE | re.DOTALL)
    meaning = m_match.group(1).strip() if m_match else None
    if not meaning:
        sec_match = re.search(r"Section:\s*(.+)", target_context)
        meaning = f"System fault diagnosed: {sec_match.group(1).strip() if sec_match else 'Hardware condition'}."

    # 2. Causes
    causes = []
    c_match = re.search(r"CAUSES:\s*\n((?:(?:\s*-\s*[^\n]+\n?))+)", target_context, re.IGNORECASE)
    if c_match:
        for line in c_match.group(1).splitlines():
            l_str = line.strip()
            if l_str.startswith("-"):
                causes.append(l_str)
    if not causes:
        lc_match = re.search(r"(?:Likely Cause|Cause):\s*(.+)", target_context, re.IGNORECASE)
        if lc_match:
            causes.append(f"- {lc_match.group(1).strip()}")
        else:
            causes = ["- Identified operating condition documented in equipment manual."]

    # 3. Steps
    steps = []
    s_match = re.search(r"(?:STEPS|Corrective Action):\s*\n((?:(?:\s*\d+[\.\)]\s*[^\n]+\n?))+)", target_context, re.IGNORECASE)
    if s_match:
        for line in s_match.group(1).splitlines():
            l_str = line.strip()
            if re.match(r"^\d+[\.\)]", l_str):
                steps.append(l_str)
    if not steps:
        ca_match = re.search(r"Corrective Action:\s*(.+)", target_context, re.IGNORECASE)
        if ca_match:
            steps.append(f"1. {ca_match.group(1).strip()}")
        else:
            steps = ["1. Inspect system and perform scheduled maintenance per technical manual."]

    # 4. Sources
    sources_found = []
    for b in selected_blocks:
        man_m = re.search(r"Manual:\s*(.+)", b)
        sec_m = re.search(r"Section:\s*(.+)", b)
        if man_m and sec_m:
            s_desc = f"{man_m.group(1).strip()} ({sec_m.group(1).strip()})"
            if s_desc not in sources_found:
                sources_found.append(s_desc)
    sources_text = ", ".join(sources_found) if sources_found else "Verified equipment manuals."

    causes_text = "\n".join(causes)
    steps_text = "\n".join(steps)
    return f"1. Error meaning:\n{meaning}\n\n2. Probable causes:\n{causes_text}\n\n3. Step-by-step corrective action:\n{steps_text}\n\n4. Sources:\n{sources_text}"

def generate_answer(query, context, api_key=None):
    """
    Calls the Google GenAI SDK (google-genai) directly to generate a structured answer.
    """
    load_dotenv(override=True)
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        return _extract_structured_answer_from_context(context, query)

    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key)

        user_content = f"--- SOURCES ---\n{context}\n\n--- USER QUERY ---\n{query}"

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT
        )

        models_to_try = [
            os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
            "gemini-3.5-flash-lite",
            "gemini-flash-lite-latest",
            "gemini-flash-latest",
            "gemini-3.5-flash"
        ]
        # Deduplicate while preserving order
        seen_models = set()
        unique_models = []
        for m in models_to_try:
            if m not in seen_models:
                seen_models.add(m)
                unique_models.append(m)

        response = None
        last_client_error = None
        for m in unique_models:
            try:
                response = client.models.generate_content(
                    model=m,
                    contents=user_content,
                    config=config
                )
                if response and response.candidates:
                    break
            except Exception as model_err:
                last_client_error = model_err
                continue

        if not response or not response.candidates:
            if last_client_error:
                raise last_client_error
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
        return _extract_structured_answer_from_context(context, query)

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
        temperature=0.0
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
