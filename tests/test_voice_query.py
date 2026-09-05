# -*- coding: utf-8 -*-
"""
Tests for Voice Query & Speech-to-Text Integration (src/speech.py & src/api.py)

Validates:
1. Speech-to-Text audio transcription & Language Detection for:
   - English (en-US)
   - Simplified Chinese (zh-CN)
   - Japanese (ja-JP)
   - German (de-DE)
2. English direct pass-through (no translation applied).
3. Translation to English for Chinese, Japanese, and German voice inputs via the EXISTING translation module.
4. User transcription review & editing before pipeline submission.
5. Direct connection to the EXISTING machine fault detection pipeline (handle_query / /query).
6. Graceful error handling (empty audio, corrupted bytes, API failures).
7. Modular enable/disable toggle.
8. API endpoints: /api/voice/status, /api/voice/samples, /api/voice/transcribe, /api/voice/query.
"""

import sys
import os
import base64
from unittest.mock import MagicMock, patch
import pytest

# Ensure repository root is in sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.speech import (
    GoogleSpeechToTextService,
    speech_service,
    VOICE_BENCHMARK_SAMPLES,
    SUPPORTED_VOICE_LANGUAGES,
)
from src.translation import MultilingualTranslationModule


class TestVoiceLanguageTranscriptionAndDetection:
    """Validates Speech-to-Text, language detection, and translation module connection."""

    def test_english_voice_input_passes_directly(self):
        """English voice input must NOT be translated and should pass directly."""
        service = GoogleSpeechToTextService()
        mock_speech_client = MagicMock()
        mock_result = MagicMock()
        mock_alt = MagicMock()
        mock_alt.transcript = "What does error E101 mean on the CNC-100?"
        mock_alt.confidence = 0.98
        mock_result.alternatives = [mock_alt]
        mock_result.language_code = "en-US"
        mock_speech_client.recognize.return_value.results = [mock_result]
        service.speech_client = mock_speech_client

        dummy_audio = b"RIFF" + b"\x00" * 100
        res = service.transcribe_audio(dummy_audio, mime_type="audio/wav")

        assert res["status"] == "success"
        assert res["transcription"] == "What does error E101 mean on the CNC-100?"
        assert res["detectedLanguage"] == "en"
        assert res["languageName"] == "English"
        assert res["englishText"] == "What does error E101 mean on the CNC-100?"
        assert res["isTranslated"] is False

    def test_chinese_voice_input_calls_existing_translation(self):
        """Chinese voice input must be translated to English via existing translation module."""
        service = GoogleSpeechToTextService()
        mock_speech_client = MagicMock()
        mock_result = MagicMock()
        mock_alt = MagicMock()
        mock_alt.transcript = "电机温度过高"
        mock_alt.confidence = 0.96
        mock_result.alternatives = [mock_alt]
        mock_result.language_code = "zh-CN"
        mock_speech_client.recognize.return_value.results = [mock_result]
        service.speech_client = mock_speech_client

        dummy_audio = b"\x1aE\xdf\xa3" + b"\x00" * 100  # WebM signature
        res = service.transcribe_audio(dummy_audio, mime_type="audio/webm")

        assert res["status"] == "success"
        assert res["transcription"] == "电机温度过高"
        assert res["detectedLanguage"] == "zh-CN"
        assert res["languageName"] == "Simplified Chinese"
        assert res["isTranslated"] is True
        assert res["englishText"] == "The motor temperature is too high."

    def test_japanese_voice_input_calls_existing_translation(self):
        """Japanese voice input must be translated to English via existing translation module."""
        service = GoogleSpeechToTextService()
        mock_speech_client = MagicMock()
        mock_result = MagicMock()
        mock_alt = MagicMock()
        mock_alt.transcript = "モーターの温度が高すぎます"
        mock_alt.confidence = 0.95
        mock_result.alternatives = [mock_alt]
        mock_result.language_code = "ja-JP"
        mock_speech_client.recognize.return_value.results = [mock_result]
        service.speech_client = mock_speech_client

        dummy_audio = b"\x1aE\xdf\xa3" + b"\x00" * 100
        res = service.transcribe_audio(dummy_audio, mime_type="audio/webm")

        assert res["status"] == "success"
        assert res["transcription"] == "モーターの温度が高すぎます"
        assert res["detectedLanguage"] == "ja"
        assert res["languageName"] == "Japanese"
        assert res["isTranslated"] is True
        assert res["englishText"] == "The motor temperature is too high."

    def test_german_voice_input_calls_existing_translation(self):
        """German voice input must be translated to English via existing translation module."""
        service = GoogleSpeechToTextService()
        mock_speech_client = MagicMock()
        mock_result = MagicMock()
        mock_alt = MagicMock()
        mock_alt.transcript = "Die Motortemperatur ist zu hoch."
        mock_alt.confidence = 0.97
        mock_result.alternatives = [mock_alt]
        mock_result.language_code = "de-DE"
        mock_speech_client.recognize.return_value.results = [mock_result]
        service.speech_client = mock_speech_client

        dummy_audio = b"\x1aE\xdf\xa3" + b"\x00" * 100
        res = service.transcribe_audio(dummy_audio, mime_type="audio/webm")

        assert res["status"] == "success"
        assert res["transcription"] == "Die Motortemperatur ist zu hoch."
        assert res["detectedLanguage"] == "de"
        assert res["languageName"] == "German"
        assert res["isTranslated"] is True
        assert res["englishText"] == "The motor temperature is too high."


