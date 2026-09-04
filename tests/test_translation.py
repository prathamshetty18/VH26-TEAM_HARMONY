"""
Comprehensive Test Suite for Translation Module and End-to-End Pipeline Integration.

Tests:
1. Script detection across Indic and international alphabets
2. Romanized dialect detection (Hinglish, Kanglish, Tanglish)
3. Hardware entity and error code preservation
4. Domain symptom translation (overheating, oil pressure, spindle overload, e-stop, robot arm deviation)
5. Multilingual translations of the 4 demo benchmark queries
6. End-to-end integration test through FastAPI /query pipeline
"""

import os
import sys
import unittest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.translation import (
    translate_input,
    detect_script_language,
    detect_romanized_dialect,
    _is_english_text,
    _extract_machine_and_code
)
from src.api import app
from fastapi.testclient import TestClient

client = TestClient(app)


class TestTranslationScriptDetection(unittest.TestCase):
    """Verifies script detection across Indic and global Unicode blocks."""

    def test_kannada_detection(self):
        self.assertEqual(detect_script_language("ಮೋಟಾರ್ ಹೆಚ್ಚು ಬಿಸಿಯಾಗುತ್ತಿದೆ"), "Kannada")

    def test_hindi_detection(self):
        self.assertEqual(detect_script_language("मोटर ज़्यादा गरम हो रही है"), "Hindi")

    def test_tamil_detection(self):
        self.assertEqual(detect_script_language("மோட்டார் அதிக வெப்பமடைகிறது"), "Tamil")

    def test_telugu_detection(self):
        self.assertEqual(detect_script_language("మోటారు వేడెక్కుతోంది"), "Telugu")

    def test_bengali_detection(self):
        self.assertEqual(detect_script_language("মোটর অতিরিক্ত গরম হয়ে যাচ্ছে"), "Bengali")

    def test_gujarati_detection(self):
        self.assertEqual(detect_script_language("મોટર વધુ પડતી ગરમ થઈ રહી છે"), "Gujarati")

    def test_malayalam_detection(self):
        self.assertEqual(detect_script_language("മോട്ടോർ അമിതമായി ചൂടാകുന്നു"), "Malayalam")

    def test_chinese_detection(self):
        self.assertEqual(detect_script_language("电机过热"), "Chinese")

    def test_japanese_detection(self):
        self.assertEqual(detect_script_language("モーターが過熱しています"), "Japanese")

    def test_english_detection(self):
        self.assertEqual(detect_script_language("What does E101 mean on CNC-100?"), "English")


class TestRomanizedDialectDetection(unittest.TestCase):
    """Verifies recognition of phonetic Indian regional keywords written in Latin script."""

    def test_hinglish(self):
        res = detect_romanized_dialect("motor garam ho raha hai")
        self.assertEqual(res, "Hindi (Romanized)")

    def test_hinglish_error_code(self):
        res = detect_romanized_dialect("cnc-100 me e101 ka matlab kya hai")
        self.assertEqual(res, "Hindi (Romanized)")

    def test_kanglish(self):
        res = detect_romanized_dialect("motor thumba bisi aagthide")
        self.assertEqual(res, "Kannada (Romanized)")

    def test_pure_english_not_dialect(self):
        self.assertIsNone(detect_romanized_dialect("Why is Press-200 stopping due to oil pressure?"))


class TestEntityPreservation(unittest.TestCase):
    """Verifies that machine names and error codes are extracted accurately without corruption."""

    def test_cnc100_and_e101(self):
        m, c = _extract_machine_and_code("CNC-100 ನಲ್ಲಿ E101 ಅರ್ಥವೇನು?")
        self.assertEqual(m, "CNC-100")
        self.assertEqual(c, "E101")

    def test_press200_and_e202(self):
        m, c = _extract_machine_and_code("Press-200 पर E202 क्यों आ रहा है?")
        self.assertEqual(m, "Press-200")
        self.assertEqual(c, "E202")

    def test_robotarm300_and_r101(self):
        m, c = _extract_machine_and_code("RobotArm-300 இல் R101 என்றால் என்ன?")
        self.assertEqual(m, "RobotArm-300")
        self.assertEqual(c, "R101")


