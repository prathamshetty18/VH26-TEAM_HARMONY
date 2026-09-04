# -*- coding: utf-8 -*-
"""
Tests for Multilingual Machine Instruction Manual Section

Validates:
1. Presence of all 4 languages: English (en), Simplified Chinese (zh), Japanese (ja), German (de).
2. Presence and integrity of all 9 manual sections in each language:
   - Section 1: Machine Overview
   - Section 2: Safety Instructions
   - Section 3: Machine Components
   - Section 4: Operating Instructions
   - Section 5: Error and Fault Instructions
   - Section 6: Maintenance Instructions
   - Section 7: Troubleshooting Table (9 hardware faults)
   - Section 8: Emergency Procedures
   - Section 9: Technical Specifications
3. Strict preservation of numerical values and units (400V, 32A, 15 kW, 24,000 RPM, 94°C, 6.5 bar, 18 bar) across all languages.
4. Correct behavior of /api/manuals/multilingual endpoint for en, zh, ja, and de.
5. Strict non-interference with the existing machine hardware error detection pipeline.
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient

# Ensure repo root is in sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.multilingual_manual_data import (
    MULTILINGUAL_MANUAL,
    get_multilingual_manual,
    get_available_languages
)
from src.api import app

REQUIRED_SECTIONS = [
    "overview",
    "safety",
    "components",
    "operating",
    "error_fault",
    "maintenance",
    "troubleshooting",
    "emergency_procedures",
    "specifications"
]

PRESERVED_UNITS = [
    "400V",
    "32A",
    "15 kW",
    "24,000 RPM",
    "94°C",
    "6.5 bar",
    "18 bar"
]


class TestMultilingualManualDataStructure:
    """Verifies that all 4 languages exist and contain all 9 sections."""

    def test_supported_languages_exist(self):
        langs = list(MULTILINGUAL_MANUAL.keys())
        for expected in ["en", "zh", "ja", "de"]:
            assert expected in langs, f"Missing language code: {expected}"

    @pytest.mark.parametrize("lang_code", ["en", "zh", "ja", "de"])
    def test_all_nine_sections_present(self, lang_code):
        manual = get_multilingual_manual(lang_code)
        assert manual is not None, f"Manual not found for {lang_code}"
        sections = manual.get("sections", {})
        for sec in REQUIRED_SECTIONS:
            assert sec in sections, f"Section '{sec}' missing in {lang_code} manual"
            assert sections[sec]["section_id"] > 0
            assert len(sections[sec]["title"]) > 0

    @pytest.mark.parametrize("lang_code", ["en", "zh", "ja", "de"])
    def test_components_section_structure(self, lang_code):
        manual = get_multilingual_manual(lang_code)
        comps = manual["sections"]["components"].get("components_list", [])
        assert len(comps) >= 5, f"Expected at least 5 components in {lang_code}"
        for c in comps:
            assert "name" in c and len(c["name"]) > 0
            assert "function" in c and len(c["function"]) > 0
            assert "normal_condition" in c and len(c["normal_condition"]) > 0
            assert "common_problems" in c and len(c["common_problems"]) > 0

    @pytest.mark.parametrize("lang_code", ["en", "zh", "ja", "de"])
    def test_operating_instructions_steps(self, lang_code):
        manual = get_multilingual_manual(lang_code)
        op_steps = manual["sections"]["operating"].get("steps", {})
        for category in ["starting", "normal_operation", "monitoring", "stopping", "emergency_shutdown"]:
            assert category in op_steps, f"Missing step category '{category}' in {lang_code}"
            assert len(op_steps[category]) > 0

    @pytest.mark.parametrize("lang_code", ["en", "zh", "ja", "de"])
    def test_troubleshooting_table_nine_faults(self, lang_code):
        manual = get_multilingual_manual(lang_code)
        table = manual["sections"]["troubleshooting"].get("table", [])
        assert len(table) == 9, f"Troubleshooting table in {lang_code} must contain 9 hardware faults"
        for row in table:
            assert "error" in row and len(row["error"]) > 0
            assert "possible_cause" in row and len(row["possible_cause"]) > 0
            assert "solution" in row and len(row["solution"]) > 0


class TestNumericalUnitsPreservation:
    """Verifies that numbers, units, and engineering limits are identical across all languages."""

    @pytest.mark.parametrize("lang_code", ["en", "zh", "ja", "de"])
    def test_technical_specifications_values(self, lang_code):
        manual = get_multilingual_manual(lang_code)
        specs = manual["sections"]["specifications"].get("specs", [])
        assert len(specs) >= 7, f"Technical specifications in {lang_code} must have at least 7 fields"

        # Check values in specs
        all_spec_values = " ".join([s["value"] for s in specs])
        for unit in ["400V", "32A", "15 kW", "24,000 RPM", "94°C", "6.5 bar", "18 bar"]:
            assert unit in all_spec_values, f"Unit '{unit}' must be preserved in {lang_code} specifications"

    @pytest.mark.parametrize("lang_code", ["en", "zh", "ja", "de"])
    def test_motor_overheating_temperature_preservation(self, lang_code):
        manual = get_multilingual_manual(lang_code)
        # Check that 94°C appears in error_fault motor problem and troubleshooting table
        error_items = manual["sections"]["error_fault"].get("items", [])
        motor_fault = error_items[0]
        assert "94°C" in motor_fault["problem"] or "94°C" in motor_fault["what_to_check"]

        tb_rows = manual["sections"]["troubleshooting"].get("table", [])
        overheat_row = tb_rows[0]
        assert "94°C" in overheat_row["possible_cause"]


class TestMultilingualManualAPI:
    """Tests the /api/manuals/multilingual endpoint."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.mark.parametrize("lang_code", ["en", "zh", "ja", "de"])
    def test_api_returns_correct_language(self, client, lang_code):
        resp = client.get(f"/api/manuals/multilingual?lang={lang_code}")
        assert resp.status_code == 200
        data = resp.json()
        assert "selected_language" in data
        assert data["selected_language"] == lang_code
        assert "languages" in data
        assert len(data["languages"]) == 4
        assert "manual" in data
        assert "sections" in data["manual"]
        for sec in REQUIRED_SECTIONS:
            assert sec in data["manual"]["sections"]

    def test_api_defaults_to_english_on_unknown(self, client):
        resp = client.get("/api/manuals/multilingual?lang=unknown_xyz")
        assert resp.status_code == 200
        data = resp.json()
        assert data["selected_language"] == "en"
        assert "Machine Overview" in data["manual"]["sections"]["overview"]["title"]


