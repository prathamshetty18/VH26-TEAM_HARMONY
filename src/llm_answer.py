import os
from dotenv import load_dotenv

load_dotenv()

from src.safety import REFUSAL_MESSAGE

SYSTEM_PROMPT = f"""You are MachineAssist, an expert factory troubleshooting assistant. Answer ONLY using the information in the provided sources below. Do not use outside knowledge.

CRITICAL INSTRUCTION:
If the provided sources do NOT contain enough information to answer the user's specific question, reply with ONLY this exact string:
"{REFUSAL_MESSAGE}"
Do NOT output any numbered sections, bullet points, or "N/A" fields if the sources lack the necessary information.

If and only if the sources contain sufficient information to answer the question, structure your answer as:
1. Error meaning
2. Probable causes
3. Step-by-step corrective action
4. Sources (manual name, section reference)
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
        client = genai.Client(api_key=api_key)
        
        prompt = f"{SYSTEM_PROMPT}\n\n--- SOURCES ---\n{context}\n\n--- USER QUERY ---\n{query}"
        
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        # Fallback if API call fails e.g. quota or connection error
        return f"[Error calling Gemini API: {str(e)}]\n\nBased on retrieved context:\n{context}"

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