class TestDomainTranslations(unittest.TestCase):
    """Verifies domain symptom translations across languages."""

    def test_kannada_overheating(self):
        res = translate_input("ಮೋಟಾರ್ ಹೆಚ್ಚು ಬಿಸಿಯಾಗುತ್ತಿದೆ")
        self.assertEqual(res["detectedLanguage"], "Kannada")
        self.assertEqual(res["translatedText"], "The motor is overheating.")

    def test_hindi_overheating(self):
        res = translate_input("मोटर ज़्यादा गरम हो रही है")
        self.assertEqual(res["detectedLanguage"], "Hindi")
        self.assertEqual(res["translatedText"], "The motor is overheating.")

    def test_tamil_overheating(self):
        res = translate_input("மோட்டார் அதிக வெப்பமடைகிறது")
        self.assertEqual(res["detectedLanguage"], "Tamil")
        self.assertEqual(res["translatedText"], "The motor is overheating.")

    def test_telugu_overheating(self):
        res = translate_input("మోటారు వేడెక్కుతోంది")
        self.assertEqual(res["detectedLanguage"], "Telugu")
        self.assertEqual(res["translatedText"], "The motor is overheating.")

    def test_german_query(self):
        res = translate_input("Warum stoppt Press-200 wegen Öldruck?")
        self.assertEqual(res["translatedText"], "Why is Press-200 stopping due to oil pressure?")

    def test_spanish_query(self):
        res = translate_input("¿Qué significa E101 en CNC-100?")
        self.assertEqual(res["translatedText"], "What does E101 mean on CNC-100?")

    def test_french_query(self):
        res = translate_input("Que signifie E101 sur CNC-100?")
        self.assertEqual(res["translatedText"], "What does E101 mean on CNC-100?")

    def test_chinese_query(self):
        res = translate_input("CNC-100上的E101是什么意思？")
        self.assertEqual(res["detectedLanguage"], "Chinese")
        self.assertEqual(res["translatedText"], "What does E101 mean on CNC-100?")

    def test_japanese_query(self):
        res = translate_input("CNC-100のE101はどういう意味ですか？")
        self.assertEqual(res["detectedLanguage"], "Japanese")
        self.assertEqual(res["translatedText"], "What does E101 mean on CNC-100?")

    def test_hinglish_query(self):
        res = translate_input("cnc-100 me e101 ka matlab kya hai")
        self.assertEqual(res["detectedLanguage"], "Hindi (Romanized)")
        self.assertEqual(res["translatedText"], "What does E101 mean on CNC-100?")

    def test_kanglish_query(self):
        res = translate_input("motor thumba bisi aagthide")
        self.assertEqual(res["detectedLanguage"], "Kannada (Romanized)")
        self.assertEqual(res["translatedText"], "The motor is overheating.")


class TestDemoQueryTranslations(unittest.TestCase):
    """Verifies that the 4 verified Section 6 demo queries translate accurately from Kannada and Hindi."""

    # 1. Exact Code: "What does E101 mean on CNC-100?"
    def test_demo1_kannada(self):
        res = translate_input("CNC-100 ನಲ್ಲಿ E101 ಅರ್ಥವೇನು?")
        self.assertEqual(res["translatedText"], "What does E101 mean on CNC-100?")

    def test_demo1_hindi(self):
        res = translate_input("CNC-100 पर E101 का क्या मतलब है?")
        self.assertEqual(res["translatedText"], "What does E101 mean on CNC-100?")

    # 2. Symptom Search: "Why is Press-200 stopping due to oil pressure?"
    def test_demo2_kannada(self):
        res = translate_input("Press-200 ನಲ್ಲಿ ತೈಲ ಒತ್ತಡದಿಂದ ಏಕೆ ನಿಲ್ಲುತ್ತಿದೆ?")
        self.assertEqual(res["translatedText"], "Why is Press-200 stopping due to oil pressure?")

    def test_demo2_hindi(self):
        res = translate_input("Press-200 तेल के दबाव के कारण क्यों रुक रहा है?")
        self.assertEqual(res["translatedText"], "Why is Press-200 stopping due to oil pressure?")

    # 3. Ambiguity Check: "What does E101 mean?"
    def test_demo3_kannada(self):
        res = translate_input("E101 ಅರ್ಥವೇನು?")
        self.assertEqual(res["translatedText"], "What does E101 mean?")

    def test_demo3_hindi(self):
        res = translate_input("E101 का क्या मतलब है?")
        self.assertEqual(res["translatedText"], "What does E101 mean?")

    # 4. Insufficient Info: "How do I replace spindle bearing on CNC-100?"
    def test_demo4_kannada(self):
        res = translate_input("CNC-100 ನಲ್ಲಿ ಸ್ಪಿಂಡಲ್ ಬೇರಿಂಗ್ ಅನ್ನು ಹೇಗೆ ಬದಲಾಯಿಸುವುದು?")
        self.assertEqual(res["translatedText"], "How do I replace spindle bearing on CNC-100?")

    def test_demo4_hindi(self):
        res = translate_input("CNC-100 पर स्पिंडल बेयरिंग कैसे बदलें?")
        self.assertEqual(res["translatedText"], "How do I replace spindle bearing on CNC-100?")


class TestPipelineEndToEndWithTranslation(unittest.TestCase):
    """Verifies that non-English queries pass through translation and retrieve correct manual answers."""

    def test_e2e_kannada_query(self):
        resp = client.post("/query", json={
            "message": "CNC-100 ನಲ್ಲಿ E101 ಅರ್ಥವೇನು?",
            "session_id": "test_sess_kannada"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("Excessive motor temperature", data["answer"])
        self.assertTrue(any("cnc100.txt" in s.get("manual", "") for s in data["sources"]))

    def test_e2e_hindi_query(self):
        resp = client.post("/query", json={
            "message": "Press-200 तेल के दबाव के कारण क्यों रुक रहा है?",
            "session_id": "test_sess_hindi"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("Hydraulic oil pressure low", data["answer"])
        self.assertTrue(any("press200.txt" in s.get("manual", "") for s in data["sources"]))

    def test_e2e_hinglish_query(self):
        resp = client.post("/query", json={
            "message": "cnc-100 me e101 kya hai",
            "session_id": "test_sess_hinglish"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("Excessive motor temperature", data["answer"])

    def test_e2e_dedicated_translate_endpoint(self):
        resp = client.post("/api/translate", json={
            "text": "ಮೋಟಾರ್ ಹೆಚ್ಚು ಬಿಸಿಯಾಗುತ್ತಿದೆ"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["detectedLanguage"], "Kannada")
        self.assertEqual(data["translatedText"], "The motor is overheating.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