class TestPipelineNonInterference:
    """Ensures existing machine fault detection pipeline is not modified or impaired."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_existing_query_pipeline_intact(self, client):
        resp = client.post("/query", json={
            "message": "What does error E101 mean on the Conveyor Belt System?",
            "session_id": "test_manual_pipeline_check"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert len(data["answer"]) > 0


class TestMultilingualTxtFiles:
    """Verifies that the multilingual manual is exported into separate .txt files."""

    @pytest.mark.parametrize("lang_code", ["en", "zh", "ja", "de"])
    def test_individual_txt_manual_exists(self, lang_code):
        file_path = os.path.join(ROOT, "data", "manuals", f"multilingual_manual_{lang_code}.txt")
        assert os.path.exists(file_path), f"File {file_path} does not exist"
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert len(content) > 5000, f"File {file_path} is unexpectedly small"
        for unit in PRESERVED_UNITS:
            assert unit in content, f"Unit '{unit}' missing in {file_path}"

    def test_combined_txt_manual_exists(self):
        file_path = os.path.join(ROOT, "data", "manuals", "multilingual_manual.txt")
        assert os.path.exists(file_path), f"File {file_path} does not exist"
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert len(content) > 20000
        for unit in PRESERVED_UNITS:
            assert unit in content

    def test_manuals_endpoint_lists_txt_files(self):
        client = TestClient(app)
        resp = client.get("/api/manuals")
        assert resp.status_code == 200
        manuals = resp.json().get("manuals", [])
        filenames = [m["filename"] for m in manuals]
        assert "multilingual_manual_zh.txt" in filenames
        assert "multilingual_manual_ja.txt" in filenames
        assert "multilingual_manual_de.txt" in filenames
        assert "multilingual_manual_en.txt" in filenames

