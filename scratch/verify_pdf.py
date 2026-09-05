import requests
import io
import time
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

BASE_URL = "http://127.0.0.1:8000"
MACHINE_NAME = "TEST-PDF-MACHINE"

def create_good_pdf(filename):
    c = canvas.Canvas(filename, pagesize=letter)
    text = c.beginText(40, 750)
    text.setFont("Helvetica", 12)
    # Important: Include numeric values to test preservation
    lines = [
        f"MACHINE: {MACHINE_NAME}",
        "SECTION: Diagnostics E999",
        "MEANING: System failure due to extreme conditions.",
        "CAUSE: Temperature exceeded 150.5C and pressure dropped below 12.3 PSI.",
        "SOLUTION: Replace valve 42B immediately."
    ]
    for line in lines:
        text.textLine(line)
    c.drawText(text)
    c.showPage()
    c.save()
    print(f"Created {filename}")

def create_scanned_pdf(filename):
    # A PDF with NO text objects (just a blank page or lines/shapes)
    c = canvas.Canvas(filename, pagesize=letter)
    c.rect(100, 100, 200, 200) # Draw a shape instead of text
    c.showPage()
    c.save()
    print(f"Created {filename}")

def run_pdf_verification():
    print("--- Starting PDF Verification ---")
    good_pdf = "good.pdf"
    scanned_pdf = "scanned.pdf"
    
    create_good_pdf(good_pdf)
    create_scanned_pdf(scanned_pdf)
    
    try:
        # 1. Upload realistic PDF
        print("Uploading realistic PDF...")
        with open(good_pdf, "rb") as f:
            files = {"file": (good_pdf, f, "application/pdf")}
            resp = requests.post(f"{BASE_URL}/manuals/upload", files=files)
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        print("Good PDF response keys:", data.keys())
        print("Good PDF status:", data.get("status"))
        
        assert data.get("status") == "needs_review", "Expected 'needs_review' status for PDF"
        draft_text = data.get("draft_text", "")
        
        # Check numeric preservation
        assert "150.5C" in draft_text or "150.5" in draft_text, f"Numeric value 150.5 lost! Draft: {draft_text}"
        assert "12.3" in draft_text, f"Numeric value 12.3 lost! Draft: {draft_text}"
        assert "42B" in draft_text, f"Value 42B lost! Draft: {draft_text}"
        print("Numeric values successfully preserved character-for-character.")
        
        # 2. Confirm the draft
        print("Confirming draft...")
        confirm_req = {
            "machine": MACHINE_NAME,
            "content": draft_text
        }
        resp_confirm = requests.post(f"{BASE_URL}/manuals/confirm", json=confirm_req)
        assert resp_confirm.status_code == 200, f"Confirm failed: {resp_confirm.text}"
        print("Confirm success.")
        
        # 3. Upload scanned PDF
        print("Uploading scanned PDF...")
        with open(scanned_pdf, "rb") as f:
            files2 = {"file": (scanned_pdf, f, "application/pdf")}
            resp2 = requests.post(f"{BASE_URL}/manuals/upload", files=files2)
        
        print("Scanned PDF status code:", resp2.status_code)
        print("Scanned PDF response text:", resp2.text)
        assert resp2.status_code == 400, "Expected 400 for scanned PDF"
        assert "OCR" in resp2.text or "scanned" in resp2.text, "Expected OCR message in error detail"
        print("Scanned PDF correctly rejected with OCR error.")
        
    finally:
        # Ensure cleanup
        print(f"Cleaning up {MACHINE_NAME}...")
        requests.delete(f"{BASE_URL}/manuals/{MACHINE_NAME}")
        import os
        if os.path.exists(good_pdf): os.remove(good_pdf)
        if os.path.exists(scanned_pdf): os.remove(scanned_pdf)
        print("--- PDF Verification Complete ---")

if __name__ == "__main__":
    run_pdf_verification()
