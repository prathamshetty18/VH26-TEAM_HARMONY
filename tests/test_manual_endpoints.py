import os
import io
import pytest
from fastapi.testclient import TestClient
import pypdf

from src.api import app, MANUALS_DIR
from src.embed_store import get_distinct_machines, delete_by_machine

client = TestClient(app)

SAMPLE_VALID_TXT = """MACHINE: Laser Cutter
MODEL: LC-900

ERROR CODE: L101
SECTION: L101 Beam Alignment Error
PAGE: 1
MEANING: Beam delivery mirror galvanometer out of alignment.
CAUSES:
- Optical mount vibration
- Thermal drift of laser tube

SECTION: L101 Troubleshooting
PAGE: 1
STEPS:
1. Power down the laser diode at CP-3.
2. Inspect front-surface turning mirror with alignment target.
3. Calibrate galvanometer trim potentiometer until laser beam centers on target.
"""

SAMPLE_UPDATED_TXT = """MACHINE: Laser Cutter
MODEL: LC-900

ERROR CODE: L101
SECTION: L101 Beam Alignment Error
PAGE: 1
MEANING: Beam delivery mirror galvanometer out of alignment.
CAUSES:
- Optical mount vibration

SECTION: L101 Troubleshooting
PAGE: 1
STEPS:
1. Power down laser.
2. Re-center target.

ERROR CODE: L202
SECTION: L202 Water Chiller Low Flow
PAGE: 2
MEANING: Cooling loop flow rate below 4 liters per minute.
CAUSES:
- Chiller pump cavitation
- Kinked polyurethane hose

SECTION: L202 Troubleshooting
PAGE: 2
STEPS:
1. Verify chiller reservoir sight gauge.
2. Purge air bleed screw on heat exchanger.
"""

SAMPLE_MALFORMED_TXT = """SECTION: Error Codes
PAGE: 1
MEANING: Missing machine header completely.
"""

def create_mock_pdf(text: str) -> bytes:
    """Helper to generate a minimal valid PDF containing given text."""
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=200, height=200)
    # If text is needed in the PDF, write minimal stream
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()

