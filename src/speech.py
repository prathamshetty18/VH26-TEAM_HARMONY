"""
Modular Voice Query & Speech-to-Text Service for Machine Hardware Error Detection Application.

Flow:
Voice Input (Audio)
    ↓
Google Cloud Speech-to-Text API (en-US, zh-CN, ja-JP, de-DE)
    ↓
Language Detection (English, Simplified Chinese, Japanese, German)
    ↓
If non-English (Chinese, Japanese, German):
    Pass through EXISTING Google Translation Module (src/translation.py) → English Text
If English:
    Direct English Text (no translation needed)
    ↓
Editable Preview (User can review & edit transcription before submission)
    ↓
Existing Machine Fault Detection / AI Diagnosis Pipeline (handle_query / /query)
"""

import os
import re
import io
import wave
import base64
import logging
from typing import Dict, Any, Optional, Tuple, List, Callable

from src.translation import (
    MultilingualTranslationModule,
    detect_language as translation_detect_language,
    translate_input as translation_translate_input
)

logger = logging.getLogger("MachineAssist.Speech")

# Supported voice recognition languages
SUPPORTED_VOICE_LANGUAGES = {
    "en": {"code": "en-US", "name": "English", "flag": "🇺🇸"},
    "zh": {"code": "zh-CN", "name": "Simplified Chinese", "flag": "🇨🇳"},
    "zh-CN": {"code": "zh-CN", "name": "Simplified Chinese", "flag": "🇨🇳"},
    "ja": {"code": "ja-JP", "name": "Japanese", "flag": "🇯🇵"},
    "de": {"code": "de-DE", "name": "German", "flag": "🇩🇪"},
}

VOICE_LANGUAGE_CODES = ["en-US", "zh-CN", "ja-JP", "de-DE"]

# Sample voice benchmarks for instant 1-click testing across all 4 languages
VOICE_BENCHMARK_SAMPLES = [
    {
        "id": "sample_en_e101",
        "language": "en",
        "language_name": "English",
        "sample_text": "What does error E101 mean on the CNC-100?",
        "english_text": "What does error E101 mean on the CNC-100?",
        "machine": "CNC-100",
        "is_translated": False,
        "description": "CNC Machining Center spindle fault inquiry (English)"
    },
    {
        "id": "sample_zh_motor",
        "language": "zh-CN",
        "language_name": "Simplified Chinese",
        "sample_text": "电机温度过高",
        "english_text": "The motor temperature is too high.",
        "machine": "Conveyor Belt System",
        "is_translated": True,
        "description": "Conveyor motor thermal overload symptom (Chinese)"
    },
    {
        "id": "sample_ja_spindle",
        "language": "ja",
        "language_name": "Japanese",
        "sample_text": "モーターの温度が高すぎます",
        "english_text": "The motor temperature is too high.",
        "machine": "CNC Milling Machine",
        "is_translated": True,
        "description": "Motor overheating symptom (Japanese)"
    },
    {
        "id": "sample_de_press",
        "language": "de",
        "language_name": "German",
        "sample_text": "Die Motortemperatur ist zu hoch.",
        "english_text": "The motor temperature is too high.",
        "machine": "Hydraulic Press",
        "is_translated": True,
        "description": "Hydraulic unit motor temperature warning (German)"
    },
    {
        "id": "sample_zh_vibration",
        "language": "zh-CN",
        "language_name": "Simplified Chinese",
        "sample_text": "主轴振动过大",
        "english_text": "Spindle vibration is excessive.",
        "machine": "CNC-100",
        "is_translated": True,
        "description": "Spindle mechanical runout symptom (Chinese)"
    },
    {
        "id": "sample_de_pressure",
        "language": "de",
        "language_name": "German",
        "sample_text": "Hydraulikdruck ist zu niedrig",
        "english_text": "Hydraulic pressure is too low.",
        "machine": "Press-200",
        "is_translated": True,
        "description": "Hydraulic circuit pressure drop (German)"
    }
]


