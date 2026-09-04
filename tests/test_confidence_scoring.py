# -*- coding: utf-8 -*-
"""
Tests for AI Confidence Scoring & Diagnostics Feature

Validates:
1. AI Confidence Level classification:
   - 90–100% = High Confidence
   - 70–89% = Moderate Confidence
   - Below 70% = Low Confidence
2. Model predictive confidence calibration (derived from existing retrieval similarity).
3. Non-Guarantee statement: Confidence score is presented as model predictive confidence
   and NOT described as a guarantee that the fault is physically present.
4. Multiple possible faults ranked by confidence, clearly marking the highest-confidence
   fault as primary (is_primary = True).
5. "View Explanation" evidence synthesis (sensor telemetry readings and reasoning).
6. Integration across website API endpoints:
   - POST /query (returns confidence score, level, multiple candidate faults, evidence, disclaimer)
   - Refusal queries return NO fabricated confidence score (confidence_score is None)
   - GET /api/fault-history (returns historical audit log with confidence scores and disclaimer)
   - GET /api/machine-health (returns fleet health scores and active confidence metrics)
   - GET /api/diagnostic-report (returns executive diagnostic summary with distribution metrics)
"""

import sys
import os
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.confidence import (
    get_confidence_level,
    calculate_model_confidence,
    extract_fault_title_and_component,
    extract_cause_and_recommendation,
    generate_telemetry_evidence,
    rank_candidate_faults,
    compute_machine_health,
    CONFIDENCE_DISCLAIMER
)
from src.api import (
    handle_query,
    QueryRequest,
    get_fault_history,
    get_machine_health_overview,
    get_diagnostic_report,
    FAULT_HISTORY
)

class TestConfidenceScoringLogic:
    """Tests for confidence calculation, level mapping, and disclaimer compliance."""

    def test_confidence_level_high(self):
        """90-100% must map to High Confidence."""
        assert get_confidence_level(1.0) == "High"
        assert get_confidence_level(0.95) == "High"
        assert get_confidence_level(0.90) == "High"

    def test_confidence_level_moderate(self):
        """70-89% must map to Moderate Confidence."""
        assert get_confidence_level(0.89) == "Moderate"
        assert get_confidence_level(0.80) == "Moderate"
        assert get_confidence_level(0.70) == "Moderate"

    def test_confidence_level_low(self):
        """Below 70% must map to Low Confidence."""
        assert get_confidence_level(0.69) == "Low"
        assert get_confidence_level(0.50) == "Low"
        assert get_confidence_level(0.28) == "Low"
        assert get_confidence_level(0.10) == "Low"

    def test_non_guarantee_disclaimer_content(self):
        """Disclaimer must explicitly state confidence is model prediction, not a guarantee."""
        assert "not a guarantee" in CONFIDENCE_DISCLAIMER.lower()
        assert "predictive" in CONFIDENCE_DISCLAIMER.lower() or "probability" in CONFIDENCE_DISCLAIMER.lower()

    def test_calculate_model_confidence_exact_error(self):
        """Exact error code matches in chunk should yield high confidence (>= 0.90)."""
        chunk = {
            "score": 0.69,
            "error_code": "E101",
            "section": "E101 Troubleshooting"
        }
        score = calculate_model_confidence(chunk, query_has_exact_error=True)
        assert score >= 0.90
        assert get_confidence_level(score) == "High"

    def test_calculate_model_confidence_moderate_symptom(self):
        """Moderate semantic similarity should yield moderate confidence (0.70 - 0.89)."""
        chunk = {
            "score": 0.55,
            "error_code": None,
            "section": "Startup Squeal Troubleshooting"
        }
        score = calculate_model_confidence(chunk, query_has_exact_error=False)
        assert 0.70 <= score <= 0.89
        assert get_confidence_level(score) == "Moderate"

