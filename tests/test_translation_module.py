# -*- coding: utf-8 -*-
"""
Tests for Multilingual Translation Module (src/translation.py)

Validates:
1. Automatic Language Detection for:
   - Simplified Chinese (zh-CN)
   - Japanese (ja)
   - German (de)
   - English (en)
2. English Pass-Through (no translation applied).
3. Translation to English for Chinese, Japanese, and German inputs.
4. User example phrases:
   - Chinese: "电机温度过高" -> "The motor temperature is too high."
   - Japanese: "モーターの温度が高すぎます" -> "The motor temperature is too high."
   - German: "Die Motortemperatur ist zu hoch." -> "The motor temperature is too high."
5. Google Cloud Translation API client integration & fallback.
6. Seamless forwarding to the existing machine error detection pipeline.
"""

import sys
import os
from unittest.mock import MagicMock, patch
import pytest

# Ensure repository root is in sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.translation import (
    MultilingualTranslationModule,
    detect_language,
    translate_input,
    translateInput,
    process_machine_instruction
)


class TestLanguageDetection:
    """Tests language detection for Chinese, Japanese, German, and English."""

    def test_detect_chinese(self):
        chinese_samples = [
            "电机温度过高",
            "主轴振动过大",
            "传送带打滑",
            "液压油温过高",
        ]
        for sample in chinese_samples:
            res = detect_language(sample)
            assert res == "Simplified Chinese", f"Failed for Chinese input: {sample}"

    def test_detect_japanese(self):
        japanese_samples = [
            "モーターの温度が高すぎます",
            "コンベアベルトが滑っています",
            "油圧が低すぎます",
            "スピンドル異常音",
        ]
        for sample in japanese_samples:
            res = detect_language(sample)
            assert res == "Japanese", f"Failed for Japanese input: {sample}"

    def test_detect_german(self):
        german_samples = [
            "Die Motortemperatur ist zu hoch.",
            "Das Förderband rutscht",
            "Hydraulikdruck zu niedrig",
            "Spindelvibration bei hoher Drehzahl",
        ]
        for sample in german_samples:
            res = detect_language(sample)
            assert res == "German", f"Failed for German input: {sample}"

    def test_detect_english(self):
        english_samples = [
            "The motor temperature is too high.",
            "What does error E101 mean on CNC-100?",
            "Hydraulic pressure is dropping on Press-200",
            "Conveyor belt is slipping",
        ]
        for sample in english_samples:
            res = detect_language(sample)
            assert res == "English", f"Failed for English input: {sample}"


class TestTranslationFlow:
    """Tests translation to English and English pass-through."""

    def test_chinese_translation(self):
        # User requested exact example: "电机温度过高" -> "The motor temperature is too high."
        res = translate_input("电机温度过高")
        assert res["detectedLanguage"] == "Simplified Chinese"
        assert res["detectedCode"] in ["zh-CN", "zh"]
        assert res["translatedText"] == "The motor temperature is too high."
        assert res["isTranslated"] is True

    def test_japanese_translation(self):
        # User requested exact example: "モーターの温度が高すぎます" -> "The motor temperature is too high."
        res = translate_input("モーターの温度が高すぎます")
        assert res["detectedLanguage"] == "Japanese"
        assert res["detectedCode"] == "ja"
        assert res["translatedText"] == "The motor temperature is too high."
        assert res["isTranslated"] is True

    def test_german_translation(self):
        # User requested exact example: "Die Motortemperatur ist zu hoch." -> "The motor temperature is too high."
        res = translate_input("Die Motortemperatur ist zu hoch.")
        assert res["detectedLanguage"] == "German"
        assert res["detectedCode"] == "de"
        assert res["translatedText"] == "The motor temperature is too high."
        assert res["isTranslated"] is True

    def test_english_pass_through(self):
        # English must NOT be translated. Passed directly.
        english_text = "The motor temperature is too high."
        res = translate_input(english_text)
        assert res["detectedLanguage"] == "English"
        assert res["detectedCode"] == "en"
        assert res["translatedText"] == english_text
        assert res["isTranslated"] is False

    def test_empty_input(self):
        res = translate_input("")
        assert res["detectedLanguage"] == "English"
        assert res["translatedText"] == ""
        assert res["isTranslated"] is False


