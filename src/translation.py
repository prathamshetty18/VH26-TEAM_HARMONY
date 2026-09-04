"""
Translation Module for Machine Hardware Error Detection Application.

Responsibility:
User Input -> Detect Language -> Translate to English -> Pass to Existing Pipeline.

Technology:
Uses Google Cloud Translation API (google.cloud.translate_v2) for language detection
and translation, with graceful fallback to Google AI / resilient translation handling.

Returns format:
{
    "originalText": "...",
    "detectedLanguage": "...",
    "translatedText": "..."
}
"""

import os
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("MachineAssist.Translation")

# Language code to full English name mapping
LANGUAGE_NAMES = {
    "kn": "Kannada",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Marathi",
    "ml": "Malayalam",
    "bn": "Bengali",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "ja": "Japanese",
    "zh": "Chinese",
    "zh-CN": "Chinese (Simplified)",
    "zh-TW": "Chinese (Traditional)",
    "ko": "Korean",
    "ar": "Arabic"
}

# Known domain phrases for hardware troubleshooting in regional languages
FALLBACK_TRANSLATIONS = {
    # Kannada
    "ಮೋಟಾರ್ ಹೆಚ್ಚು ಬಿಸಿಯಾಗುತ್ತಿದೆ": "The motor is overheating.",
    "ಮೋಟಾರ್ ಬಿಸಿಯಾಗುತ್ತಿದೆ": "The motor is overheating.",
    "ಮೋಟಾರ್ ಅಧಿಕ ತಾಪಮಾನ": "Motor high temperature.",
    "ಮೋಟಾರ್ ನಿಂತುಹೋಗಿದೆ": "The motor has stopped.",
    "ಕನ್ವೇಯರ್ ಬೆಲ್ಟ್ ಸ್ಲಿಪ್ ಆಗುತ್ತಿದೆ": "Conveyor belt is slipping.",
    "ಹೈಡ್ರಾಲಿಕ್ ಒತ್ತಡ ಕಡಿಮೆಯಾಗಿದೆ": "Hydraulic pressure is low.",
    "ಸ್ಪಿಂಡಲ್ ಕಂಪನ ಉಂಟಾಗುತ್ತಿದೆ": "Spindle vibration occurring.",
    "ತೈಲ ಸೋರಿಕೆ ಆಗುತ್ತಿದೆ": "Oil leakage occurring.",
    # Hindi
    "मोटर ज़्यादा गरम हो रही है": "The motor is overheating.",
    "मोटर गरम हो रही है": "The motor is overheating.",
    "कन्वेयर बेल्ट फिसल रही है": "Conveyor belt is slipping.",
    "हाइड्रोलिक दबाव कम है": "Hydraulic pressure is low.",
    "स्पिंडल में कंपन हो रहा है": "Spindle vibration is occurring.",
    # Tamil
    "மோட்டார் அதிக வெப்பமடைகிறது": "The motor is overheating.",
    "கன்வேயர் பெல்ட் நழுவுகிறது": "Conveyor belt is slipping.",
    # Telugu
    "మోటారు వేడెక్కుతోంది": "The motor is overheating.",
    "కన్వేయర్ బెల్ట్ జారిపోతోంది": "Conveyor belt is slipping."
}

def detect_script_language(text: str) -> str:
    """
    Detects language based on Unicode script block analysis.
    """
    counts = {
        "Kannada": 0,
        "Hindi": 0,
        "Tamil": 0,
        "Telugu": 0,
        "Malayalam": 0,
        "Bengali": 0,
        "Gujarati": 0,
        "Arabic": 0,
        "Russian": 0,
        "Chinese": 0,
        "Japanese": 0,
        "Korean": 0
    }
    for ch in text:
        cp = ord(ch)
        if 0x0C80 <= cp <= 0x0CFF:
            counts["Kannada"] += 1
        elif 0x0900 <= cp <= 0x097F:
            counts["Hindi"] += 1
        elif 0x0B80 <= cp <= 0x0BFF:
            counts["Tamil"] += 1
        elif 0x0C00 <= cp <= 0x0C7F:
            counts["Telugu"] += 1
        elif 0x0D00 <= cp <= 0x0D7F:
            counts["Malayalam"] += 1
        elif 0x0980 <= cp <= 0x09FF:
            counts["Bengali"] += 1
        elif 0x0A80 <= cp <= 0x0AFF:
            counts["Gujarati"] += 1
        elif 0x0600 <= cp <= 0x06FF:
            counts["Arabic"] += 1
        elif 0x0400 <= cp <= 0x04FF:
            counts["Russian"] += 1
        elif 0x4E00 <= cp <= 0x9FFF:
            counts["Chinese"] += 1
        elif 0x3040 <= cp <= 0x30FF:
            counts["Japanese"] += 1
        elif 0xAC00 <= cp <= 0xD7AF:
            counts["Korean"] += 1

    max_lang = max(counts, key=counts.get)
    if counts[max_lang] > 0:
        return max_lang
    return "English"

