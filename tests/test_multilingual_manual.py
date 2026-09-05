# -*- coding: utf-8 -*-
"""
Tests validating that language-parallel manual concepts have been removed,
enforcing a single English manual per physical machine, absence of the legacy
multilingual endpoint/files, and correct behavior of the single-manual library.
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.api import app
from src.llm_answer import PDF_STRUCTURING_SYSTEM_PROMPT

PRESERVED_UNITS = [
    "400V",
    "32A",
    "15 kW",
    "24,000 RPM",
    "94°C",
    "6.5 bar",
    "18 bar"
]

@pytest.fixture
def client():
    return TestClient(app)


class TestSingleManualPerMachineArchitecture:
    """Verifies that the multilingual manual viewer endpoint and parallel files are gone."""

    def test_multilingual_endpoint_is_removed(self, client):
        """GET /api/manuals/multilingual must return 404 since language-parallel endpoint is deleted."""
        resp = client.get("/api/manuals/multilingual")
        assert resp.status_code == 404

        resp_de = client.get("/api/manuals/multilingual?lang=de")
        assert resp_de.status_code == 404

    def test_no_multilingual_manual_files_in_manuals_library(self, client):
        """GET /api/manuals must not contain any multilingual_manual*.txt demo files."""
        resp = client.get("/api/manuals")
        assert resp.status_code == 200
        data = resp.json()
        manuals = data.get("manuals", [])
        filenames = [m["filename"] for m in manuals]

        assert "multilingual_manual.txt" not in filenames
        assert "multilingual_manual_zh.txt" not in filenames
        assert "multilingual_manual_ja.txt" not in filenames
        assert "multilingual_manual_de.txt" not in filenames
        assert "multilingual_manual_en.txt" not in filenames

    def test_single_card_per_physical_machine(self, client):
        """Ensure exactly ONE manual per physical machine (CB-4400, MX-7, HP-2200, RobotArm-300)."""
        resp = client.get("/api/manuals")
        assert resp.status_code == 200
        manuals = resp.json().get("manuals", [])
        filenames = [m["filename"] for m in manuals]

        expected_canonical = [
            "conveyorcb4400.txt",
            "cncmx7.txt",
            "presshp2200.txt",
            "robotarm_300.txt"
        ]
        assert filenames == expected_canonical
        assert len(manuals) == 4

        # Each manual must support translation metadata fields
        for m in manuals:
            assert "is_translated" in m
            assert "source_language" in m
            assert "detected_language" in m


class TestTranslationIngestPromptIntegrity:
    """Verifies that PDF_STRUCTURING_SYSTEM_PROMPT instructs unconditional English translation and unit preservation."""

    def test_unconditional_translation_instructions(self):
        assert "ALL structured output fields (MACHINE, MODEL, SECTION, MEANING, CAUSES, STEPS) MUST BE IN ENGLISH" in PDF_STRUCTURING_SYSTEM_PROMPT
        assert "TRANSLATE all descriptions, meanings, causes, and corrective action steps into clear, professional technical English" in PDF_STRUCTURING_SYSTEM_PROMPT

    def test_token_preservation_instructions(self):
        assert "NUMERIC VALUES, THRESHOLDS, UNITS, AND ERROR CODES MUST BE COPIED CHARACTER-FOR-CHARACTER" in PDF_STRUCTURING_SYSTEM_PROMPT
        for unit in PRESERVED_UNITS:
            assert unit in PDF_STRUCTURING_SYSTEM_PROMPT


class TestPipelineNonInterference:
    """Ensures existing machine fault query pipeline remains functional."""

    def test_existing_query_pipeline_intact(self, client):
        resp = client.post("/query", json={
            "message": "How do I fix error E101 on the CB-4400 conveyor belt?",
            "session_id": "test_pipeline_check"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert len(data["answer"]) > 0
        assert data.get("fault") is not None