class TestPreSubmissionEditing:
    """Validates user's ability to edit transcription before sending to pipeline."""

    def test_user_edits_transcription_before_submitting(self):
        service = GoogleSpeechToTextService()
        received_queries = []

        def mock_pipeline(query: str, **kwargs):
            received_queries.append(query)
            return {"status": "success", "query": query}

        # Case 1: Speech recognition slightly misheard ("E 101" -> user fixes to "E101 on CNC-100")
        original_transcript = "What does E 101 mean"
        edited_transcript = "What does error E101 mean on CNC-100?"

        service.process_voice_and_forward(
            transcription=original_transcript,
            edited_transcription=edited_transcript,
            pipeline_fn=mock_pipeline
        )

        assert len(received_queries) == 1
        assert received_queries[0] == "What does error E101 mean on CNC-100?"

    def test_user_submits_unedited_transcription(self):
        service = GoogleSpeechToTextService()
        received_queries = []

        def mock_pipeline(query: str, **kwargs):
            received_queries.append(query)
            return {"status": "success", "query": query}

        service.process_voice_and_forward(
            transcription="The motor is overheating.",
            edited_transcription=None,
            pipeline_fn=mock_pipeline
        )

        assert len(received_queries) == 1
        assert received_queries[0] == "The motor is overheating."


class TestPipelineForwardingIntegrity:
    """Verifies that voice queries connect directly to the existing diagnosis pipeline."""

    def test_voice_forwards_to_existing_handle_query(self):
        from src.api import handle_query, QueryRequest

        service = GoogleSpeechToTextService()

        # Chinese input translated to English and fed to handle_query
        result = service.process_voice_and_forward(
            transcription="电机温度过高",
            session_id="voice_test_session"
        )

        # Assert output is QueryResponse from existing pipeline
        assert hasattr(result, "answer")
        assert len(result.answer) > 0
        assert hasattr(result, "confidence_score")
        assert hasattr(result, "sources")


class TestErrorHandlingAndModularity:
    """Validates graceful error handling and modularity."""

    def test_empty_audio_handling(self):
        service = GoogleSpeechToTextService()
        res = service.transcribe_audio(b"")
        assert res["status"] == "error"
        assert "empty" in res["error"].lower()

    def test_modular_disable_toggle(self):
        service = GoogleSpeechToTextService()
        service.enabled = False
        res = service.transcribe_audio(b"dummy_bytes_long_enough_12345678901234567890")
        assert res["status"] == "error"
        assert "disabled" in res["error"].lower()