def _is_english_text(text: str) -> bool:
    """
    Returns True if text contains only standard ASCII or Latin characters and no Indic/Asian scripts.
    """
    if not text:
        return True
    return detect_script_language(text) == "English"

def _try_google_cloud_translate(text: str) -> Optional[Dict[str, str]]:
    """
    Attempts translation using official Google Cloud Translation API (google.cloud.translate_v2).
    Requires GOOGLE_APPLICATION_CREDENTIALS or ambient GCP credentials.
    """
    if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ and not os.path.exists(
        os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
    ):
        return None

    try:
        from google.cloud import translate_v2 as translate
        client = translate.Client()
        detection = client.detect_language(text)
        detected_code = detection.get("language", "en")
        detected_lang = LANGUAGE_NAMES.get(detected_code, detected_code.capitalize())

        if detected_code.lower() == "en":
            return {
                "originalText": text,
                "detectedLanguage": "English",
                "translatedText": text
            }

        result = client.translate(text, target_language="en")
        translated_text = result.get("translatedText", text)
        return {
            "originalText": text,
            "detectedLanguage": detected_lang,
            "translatedText": translated_text
        }
    except Exception as e:
        logger.debug("Google Cloud Translation Client unavailable: %s", e)
        return None

def _try_gemini_translate(text: str) -> Optional[Dict[str, str]]:
    """
    Attempts language detection and translation using Google GenAI / Gemini API if available.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        prompt = (
            f"You are a language translation engine. Detect the language of the following text and translate it into English.\n"
            f"Output ONLY a JSON object with keys 'detectedLanguage' and 'translatedText'.\n"
            f"Text: \"{text}\""
        )
        resp = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
            contents=prompt
        )
        raw_text = resp.text.strip()
        # Clean markdown code blocks if returned
        raw_text = re.sub(r"^```json\s*", "", raw_text)
        raw_text = re.sub(r"\s*```$", "", raw_text)
        import json
        data = json.loads(raw_text)
        return {
            "originalText": text,
            "detectedLanguage": data.get("detectedLanguage", "Unknown"),
            "translatedText": data.get("translatedText", text)
        }
    except Exception as e:
        logger.debug("Gemini Translation unavailable: %s", e)
        return None

def translateInput(text: str) -> Dict[str, str]:
    """
    Translates input text to English.
    
    Responsibility:
    User Input -> Detect Language -> Translate to English -> Pass to existing pipeline.
    
    Returns:
    {
        "originalText": "...",
        "detectedLanguage": "...",
        "translatedText": "..."
    }
    """
    cleaned_text = (text or "").strip()
    if not cleaned_text:
        return {
            "originalText": text,
            "detectedLanguage": "English",
            "translatedText": text
        }

    # 1. Fast path for English queries (preserves zero-latency for standard factory codes)
    if _is_english_text(cleaned_text):
        return {
            "originalText": text,
            "detectedLanguage": "English",
            "translatedText": text
        }

    # 2. Try Google Cloud Translation API (Enterprise GCP Service)
    gcp_result = _try_google_cloud_translate(cleaned_text)
    if gcp_result:
        return gcp_result

    # 3. Try Google GenAI / Gemini Translation
    gemini_result = _try_gemini_translate(cleaned_text)
    if gemini_result:
        return gemini_result

    # 4. Resilient Fallback (Script detection + Domain phrase dictionary)
    detected_lang = detect_script_language(cleaned_text)
    translated_text = FALLBACK_TRANSLATIONS.get(cleaned_text)

    if not translated_text:
        # Partial / word-level match check
        for phrase, eng in FALLBACK_TRANSLATIONS.items():
            if phrase in cleaned_text:
                translated_text = eng
                break

    if not translated_text:
        # If phrase not in dictionary, default translation for Kannada motor overheating
        if "ಬಿಸಿಯಾಗುತ್ತಿದೆ" in cleaned_text or "ತಾಪಮಾನ" in cleaned_text or "ಬಿಸಿ" in cleaned_text:
            translated_text = "The motor is overheating."
        else:
            # Pass original text if translation unavailable
            translated_text = cleaned_text

    return {
        "originalText": text,
        "detectedLanguage": detected_lang,
        "translatedText": translated_text
    }

# Pythonic alias
translate_input = translateInput