class GoogleSpeechToTextService:
    """
    Google Cloud Speech-to-Text service with multi-tier failover and
    seamless integration into existing translation and diagnostic pipelines.
    """

    def __init__(
        self,
        credentials_path: Optional[str] = None,
        api_key: Optional[str] = None,
        translation_module: Optional[MultilingualTranslationModule] = None
    ):
        self.credentials_path = credentials_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.api_key = api_key or os.getenv("GOOGLE_SPEECH_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self._speech_client = None
        self._translation_module = translation_module or MultilingualTranslationModule(credentials_path=self.credentials_path)
        self.enabled = os.getenv("VOICE_QUERY_ENABLED", "true").lower() in ("1", "true", "yes")
        self._init_speech_client()

    def _init_speech_client(self):
        """Initializes the official google.cloud.speech client if available."""
        try:
            from google.cloud import speech_v1 as speech
            if self.credentials_path and os.path.exists(self.credentials_path):
                self._speech_client = speech.SpeechClient.from_service_account_file(self.credentials_path)
                logger.info("Google Cloud Speech client initialized from credentials file.")
            elif "GOOGLE_APPLICATION_CREDENTIALS" in os.environ or os.path.exists(
                os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
            ):
                self._speech_client = speech.SpeechClient()
                logger.info("Google Cloud Speech client initialized from environment.")
        except Exception as e:
            logger.debug("Google Cloud Speech client could not be initialized: %s", e)
            self._speech_client = None

    @property
    def speech_client(self):
        return self._speech_client

    @speech_client.setter
    def speech_client(self, value):
        self._speech_client = value

    def is_available(self) -> bool:
        """Returns True if the voice service is enabled."""
        return self.enabled

    def _call_gcp_speech_client(
        self,
        audio_bytes: bytes,
        sample_rate_hertz: int = 48000,
        encoding_str: str = "WEBM_OPUS",
        language_code: str = "en-US"
    ) -> Optional[Tuple[str, str, float]]:
        """
        Uses the official google.cloud.speech_v1 client to transcribe audio.
        Returns: (transcribed_text, detected_language_code, confidence)
        """
        if not self._speech_client:
            return None

        try:
            from google.cloud import speech_v1 as speech

            encoding_map = {
                "WEBM_OPUS": speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                "LINEAR16": speech.RecognitionConfig.AudioEncoding.LINEAR16,
                "OGG_OPUS": speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
                "FLAC": speech.RecognitionConfig.AudioEncoding.FLAC,
            }
            enc = encoding_map.get(encoding_str.upper(), speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED)

            alt_langs = [l for l in VOICE_LANGUAGE_CODES if l != language_code]
            config = speech.RecognitionConfig(
                encoding=enc,
                sample_rate_hertz=sample_rate_hertz,
                language_code=language_code,
                alternative_language_codes=alt_langs,
                enable_automatic_punctuation=True,
            )
            audio = speech.RecognitionAudio(content=audio_bytes)

            response = self._speech_client.recognize(config=config, audio=audio)
            for result in response.results:
                if result.alternatives:
                    best = result.alternatives[0]
                    detected_lang = getattr(result, "language_code", language_code) or language_code
                    return best.transcript.strip(), detected_lang, float(best.confidence or 0.95)
        except Exception as e:
            logger.debug("Official Google Cloud Speech client call failed: %s", e)

        return None

    def _call_gcp_speech_rest_api(
        self,
        audio_bytes: bytes,
        language_code: str = "en-US"
    ) -> Optional[Tuple[str, str, float]]:
        """
        Calls Google Cloud Speech-to-Text v1 REST API.
        """
        if not self.api_key:
            return None

        try:
            import requests
            url = f"https://speech.googleapis.com/v1/speech:recognize?key={self.api_key}"
            alt_langs = [l for l in VOICE_LANGUAGE_CODES if l != language_code]

            payload = {
                "config": {
                    "languageCode": language_code,
                    "alternativeLanguageCodes": alt_langs,
                    "enableAutomaticPunctuation": True,
                },
                "audio": {
                    "content": base64.b64encode(audio_bytes).decode("utf-8")
                }
            }

            resp = requests.post(url, json=payload, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                if results and results[0].get("alternatives"):
                    best = results[0]["alternatives"][0]
                    detected = results[0].get("languageCode", language_code)
                    confidence = float(best.get("confidence", 0.95))
                    return best.get("transcript", "").strip(), detected, confidence
        except Exception as e:
            logger.debug("Google Cloud Speech REST API call failed: %s", e)

        return None

    def _call_gemini_audio_transcribe(
        self,
        audio_bytes: bytes,
        mime_type: str = "audio/webm"
    ) -> Optional[Tuple[str, str, float]]:
        """
        High-accuracy fallback using Google GenAI (Gemini) audio understanding.
        Extracts exact technical speech preserving industrial equipment codes.
        """
        api_key = os.getenv("GEMINI_API_KEY") or self.api_key
        if not api_key:
            return None

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            prompt = (
                "You are a strict verbatim speech-to-text transcription engine.\n"
                "Listen to the user's speech in the provided audio.\n"
                "Transcribe the EXACT words spoken by the user verbatim.\n"
                "CRITICAL INSTRUCTIONS:\n"
                "- Do NOT summarize, rewrite, rephrase, or correct the speech.\n"
                "- Do NOT replace the user's words with a canned query or error code.\n"
                "- Do NOT interpret the user's speech into predefined options or questions.\n"
                "- If the user says 'The motor is overheating and producing abnormal vibration', transcribe: 'The motor is overheating and producing abnormal vibration'.\n"
                "Format output as JSON: {\"transcription\": \"<exact words spoken>\", \"language\": \"<en|zh-CN|ja|de>\"}"
            )

            part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
            response = client.models.generate_content(
                model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
                contents=[part, prompt]
            )

            text_out = response.text.strip()
            # Extract JSON from response
            json_match = re.search(r"\{[\s\S]*\}", text_out)
            if json_match:
                import json
                parsed = json.loads(json_match.group(0))
                transcription = parsed.get("transcription", "").strip()
                lang = parsed.get("language", "en")
                if transcription:
                    return transcription, lang, 0.98

            if text_out:
                # Clean any markdown or quotes
                cleaned_text = re.sub(r"^```json\s*", "", text_out)
                cleaned_text = re.sub(r"\s*```$", "", cleaned_text).strip()
                return cleaned_text, "en", 0.90
        except Exception as e:
            logger.debug("Gemini audio transcription fallback failed: %s", e)

        return None

    def _call_google_speech_recognition(
        self,
        audio_bytes: bytes,
        language_code: str = "en-US"
    ) -> Optional[Tuple[str, str, float]]:
        """
        Uses Google's Speech-to-Text service via the speech_recognition engine.
        Accepts WAV audio or wraps PCM audio directly.
        """
        try:
            import speech_recognition as sr
            r = sr.Recognizer()

            wav_data = audio_bytes
            # If not already a RIFF/WAV header, attempt wrapping raw PCM 16kHz mono 16-bit
            if not audio_bytes.startswith(b"RIFF"):
                try:
                    pcm_buf = io.BytesIO()
                    with wave.open(pcm_buf, "wb") as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(16000)
                        wf.writeframes(audio_bytes)
                    wav_data = pcm_buf.getvalue()
                except Exception:
                    pass

            with sr.AudioFile(io.BytesIO(wav_data)) as source:
                audio = r.record(source)

            # Query Google Speech-to-Text
            target_langs = [language_code]
            if language_code != "en-US":
                target_langs.append("en-US")

            for lang in target_langs:
                try:
                    text = r.recognize_google(audio, language=lang)
                    if text and text.strip():
                        return text.strip(), lang, 0.96
                except sr.UnknownValueError:
                    continue
                except sr.RequestError as e:
                    logger.debug("Google STT service unreachable for %s: %s", lang, e)
                    break
        except Exception as e:
            logger.debug("SpeechRecognition processing failed: %s", e)

        return None

    def transcribe_audio(
        self,
        audio_bytes: bytes,
        mime_type: str = "audio/webm",
        language_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main speech-to-text entry point adhering to exact user contract:
        1. Convert speech to text via Google Cloud Speech-to-Text API.
        2. Detect the spoken language (English, Simplified Chinese, Japanese, German).
        3. If English: direct English output (isTranslated=False).
        4. If Chinese, Japanese, or German: pass to EXISTING Google Translation module → English Text.
        5. Return transcription and translation for display and user editing.
        """
        if not self.enabled:
            return {
                "status": "error",
                "error": "Voice query feature is currently disabled",
                "transcription": "",
                "detectedLanguage": "en",
                "languageName": "English",
                "isTranslated": False
            }

        if not audio_bytes or len(audio_bytes) < 32:
            return {
                "status": "error",
                "error": "Empty audio recording. No speech detected. Please try again.",
                "transcription": "",
                "detectedLanguage": "en",
                "languageName": "English",
                "isTranslated": False
            }

        target_lang = "en-US"
        if language_hint:
            norm_hint = language_hint.lower().strip()
            if norm_hint in ("zh", "zh-cn", "chinese"):
                target_lang = "zh-CN"
            elif norm_hint in ("ja", "ja-jp", "japanese"):
                target_lang = "ja-JP"
            elif norm_hint in ("de", "de-de", "german"):
                target_lang = "de-DE"
            elif norm_hint in ("en", "en-us", "english"):
                target_lang = "en-US"

        # Determine audio encoding
        encoding_str = "WEBM_OPUS"
        if "wav" in mime_type or audio_bytes.startswith(b"RIFF"):
            encoding_str = "LINEAR16"
        elif "ogg" in mime_type or audio_bytes.startswith(b"OggS"):
            encoding_str = "OGG_OPUS"

        # 1. Official Google Cloud Speech Client (if GCP credentials configured)
        recognition = self._call_gcp_speech_client(
            audio_bytes,
            encoding_str=encoding_str,
            language_code=target_lang
        )

        # 2. Google Cloud Speech REST API (if API key configured)
        if not recognition:
            recognition = self._call_gcp_speech_rest_api(
                audio_bytes,
                language_code=target_lang
            )

        # 3. Google Speech-to-Text service via SpeechRecognition (Free Google Cloud STT)
        if not recognition:
            recognition = self._call_google_speech_recognition(
                audio_bytes,
                language_code=target_lang
            )

        # 4. Google GenAI / Gemini Audio Transcription
        if not recognition:
            recognition = self._call_gemini_audio_transcribe(
                audio_bytes,
                mime_type=mime_type
            )

        if not recognition or not recognition[0] or not recognition[0].strip():
            return {
                "status": "error",
                "error": "No speech detected. Please try again.",
                "transcription": "",
                "detectedLanguage": "en",
                "languageName": "English",
                "isTranslated": False
            }

        raw_transcription, detected_lang_code, confidence = recognition

        # Refine language detection using both speech API and existing translation module
        lang_name, canonical_code = self._resolve_language(raw_transcription, detected_lang_code)

        # Step 4 & 5: Language-based Routing to Existing Translation Module
        if canonical_code == "en" or lang_name == "English":
            # If English: send transcribed text directly to existing pipeline without translation
            english_text = raw_transcription
            is_translated = False
        else:
            # If Chinese, Japanese, or German: send transcription to EXISTING Google Translation module
            trans_result = self._translation_module.translate_input(raw_transcription)
            english_text = trans_result.get("translatedText", raw_transcription)
            is_translated = True

        return {
            "status": "success",
            "transcription": raw_transcription,
            "detectedLanguage": canonical_code,
            "languageName": lang_name,
            "englishText": english_text,
            "isTranslated": is_translated,
            "confidence": round(confidence, 2),
            "state": "complete"
        }

    def _resolve_language(self, text: str, speech_code: str) -> Tuple[str, str]:
        """
        Cross-checks Speech API language code with domain script heuristic from src/translation.py.
        """
        # First check text content using existing translation module's detect_language
        text_detected_name = self._translation_module.detect_language(text).get("language_name", "")

        if text_detected_name in ("Simplified Chinese", "Japanese", "German", "English"):
            if text_detected_name == "Simplified Chinese":
                return "Simplified Chinese", "zh-CN"
            elif text_detected_name == "Japanese":
                return "Japanese", "ja"
            elif text_detected_name == "German":
                return "German", "de"
            elif text_detected_name == "English":
                return "English", "en"

        # Fallback to speech recognition code
        sc = speech_code.lower()
        if "zh" in sc:
            return "Simplified Chinese", "zh-CN"
        elif "ja" in sc:
            return "Japanese", "ja"
        elif "de" in sc:
            return "German", "de"
        return "English", "en"

    def process_voice_and_forward(
        self,
        transcription: str,
        edited_transcription: Optional[str] = None,
        pipeline_fn: Optional[Callable[[str], Any]] = None,
        **pipeline_kwargs
    ) -> Any:
        """
        Takes the transcribed (and optionally edited) text and connects it directly
        to the EXISTING machine fault detection pipeline.

        CRITICAL: Does NOT create a separate diagnosis system.
        Calls the exact same pipeline used by typed queries.
        """
        final_text = (edited_transcription or transcription or "").strip()
        if not final_text:
            raise ValueError("Query text cannot be empty.")

        # Detect language of the final text
        det = self._translation_module.detect_language(final_text)
        lang_name = det.get("language_name", "English")

        if lang_name == "English":
            english_query = final_text
        else:
            # Pass through existing translation module
            trans_res = self._translation_module.translate_input(final_text)
            english_query = trans_res.get("translatedText", final_text)

        # Forward directly to existing pipeline
        if pipeline_fn is not None:
            return pipeline_fn(english_query, **pipeline_kwargs)

        from src.api import handle_query, QueryRequest
        req = QueryRequest(
            message=english_query,
            session_id=pipeline_kwargs.get("session_id", "default_session"),
            machine_filter=pipeline_kwargs.get("machine_filter")
        )
        return handle_query(req)


# Global singleton instance
speech_service = GoogleSpeechToTextService()
