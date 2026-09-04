import os
import re

def load_and_chunk_manuals(manuals_dir="data/manuals"):
    """
    Reads manual text files from manuals_dir, splits them into structured chunks
    based on 'SECTION:' markers, and extracts metadata.
    """
    chunks = []
    
    if not os.path.exists(manuals_dir):
        return chunks

    for filename in os.listdir(manuals_dir):
        if not (filename.endswith(".txt") or filename.endswith(".pdf")):
            continue
            
        filepath = os.path.join(manuals_dir, filename)
        
        # Read text content
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Global header metadata fallback
        global_machine = None
        global_model = None

        m_match = re.search(r"^MACHINE:\s*(.+)$", content, re.MULTILINE)
        if m_match:
            global_machine = m_match.group(1).strip()

        mod_match = re.search(r"^MODEL:\s*(.+)$", content, re.MULTILINE)
        if mod_match:
            global_model = mod_match.group(1).strip()

        # Split content into sections using SECTION: as delimiter
        sections = re.split(r"(?=SECTION:)", content)

        for sec in sections:
            sec_text = sec.strip()
            if not sec_text:
                continue

            # Extract section title
            section_title = "General"
            sec_title_match = re.search(r"^SECTION:\s*(.+)$", sec_text, re.MULTILINE)
            if sec_title_match:
                section_title = sec_title_match.group(1).strip()

            # Extract chunk-specific machine
            sec_machine = global_machine
            chunk_m_match = re.search(r"^MACHINE:\s*(.+)$", sec_text, re.MULTILINE)
            if chunk_m_match:
                sec_machine = chunk_m_match.group(1).strip()

            # Extract chunk-specific model
            sec_model = global_model
            chunk_mod_match = re.search(r"^MODEL:\s*(.+)$", sec_text, re.MULTILINE)
            if chunk_mod_match:
                sec_model = chunk_mod_match.group(1).strip()

            # Extract error code
            error_code = None
            err_match = re.search(r"^ERROR CODE:\s*(.+)$", sec_text, re.MULTILINE)
            if err_match:
                error_code = err_match.group(1).strip()
            else:
                # Regex fallback for error codes in section title e.g. E101
                title_err_match = re.search(r"\b(E\d{3})\b", section_title)
                if title_err_match:
                    error_code = title_err_match.group(1).strip()

            chunks.append({
                "text": sec_text,
                "machine": sec_machine or "Unknown",
                "model": sec_model or "Unknown",
                "manual": filename,
                "section": section_title,
                "error_code": error_code
            })

    return chunks

if __name__ == "__main__":
    parsed_chunks = load_and_chunk_manuals()
    print(f"Total chunks parsed: {len(parsed_chunks)}")
    for i, c in enumerate(parsed_chunks):
        print(f"--- Chunk {i+1} ---")
        print(f"Machine: {c['machine']} | Model: {c['model']} | Manual: {c['manual']}")
        print(f"Section: {c['section']} | Error Code: {c['error_code']}")
        print(f"Text Preview: {c['text'][:100]}...\n")
