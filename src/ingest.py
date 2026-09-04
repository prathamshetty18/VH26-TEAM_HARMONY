import os
import re
from typing import List, Dict, Any

def load_and_chunk_manuals(manuals_dir="data/manuals") -> List[Dict[str, Any]]:
    """
    Reads manual text files from manuals_dir, normalizes and splits them into structured
    chunks based on 'SECTION:' markers, and extracts error_code, machine, model, and page.
    Supports both single-section header format and dual-section error code/troubleshooting format.
    """
    chunks = []
    
    if not os.path.exists(manuals_dir):
        return chunks

    for filename in sorted(os.listdir(manuals_dir)):
        if not filename.endswith(".txt"):
            continue
            
        filepath = os.path.join(manuals_dir, filename)
        
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Global header metadata
        global_machine = None
        global_model = None

        m_match = re.search(r"^MACHINE:\s*(.+)$", content, re.MULTILINE)
        if m_match:
            global_machine = m_match.group(1).strip()

        mod_match = re.search(r"^MODEL:\s*(.+)$", content, re.MULTILINE)
        if mod_match:
            global_model = mod_match.group(1).strip()

        # Normalize format: if ERROR CODE: precedes SECTION:, swap so SECTION: comes first
        normalized = re.sub(
            r"(?m)^ERROR CODE:\s*([^\n]+)\s*\n\s*SECTION:\s*([^\n]+)$",
            r"SECTION: \2\nERROR CODE: \1",
            content
        )

        sections = re.split(r"(?m)(?=^SECTION:)", normalized)

        current_error_code = None
        for sec in sections:
            sec_text = sec.strip()
            if not sec_text or not sec_text.startswith("SECTION:"):
                continue

            # Extract section title
            sec_title_match = re.search(r"^SECTION:\s*(.+)$", sec_text, re.MULTILINE)
            section_title = sec_title_match.group(1).strip() if sec_title_match else "General"

            # Check for error code in this chunk
            err_match = re.search(r"^ERROR CODE:\s*(.+)$", sec_text, re.MULTILINE)
            if err_match:
                current_error_code = err_match.group(1).strip()
            else:
                # Regex fallback for error codes in section title e.g. E101, H205, R101, or SYM-...
                title_err_match = re.search(r"\b([A-Z]-?\d{3,4}|SYM-[A-Z0-9-]+)\b", section_title)
                if title_err_match:
                    raw_tc = title_err_match.group(1).strip()
                    current_error_code = raw_tc.replace("-", "") if not raw_tc.startswith("SYM-") else raw_tc

            # Machine / Model
            sec_machine = global_machine
            chunk_m_match = re.search(r"^MACHINE:\s*(.+)$", sec_text, re.MULTILINE)
            if chunk_m_match:
                sec_machine = chunk_m_match.group(1).strip()

            sec_model = global_model
            chunk_mod_match = re.search(r"^MODEL:\s*(.+)$", sec_text, re.MULTILINE)
            if chunk_mod_match:
                sec_model = chunk_mod_match.group(1).strip()

            page_match = re.search(r"^PAGE:\s*(.+)$", sec_text, re.MULTILINE)
            page_num = page_match.group(1).strip() if page_match else None

            # Ensure error code and machine context are present in text for high-fidelity retrieval
            chunk_text = sec_text
            if current_error_code and f"ERROR CODE: {current_error_code}" not in chunk_text:
                chunk_text = f"ERROR CODE: {current_error_code}\n" + chunk_text

            chunks.append({
                "text": chunk_text,
                "machine": sec_machine or "Unknown",
                "model": sec_model or "Unknown",
                "manual": filename,
                "section": section_title,
                "page": page_num,
                "error_code": current_error_code
            })

    return chunks

if __name__ == "__main__":
    parsed_chunks = load_and_chunk_manuals()
    print(f"Total chunks parsed: {len(parsed_chunks)}")
    for i, c in enumerate(parsed_chunks[:5]):
        print(f"--- Chunk {i+1} ---")
        print(f"Machine: {c['machine']} | Model: {c['model']} | Manual: {c['manual']}")
        print(f"Section: {c['section']} | Page: {c['page']} | Error Code: {c['error_code']}")
        print(f"Text Preview:\n{c['text'][:140]}...\n")
