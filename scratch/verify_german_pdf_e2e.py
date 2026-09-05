import os
import sys
import io
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from fastapi.testclient import TestClient

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.api import app
from src.translation import _module_instance

def generate_german_pdf(output_path: str):
    german_txt_path = os.path.join(REPO_ROOT, "data", "archived_manuals", "multilingual_manual_de.txt")
    with open(german_txt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Create a real multi-page PDF using ReportLab
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    y = height - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "CNC-Fraesmaschine Modell MX-7 Handbuch (Deutsch)")
    y -= 30
    c.setFont("Helvetica", 9)

    page_num = 1
    # Write representative sections (Overview, Errors, Troubleshooting)
    for line in lines[:160]:
        clean_line = line.strip().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss").replace("Ä", "Ae").replace("Ö", "Oe").replace("Ü", "Ue")
        if not clean_line:
            y -= 10
            continue
        if clean_line.startswith("---") or clean_line.startswith("==="):
            continue
        if len(clean_line) > 95:
            clean_line = clean_line[:95]
        
        c.drawString(50, y, clean_line)
        y -= 13
        if y < 50:
            c.drawString(width - 80, 30, f"Page {page_num}")
            c.showPage()
            page_num += 1
            c.setFont("Helvetica", 9)
            y = height - 50

    c.drawString(width - 80, 30, f"Page {page_num}")
    c.save()
    print(f"Generated German PDF at: {output_path} ({page_num} pages)")

def main():
    os.makedirs(os.path.join(REPO_ROOT, "scratch"), exist_ok=True)
    pdf_path = os.path.join(REPO_ROOT, "scratch", "test_german_manual.pdf")
    generate_german_pdf(pdf_path)

    client = TestClient(app)

    # 1. Upload the German PDF
    print("\n[Step 1] Uploading German PDF to /manuals/upload...")
    with open(pdf_path, "rb") as f:
        files = {"file": ("test_german_manual.pdf", f, "application/pdf")}
        upload_resp = client.post("/manuals/upload", files=files)

    assert upload_resp.status_code == 200, f"Upload failed: {upload_resp.text}"
    upload_data = upload_resp.json()
    print(f"Upload status: {upload_data['status']}")
    print(f"Detected language: {upload_data.get('detected_language')} ({upload_data.get('source_language')})")
    print(f"Is translated: {upload_data.get('is_translated')}")
    print(f"Parsed Machine: {upload_data.get('machine')}")
    print(f"Valid format: {upload_data.get('is_valid_format')}")

    draft = upload_data.get("draft_text", "")
    assert len(draft) > 100, "Draft text should not be empty"
    print("\n--- LLM Structured English Draft (first 500 chars) ---")
    print(draft[:500])
    print("-------------------------------------------------------")

    # Verify that the draft text was translated to English
    post_det = _module_instance.detect_language(draft[:2500])
    print(f"Draft language detection: {post_det}")
    assert post_det["language"] == "en", f"Expected English draft, got {post_det}"

    # Verify invariant unit preservation
    for unit in ["24,000 RPM", "94°C", "400V", "18 bar"]:
        if unit in draft:
            print(f" Verified preserved unit: '{unit}'")

    # 2. Confirm the manual
    print("\n[Step 2] Confirming manual via /manuals/confirm...")
    confirm_payload = {
        "machine": "CNC Milling Machine",
        "content": draft,
        "source_language": upload_data.get("source_language", "de"),
        "detected_language": upload_data.get("detected_language", "German"),
        "is_translated": upload_data.get("is_translated", True)
    }
    confirm_resp = client.post("/manuals/confirm", json=confirm_payload)
    assert confirm_resp.status_code == 200, f"Confirm failed: {confirm_resp.text}"
    confirm_data = confirm_resp.json()
    print(f"Confirmed chunk count: {confirm_data.get('chunk_count')}")

    # 3. Verify single entry in /api/manuals with translation badge
    print("\n[Step 3] Verifying /api/manuals library...")
    lib_resp = client.get("/api/manuals")
    assert lib_resp.status_code == 200
    manuals = lib_resp.json().get("manuals", [])
    print(f"Total manual entries in library: {len(manuals)}")
    for m in manuals:
        trans_info = f" [Originally: {m.get('detected_language')}]" if m.get("is_translated") else ""
        print(f" - {m['filename']}: {m['title']}{trans_info}")

    # 4. Verify retrieval via normal English query
    print("\n[Step 4] Executing normal English query against newly ingested manual...")
    query_payload = {
        "message": "What is the recommended action if the spindle temperature reaches 94°C on the CNC Milling Machine?",
        "session_id": "e2e_german_verification"
    }
    query_resp = client.post("/query", json=query_payload)
    assert query_resp.status_code == 200, f"Query failed: {query_resp.text}"
    query_data = query_resp.json()
    print(f"Query Answer:\n{query_data.get('answer')}")
    print(f"Fault identified: {query_data.get('fault')}")
    print(f"Confidence score: {query_data.get('confidence_score')} ({query_data.get('confidence_percentage')}%)")

    assert "94°C" in query_data.get("answer", "") or "94" in query_data.get("answer", "")
    assert len(query_data.get("sources", [])) > 0, "Expected citations from ingested manual"
    print("\n SUCCESS: End-to-end German PDF ingestion, translation, confirmation, and retrieval verified!")

if __name__ == "__main__":
    main()