class TestManualEndpoints:

    @pytest.fixture(autouse=True)
    def cleanup_test_machine(self):
        """Ensure test machine 'Laser Cutter' is cleaned up before and after tests."""
        delete_by_machine("Laser Cutter")
        target_path = os.path.join(MANUALS_DIR, "laser_cutter.txt")
        if os.path.exists(target_path):
            try:
                os.remove(target_path)
            except Exception:
                pass
        yield
        delete_by_machine("Laser Cutter")
        if os.path.exists(target_path):
            try:
                os.remove(target_path)
            except Exception:
                pass

    def test_get_machines_returns_active_machines(self):
        resp = client.get("/machines")
        assert resp.status_code == 200
        data = resp.json()
        assert "machines" in data
        assert isinstance(data["machines"], list)
        assert len(data["machines"]) >= 3

    def test_get_manuals_list(self):
        resp = client.get("/manuals")
        assert resp.status_code == 200
        data = resp.json()
        assert "manuals" in data
        assert isinstance(data["manuals"], list)
        assert len(data["manuals"]) >= 3
        for item in data["manuals"]:
            assert "machine" in item
            assert "filename" in item
            assert "chunk_count" in item
            assert "updated_at" in item

    def test_upload_txt_malformed_returns_400(self):
        files = {"file": ("malformed.txt", io.BytesIO(SAMPLE_MALFORMED_TXT.encode("utf-8")), "text/plain")}
        resp = client.post("/manuals/upload", files=files)
        assert resp.status_code == 400
        data = resp.json()
        assert "Manual format validation failed" in data["detail"]
        assert "Missing required 'MACHINE:' header" in data["detail"]

    def test_upload_unsupported_extension_returns_400(self):
        files = {"file": ("manual.docx", io.BytesIO(b"fake docx content"), "application/vnd.openxmlformats")}
        resp = client.post("/manuals/upload", files=files)
        assert resp.status_code == 400
        assert "Unsupported file format" in resp.json()["detail"]

    def test_upload_empty_file_returns_400(self):
        files = {"file": ("empty.txt", io.BytesIO(b""), "text/plain")}
        resp = client.post("/manuals/upload", files=files)
        assert resp.status_code == 400
        assert "Uploaded file is empty" in resp.json()["detail"]

    def test_upload_txt_valid_success_and_immediate_queryable(self):
        files = {"file": ("laser_manual.txt", io.BytesIO(SAMPLE_VALID_TXT.encode("utf-8")), "text/plain")}
        resp = client.post("/manuals/upload", files=files)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["machine"] == "Laser Cutter"
        assert data["chunk_count"] == 2
        assert data["is_valid_format"] is True

        # Verify dynamic machines list updated immediately without server restart
        machines_resp = client.get("/machines")
        assert "Laser Cutter" in machines_resp.json()["machines"]

        # Verify manuals list contains Laser Cutter
        manuals_resp = client.get("/manuals")
        cutter_item = next((m for m in manuals_resp.json()["manuals"] if m["machine"] == "Laser Cutter"), None)
        assert cutter_item is not None
        assert cutter_item["chunk_count"] == 2

        # Verify immediate queryability via POST /query
        query_resp = client.post("/query", json={
            "message": "What does error L101 mean on Laser Cutter?",
            "session_id": "test_upload_s1"
        })
        assert query_resp.status_code == 200
        q_data = query_resp.json()
        assert q_data["ambiguous"] is False
        assert len(q_data["sources"]) > 0
        assert q_data["sources"][0]["machine"] == "Laser Cutter"

    def test_reupload_replaces_old_chunks(self):
        # First upload: 2 chunks
        files1 = {"file": ("laser.txt", io.BytesIO(SAMPLE_VALID_TXT.encode("utf-8")), "text/plain")}
        resp1 = client.post("/manuals/upload", files=files1)
        assert resp1.status_code == 200
        assert resp1.json()["chunk_count"] == 2

        # Re-upload with 4 chunks (L101 and L202)
        files2 = {"file": ("laser.txt", io.BytesIO(SAMPLE_UPDATED_TXT.encode("utf-8")), "text/plain")}
        resp2 = client.post("/manuals/upload", files=files2)
        assert resp2.status_code == 200
        assert resp2.json()["chunk_count"] == 4

        # Verify GET /manuals shows exactly 4 chunks, NOT 6 (no duplication)
        manuals_resp = client.get("/manuals")
        cutter_item = next((m for m in manuals_resp.json()["manuals"] if m["machine"] == "Laser Cutter"), None)
        assert cutter_item is not None
        assert cutter_item["chunk_count"] == 4

    def test_upload_scanned_pdf_rejected_with_400(self):
        # Blank PDF has 0 extractable text characters (< 100)
        blank_pdf_bytes = create_mock_pdf("empty")
        files = {"file": ("scanned_manual.pdf", io.BytesIO(blank_pdf_bytes), "application/pdf")}
        resp = client.post("/manuals/upload", files=files)
        assert resp.status_code == 400
        detail = resp.json()["detail"]
        assert "No extractable text found" in detail
        assert "OCR is not currently supported" in detail

    def test_confirm_manual_valid_and_invalid(self):
        # Invalid confirmation
        resp_bad = client.post("/manuals/confirm", json={
            "machine": "Laser Cutter",
            "content": "MALFORMED CONTENT WITHOUT MACHINE OR SECTION"
        })
        assert resp_bad.status_code == 400

        # Valid confirmation
        resp_good = client.post("/manuals/confirm", json={
            "machine": "Laser Cutter",
            "content": SAMPLE_VALID_TXT
        })
        assert resp_good.status_code == 200
        assert resp_good.json()["status"] == "success"
        assert resp_good.json()["chunk_count"] == 2

    def test_delete_manual_and_404(self):
        # Upload first
        files = {"file": ("laser.txt", io.BytesIO(SAMPLE_VALID_TXT.encode("utf-8")), "text/plain")}
        client.post("/manuals/upload", files=files)
        assert "Laser Cutter" in client.get("/machines").json()["machines"]

        # Delete
        del_resp = client.delete("/manuals/Laser Cutter")
        assert del_resp.status_code == 200
        data = del_resp.json()
        assert data["status"] == "success"
        assert data["chunks_deleted"] == 2

        # Verify no longer in GET /machines
        assert "Laser Cutter" not in client.get("/machines").json()["machines"]

        # Deleting again returns 404
        del_again = client.delete("/manuals/Laser Cutter")
        assert del_again.status_code == 404

    def test_delete_partial_resilience(self):
        # Case: file exists on disk but 0 chunks in Chroma
        target_path = os.path.join(MANUALS_DIR, "laser_cutter.txt")
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(SAMPLE_VALID_TXT)

        del_resp = client.delete("/manuals/Laser Cutter")
        assert del_resp.status_code == 200
        assert not os.path.exists(target_path)

    def test_chroma_contains_only_expected_demo_machines(self):
        """Regression for Issue 1: Assert ChromaDB only contains the exact 3 demo machines."""
        machines = get_distinct_machines()
        expected = {"CNC Milling Machine", "Conveyor Belt System", "Hydraulic Press"}
        assert set(machines) == expected, f"Contaminated machines detected in Chroma: {set(machines) - expected}"

    def test_cache_invalidation_immediate_back_to_back(self):
        """Regression for Issue 3A: No cache lag on back-to-back upload and delete operations."""
        initial_machines = set(client.get("/machines").json()["machines"])
        assert "Laser Cutter" not in initial_machines

        # Immediate back-to-back upload -> assert present with 0 sleep
        files = {"file": ("laser.txt", io.BytesIO(SAMPLE_VALID_TXT.encode("utf-8")), "text/plain")}
        up_resp = client.post("/manuals/upload", files=files)
        assert up_resp.status_code == 200
        post_up_machines = client.get("/machines").json()["machines"]
        assert "Laser Cutter" in post_up_machines

        # Immediate back-to-back delete -> assert removed with 0 sleep
        del_resp = client.delete("/manuals/Laser Cutter")
        assert del_resp.status_code == 200
        post_del_machines = client.get("/machines").json()["machines"]
        assert "Laser Cutter" not in post_del_machines

    def test_pdf_upload_does_not_index_until_confirmed(self, monkeypatch):
        """Regression for Issue 2.4: PDF upload returns draft and does NOT touch Chroma until /confirm."""
        from src import api
        mock_draft = """MACHINE: Robotic Welder
MODEL: RW-500

ERROR CODE: W301
SECTION: W301 Shielding Gas Flow Error
PAGE: 10
MEANING: Shielding gas flow below 15 L/min.
CAUSES:
- Regulator freeze
- Depleted argon cylinder

SECTION: W301 Troubleshooting
PAGE: 10
STEPS:
1. Check argon cylinder pressure gauge.
2. Replace cylinder if below 20 bar.
"""
        monkeypatch.setattr(api, "structure_pdf_text_with_llm", lambda raw: mock_draft)

        class MockPage:
            def extract_text(self):
                return "Robotic Welder Maintenance Manual. Model RW-500. Error Code W301 indicates shielding gas flow rate is critically low. Inspect argon bottle regulator." * 3
        class MockReader:
            pages = [MockPage()]

        monkeypatch.setattr(pypdf, "PdfReader", lambda stream: MockReader())

        files = {"file": ("manual.pdf", io.BytesIO(b"%PDF-1.4 dummy bytes"), "application/pdf")}
        resp = client.post("/manuals/upload", files=files)
        assert resp.status_code == 200
        assert resp.json()["status"] == "needs_review"
        assert resp.json()["draft_text"] == mock_draft

        # Assert Robotic Welder is NOT in Chroma yet
        assert "Robotic Welder" not in client.get("/machines").json()["machines"]
        manuals = [m["machine"] for m in client.get("/manuals").json()["manuals"]]
        assert "Robotic Welder" not in manuals

        # Now call confirm -> now it must be indexed
        conf_resp = client.post("/manuals/confirm", json={
            "machine": "Robotic Welder",
            "content": mock_draft
        })
        assert conf_resp.status_code == 200
        assert "Robotic Welder" in client.get("/machines").json()["machines"]

        # Cleanup
        client.delete("/manuals/Robotic Welder")

    def test_structure_pdf_text_preserves_exact_numeric_values(self):
        """Regression for Issue 2.3: Verifies exact character-for-character numeric preservation."""
        from src.llm_answer import structure_pdf_text_with_llm
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            pytest.skip("GEMINI_API_KEY not set")

        raw_sample = """
        INDUSTRIAL SYSTEM MANUAL
        MACHINE: Plasma System
        MODEL: PS-300
        Fault E101: Hydraulic temperature exceeds 65°C on sensor TT-02.
        Coolant flow must be at least 3.8 L/min under 45-70 bar pump pressure.
        Motor trip occurs if draw exceeds 125% FLA for 3.5 seconds.
        Maximum allowable spindle radial runout is 0.015 mm TIR at 1,000 RPM.
        Troubleshooting steps:
        1. Check temperature transmitter TT-02 when exceeds 65°C.
        2. Verify coolant delivery is 3.8 L/min.
        3. Regulate pump pressure to 45-70 bar.
        """
        try:
            structured = structure_pdf_text_with_llm(raw_sample)
            for expected_num in ["65°C", "3.8 L/min", "45-70 bar", "125% FLA", "3.5 seconds", "0.015 mm", "1,000 RPM"]:
                assert expected_num in structured, f"Critical numeric value '{expected_num}' was altered or omitted by LLM!"
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                pytest.skip(f"Gemini API rate limit: {e}")
            raise e