class TestGoogleCloudTranslationIntegration:
    """Tests Google Cloud Translation API client interactions and mocking."""

    def test_google_cloud_client_mock(self):
        mock_client = MagicMock()
        mock_client.detect_language.return_value = {"language": "de", "confidence": 0.99}
        mock_client.translate.return_value = {"translatedText": "The motor temperature is too high."}

        module = MultilingualTranslationModule()
        module._client = mock_client

        # Language Detection via mock GCP client
        det = module.detect_language("Die Motortemperatur ist zu hoch.")
        assert det["language"] == "de"
        assert det["language_name"] == "German"
        mock_client.detect_language.assert_called_once_with("Die Motortemperatur ist zu hoch.")

        # Translation via mock GCP client
        result = module.translate_input("Die Motortemperatur ist zu hoch.")
        assert result["translatedText"] == "The motor temperature is too high."
        assert result["detectedLanguage"] == "German"
        assert result["isTranslated"] is True
        mock_client.translate.assert_called_once_with("Die Motortemperatur ist zu hoch.", target_language="en")


class TestPipelineForwarding:
    """Tests forwarding the English translated text directly to the machine error detection pipeline."""

    def test_forwarding_to_custom_pipeline_fn(self):
        received_query = []

        def mock_error_detection_pipeline(query: str, **kwargs):
            received_query.append(query)
            return {"status": "diagnosed", "input_received": query}

        module = MultilingualTranslationModule()

        # 1. Chinese input forward
        out_zh = module.process_and_forward("电机温度过高", pipeline_fn=mock_error_detection_pipeline)
        assert out_zh["status"] == "diagnosed"
        assert received_query[-1] == "The motor temperature is too high."

        # 2. Japanese input forward
        out_ja = module.process_and_forward("モーターの温度が高すぎます", pipeline_fn=mock_error_detection_pipeline)
        assert out_ja["status"] == "diagnosed"
        assert received_query[-1] == "The motor temperature is too high."

        # 3. German input forward
        out_de = module.process_and_forward("Die Motortemperatur ist zu hoch.", pipeline_fn=mock_error_detection_pipeline)
        assert out_de["status"] == "diagnosed"
        assert received_query[-1] == "The motor temperature is too high."

        # 4. English input forward (untranslated)
        out_en = module.process_and_forward("The motor temperature is too high.", pipeline_fn=mock_error_detection_pipeline)
        assert out_en["status"] == "diagnosed"
        assert received_query[-1] == "The motor temperature is too high."

    def test_forwarding_to_existing_fastapi_pipeline(self):
        """Validates that the existing FastAPI endpoint (/query) processes multilingual inputs."""
        from fastapi.testclient import TestClient
        from src.api import app

        client = TestClient(app)

        # Chinese input: "电机温度过高" -> translated to "The motor temperature is too high." -> passed to existing pipeline
        resp = client.post("/query", json={"message": "电机温度过高", "session_id": "test_multilingual_zh"})
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert isinstance(data["answer"], str)
        assert len(data["answer"]) > 0

        # Japanese input: "モーターの温度が高すぎます" -> translated to "The motor temperature is too high." -> passed to existing pipeline
        resp = client.post("/query", json={"message": "モーターの温度が高すぎます", "session_id": "test_multilingual_ja"})
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert isinstance(data["answer"], str)
        assert len(data["answer"]) > 0

        # German input: "Die Motortemperatur ist zu hoch." -> translated to "The motor temperature is too high." -> passed to existing pipeline
        resp = client.post("/query", json={"message": "Die Motortemperatur ist zu hoch.", "session_id": "test_multilingual_de"})
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert isinstance(data["answer"], str)
        assert len(data["answer"]) > 0