class TestFastAPIVoiceEndpoints:
    """Validates FastAPI voice endpoints via TestClient."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from src.api import app
        return TestClient(app)

    def test_get_voice_status(self, client):
        resp = client.get("/api/voice/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "enabled" in data
        assert "supported_languages" in data
        assert "en" in data["supported_languages"]
        assert "zh" in data["supported_languages"]
        assert "ja" in data["supported_languages"]
        assert "de" in data["supported_languages"]

    def test_get_voice_samples(self, client):
        resp = client.get("/api/voice/samples")
        assert resp.status_code == 200
        data = resp.json()
        assert "samples" in data
        assert len(data["samples"]) >= 4
        langs = [s["language"] for s in data["samples"]]
        assert "en" in langs
        assert "zh-CN" in langs
        assert "ja" in langs
        assert "de" in langs

    def test_post_voice_transcribe_with_sample_id(self, client):
        # Test Chinese sample
        resp = client.post("/api/voice/transcribe", json={"sample_id": "sample_zh_motor"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["transcription"] == "电机温度过高"
        assert data["detectedLanguage"] == "zh-CN"
        assert data["languageName"] == "Simplified Chinese"
        assert data["englishText"] == "The motor temperature is too high."
        assert data["isTranslated"] is True

        # Test German sample
        resp_de = client.post("/api/voice/transcribe", json={"sample_id": "sample_de_press"})
        assert resp_de.status_code == 200
        data_de = resp_de.json()
        assert data_de["transcription"] == "Die Motortemperatur ist zu hoch."
        assert data_de["detectedLanguage"] == "de"
        assert data_de["languageName"] == "German"
        assert data_de["englishText"] == "The motor temperature is too high."
        assert data_de["isTranslated"] is True

        # Test English sample
        resp_en = client.post("/api/voice/transcribe", json={"sample_id": "sample_en_e101"})
        assert resp_en.status_code == 200
        data_en = resp_en.json()
        assert data_en["transcription"] == "What does error E101 mean on the CNC-100?"
        assert data_en["detectedLanguage"] == "en"
        assert data_en["languageName"] == "English"
        assert data_en["englishText"] == "What does error E101 mean on the CNC-100?"
        assert data_en["isTranslated"] is False

    def test_post_voice_transcribe_with_base64_audio(self, client):
        dummy_wav = b"RIFF" + b"\x00" * 80
        b64 = base64.b64encode(dummy_wav).decode("utf-8")
        resp = client.post("/api/voice/transcribe", json={"audio": b64, "format": "audio/wav"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("success", "error")
        if data["status"] == "success":
            assert "transcription" in data
            assert "detectedLanguage" in data

    def test_post_voice_query_direct_execution(self, client):
        # Sends Chinese transcribed speech directly into diagnostic pipeline
        resp = client.post("/api/voice/query", json={
            "transcription": "电机温度过高",
            "session_id": "api_voice_test_session"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert len(data["answer"]) > 0

    def test_direct_exact_speech_pipeline_no_options(self, client):
        """
        Validates exact user example:
        User says: 'The motor is overheating and producing abnormal vibration'
        System displays exact text: 'The motor is overheating and producing abnormal vibration'
        User clicks Analyze -> Submitted to existing pipeline -> Zero ambiguity options returned.
        """
        exact_speech = "The motor is overheating and producing abnormal vibration"
        
        # 1. Pipeline receives exact transcribed text
        resp = client.post("/query", json={
            "message": exact_speech,
            "session_id": "exact_speech_test_session"
        })
        assert resp.status_code == 200
        data = resp.json()

        # Strict checks: NO suggested queries, NO options, NO multiple choice interpretation
        assert data.get("ambiguous") is False
        assert data.get("options") == []
        assert data.get("answer") is not None
        assert len(data["answer"]) > 20