class TestMultiplePossibleFaultsRanking:
    """Tests ranking of multiple candidate faults."""

    def test_rank_candidate_faults_structure(self):
        retrieved_chunks = [
            {"score": 0.69, "section": "Motor Bearing Wear", "machine": "CNC Milling Machine", "error_code": None},
            {"score": 0.45, "section": "Shaft Misalignment", "machine": "CNC Milling Machine", "error_code": None},
            {"score": 0.38, "section": "Motor Overload", "machine": "CNC Milling Machine", "error_code": None}
        ]
        ranked = rank_candidate_faults(
            retrieved_chunks,
            query="Motor bearing vibration",
            primary_fault_title="Motor Bearing Wear",
            primary_score=0.91,
            primary_component="Motor Bearing"
        )

        assert len(ranked) >= 2
        # Check sorted descending
        for i in range(len(ranked) - 1):
            assert ranked[i]["confidence_score"] >= ranked[i+1]["confidence_score"]

        # Only first item is marked primary
        assert ranked[0]["is_primary"] is True
        assert ranked[0]["fault"] == "Motor Bearing Wear"
        assert ranked[0]["confidence_score"] == 0.91
        assert ranked[0]["confidence_level"] == "High"

        # Secondary items must NOT be primary
        for item in ranked[1:]:
            assert item["is_primary"] is False

class TestExplanationAndTelemetry:
    """Tests 'View Explanation' evidence and telemetry generation."""

    def test_generate_telemetry_evidence(self):
        evidence = generate_telemetry_evidence(
            fault_title="Motor Bearing Wear",
            component="Motor Bearing & Housing",
            machine="CNC Milling Machine",
            confidence_score=0.91
        )
        assert "sensor_readings" in evidence
        assert len(evidence["sensor_readings"]) > 0
        assert "vibration_velocity" in evidence["sensor_readings"] or "bearing_temperature" in evidence["sensor_readings"]
        assert "reasoning" in evidence
        assert "disclaimer" in evidence
        assert "not a guarantee" in evidence["disclaimer"].lower()

class TestAPIConfidenceEndpoints:
    """Tests FastAPI endpoints integration for confidence scoring and report features."""

    def test_query_returns_confidence_on_detected_fault(self):
        req = QueryRequest(message="How do I fix error E101 on the CB-4400 conveyor belt?")
        resp = handle_query(req)

        assert resp.ambiguous is False
        assert resp.confidence_score is not None
        assert resp.confidence_score >= 0.70
        assert resp.confidence_level in ["High", "Moderate"]
        assert resp.fault is not None
        assert resp.component is not None
        assert len(resp.possible_faults) >= 1
        assert resp.possible_faults[0].is_primary is True
        assert resp.evidence is not None
        assert "not a guarantee" in resp.evidence.disclaimer.lower()

    def test_refusal_query_returns_no_confidence_score(self):
        """Undocumented LED pattern should trigger honest refusal without fabricated confidence score."""
        req = QueryRequest(message="The status LED is flashing 3 short blinks followed by a long pause, what does this pattern mean?")
        resp = handle_query(req)

        # Must refuse
        assert "sufficient information" in resp.answer.lower() or "won't provide an unsupported answer" in resp.answer.lower() or "don't cover this" in resp.answer.lower() or "won't guess" in resp.answer.lower()
        # No fabricated confidence score
        assert resp.confidence_score is None
        assert resp.confidence_level is None
        assert resp.fault is None
        assert resp.possible_faults == []

    def test_fault_history_endpoint(self):
        history = get_fault_history()
        assert "faults" in history
        assert history["total_count"] >= 1
        assert "disclaimer" in history
        assert "not a guarantee" in history["disclaimer"].lower()

        first_fault = history["faults"][0]
        assert "fault" in first_fault
        assert "confidence_score" in first_fault
        assert "confidence_level" in first_fault
        assert first_fault["confidence_level"] in ["High", "Moderate", "Low"]

    def test_machine_health_endpoint(self):
        health = get_machine_health_overview()
        assert "machines" in health
        assert len(health["machines"]) >= 3
        machine_names = [m["name"] for m in health["machines"]]
        assert any("Conveyor" in n for n in machine_names)
        assert any("CNC" in n for n in machine_names)
        assert any("Press" in n for n in machine_names)

        for m in health["machines"]:
            assert "health_score" in m
            assert 0 <= m["health_score"] <= 100
            assert "status" in m

    def test_diagnostic_report_endpoint(self):
        report = get_diagnostic_report()
        assert "report_id" in report
        assert "confidence_distribution" in report
        dist = report["confidence_distribution"]
        assert "high" in dist
        assert "moderate" in dist
        assert "low" in dist
        assert "disclaimer" in report
        assert "not a guarantee" in report["disclaimer"].lower()
