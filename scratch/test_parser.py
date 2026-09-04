import re
import os

def load_and_chunk_manuals(manuals_dir="data/manuals"):
    chunks = []
    if not os.path.exists(manuals_dir):
        return chunks

    for filename in sorted(os.listdir(manuals_dir)):
        if not filename.endswith(".txt"):
            continue
        filepath = os.path.join(manuals_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

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
                # Regex fallback for error codes in section title e.g. E101, H205, or SYM-...
                title_err_match = re.search(r"\b([EH]\d{3}|SYM-[A-Z0-9-]+)\b", section_title)
                if title_err_match:
                    current_error_code = title_err_match.group(1).strip()

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

            # Ensure error code is present in chunk text for embedding and search
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
    chunks = load_and_chunk_manuals()
    print("Total chunks parsed:", len(chunks))
    by_manual = {}
    for c in chunks:
        by_manual.setdefault(c["manual"], []).append(c)
    for m, m_chunks in by_manual.items():
        print(f"\nManual: {m} ({len(m_chunks)} chunks)")
        for c in m_chunks:
            print(f"  Sec: {c['section']:<35} | Code: {str(c['error_code']):<18} | Page: {c['page']}")
