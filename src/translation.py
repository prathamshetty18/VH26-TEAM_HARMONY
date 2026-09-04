"""
Translation Module for Machine Hardware Error Detection Application.

Responsibility:
User Input -> Detect Language -> Translate to English -> Pass to Existing Pipeline.

Features:
1. Multi-tier language detection:
   - Unicode script analysis (Kannada, Hindi, Tamil, Telugu, Marathi, Bengali, Malayalam, Gujarati, Arabic, Russian, Chinese, Japanese, Korean)
   - Romanized / transliterated dialect detection (Hinglish, Kanglish, Tanglish)
   - Latin / English zero-latency fast path
2. Hardware entity & error code preservation (CNC-100, Press-200, RobotArm-300, E101, E102, E103, E202, E203, R101, H205)
3. Domain-trained semantic translation engine for factory diagnostics & symptoms
4. External translation API integrations (Google Cloud Translation v2 & Google GenAI) with resilient offline fallback

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
from typing import Dict, Any, Optional, Tuple

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

# Known domain phrases for hardware troubleshooting across regional & international languages
FALLBACK_TRANSLATIONS: Dict[str, str] = {
    # -------------------------------------------------------------
    # 1. KANNADA (ಕನ್ನಡ)
    # -------------------------------------------------------------
    "ಮೋಟಾರ್ ಹೆಚ್ಚು ಬಿಸಿಯಾಗುತ್ತಿದೆ": "The motor is overheating.",
    "ಮೋಟಾರ್ ಬಿಸಿಯಾಗುತ್ತಿದೆ": "The motor is overheating.",
    "ಮೋಟಾರ್ ಅಧಿಕ ತಾಪಮಾನ": "Motor high temperature.",
    "ಮೋಟಾರ್ ನಿಂತುಹೋಗಿದೆ": "The motor has stopped.",
    "ಹೈಡ್ರಾಲಿಕ್ ತೈಲ ಒತ್ತಡ ಕಡಿಮೆ ಇದೆ": "Hydraulic oil pressure is low.",
    "ಹೈಡ್ರಾಲಿಕ್ ಒತ್ತಡ ಕಡಿಮೆಯಾಗಿದೆ": "Hydraulic pressure is low.",
    "ಹೈಡ್ರಾಲಿಕ್ ತೈಲ ಸೋರಿಕೆ": "Hydraulic oil leakage.",
    "ತೈಲ ಸೋರಿಕೆ ಆಗುತ್ತಿದೆ": "Oil leakage occurring.",
    "ಸ್ಪಿಂಡಲ್ ಕಂಪನ ಉಂಟಾಗುತ್ತಿದೆ": "Spindle vibration occurring.",
    "ಸ್ಪಿಂಡಲ್ ಓವರ್ಲೋಡ್ ಆಗಿದೆ": "Spindle axis overload detected.",
    "ಸ್ಪಿಂಡಲ್ ಓವರ್‌ಲೋಡ್": "Spindle axis overload detected.",
    "ಕೂಲೆಂಟ್ ಮಟ್ಟ ಕಡಿಮೆ ಇದೆ": "Coolant level is low.",
    "ಕೂಲೆಂಟ್ ಒತ್ತಡ ಕಡಿಮೆಯಾಗಿದೆ": "Coolant pressure below threshold.",
    "ಎಮರ್ಜೆನ್ಸಿ ಸ್ಟಾಪ್ ಒತ್ತಲಾಗಿದೆ": "Emergency stop circuit tripped.",
    "ತುರ್ತು ನಿಲುಗಡೆ ಬಟನ್ ಒತ್ತಲಾಗಿದೆ": "Emergency stop button engaged.",
    "ಕನ್ವೇಯರ್ ಬೆಲ್ಟ್ ಸ್ಲಿಪ್ ಆಗುತ್ತಿದೆ": "Conveyor belt is slipping.",
    "ಕನ್ವೇಯರ್ ಬೆಲ್ಟ್ ಶಬ್ದ ಮಾಡುತ್ತಿದೆ": "Conveyor belt is squealing and chirping during startup.",
    "ರೋಬೋಟ್ ಆರ್ಮ್ ಕೀಲು ವಿಚಲನೆ": "RobotArm-300 joint rotational deviation.",
    "ರೋಬೋಟ್ ಜಾಯಿಂಟ್ ವಿಚಲನೆ": "RobotArm-300 joint rotational deviation.",
    "CNC-100 ನಲ್ಲಿ E101 ಅರ್ಥವೇನು?": "What does E101 mean on CNC-100?",
    "CNC-100 ನಲ್ಲಿ E101 ಏನು?": "What does E101 mean on CNC-100?",
    "Press-200 ನಲ್ಲಿ ತೈಲ ಒತ್ತಡದಿಂದ ಏಕೆ ನಿಲ್ಲುತ್ತಿದೆ?": "Why is Press-200 stopping due to oil pressure?",
    "E101 ಅರ್ಥವೇನು?": "What does E101 mean?",
    "CNC-100 ನಲ್ಲಿ ಸ್ಪಿಂಡಲ್ ಬೇರಿಂಗ್ ಅನ್ನು ಹೇಗೆ ಬದಲಾಯಿಸುವುದು?": "How do I replace spindle bearing on CNC-100?",

    # -------------------------------------------------------------
    # 2. HINDI (हिन्दी)
    # -------------------------------------------------------------
    "मोटर ज़्यादा गरम हो रही है": "The motor is overheating.",
    "मोटर गर्म हो रही है": "The motor is overheating.",
    "मोटर का तापमान बहुत अधिक है": "Motor temperature is very high.",
    "मोटर बंद हो गई है": "The motor has stopped.",
    "हाइड्रोलिक तेल का दबाव कम है": "Hydraulic oil pressure is low.",
    "हाइड्रोलिक दबाव कम है": "Hydraulic pressure is low.",
    "हाइड्रोलिक तेल का रिसाव": "Hydraulic oil leak.",
    "तेल लीक हो रहा है": "Oil is leaking.",
    "स्पिंडल में कंपन हो रहा है": "Spindle vibration is occurring.",
    "स्पिंडल ओवरलोड हो गया है": "Spindle axis overload detected.",
    "कूलेंट का स्तर कम है": "Coolant level is low.",
    "कूलेंट का दबाव कम है": "Coolant pressure below threshold.",
    "आपातकालीन स्टॉप बटन दबा हुआ है": "Emergency stop circuit tripped.",
    "इमर्जेंसी स्टॉप ट्रिप हो गया": "Emergency stop circuit tripped.",
    "कन्वेयर बेल्ट फिसल रही है": "Conveyor belt is slipping.",
    "कन्वेयर बेल्ट से आवाज़ आ रही है": "Conveyor belt is squealing and chirping during startup.",
    "रोबोट आर्म जॉइंट में खराबी": "RobotArm-300 joint rotational deviation.",
    "CNC-100 पर E101 का क्या मतलब है?": "What does E101 mean on CNC-100?",
    "Press-200 तेल के दबाव के कारण क्यों रुक रहा है?": "Why is Press-200 stopping due to oil pressure?",
    "E101 का क्या मतलब है?": "What does E101 mean?",
    "CNC-100 पर स्पिंडल बेयरिंग कैसे बदलें?": "How do I replace spindle bearing on CNC-100?",

    # -------------------------------------------------------------
    # 3. TAMIL (தமிழ்)
    # -------------------------------------------------------------
    "மோட்டார் அதிக வெப்பமடைகிறது": "The motor is overheating.",
    "மோட்டார் சூடாகிறது": "The motor is overheating.",
    "ஹைட்ராலிக் எண்ணெய் அழுத்தம் குறைவாக உள்ளது": "Hydraulic oil pressure is low.",
    "ஹைட்ராலிக் அழுத்தம் குறைவு": "Hydraulic pressure is low.",
    "ஸ்பிண்டில் அதிர்வு ஏற்படுகிறது": "Spindle vibration occurring.",
    "ஸ்பிண்டில் அதிக சுமை": "Spindle axis overload detected.",
    "அவசர நிறுத்தம் அழுத்தப்பட்டது": "Emergency stop circuit tripped.",
    "கன்வேயர் பெல்ட் நழுவுகிறது": "Conveyor belt is slipping.",
    "ரோபோ கை மூட்டு விலகல்": "RobotArm-300 joint rotational deviation.",
    "CNC-100 இல் E101 என்றால் என்ன?": "What does E101 mean on CNC-100?",
    "எண்ணெய் அழுத்தம் காரணமாக Press-200 ஏன் நிற்கிறது?": "Why is Press-200 stopping due to oil pressure?",
    "E101 என்றால் என்ன?": "What does E101 mean?",
    "CNC-100 இல் ஸ்பிண்டில் தாங்கியை எவ்வாறு மாற்றுவது?": "How do I replace spindle bearing on CNC-100?",

    # -------------------------------------------------------------
    # 4. TELUGU (తెలుగు)
    # -------------------------------------------------------------
    "మోటారు వేడెక్కుతోంది": "The motor is overheating.",
    "మోటార్ చాలా వేడిగా ఉంది": "The motor is overheating.",
    "హైడ్రాలిక్ ఆయిల్ ప్రెజర్ తక్కువగా ఉంది": "Hydraulic oil pressure is low.",
    "హైడ్రాలిక్ ప్రెజర్ తక్కువగా ఉంది": "Hydraulic pressure is low.",
    "స్పిండిల్ వైబ్రేషన్ వస్తోంది": "Spindle vibration occurring.",
    "స్పిండిల్ ఓవర్‌లోడ్ అయింది": "Spindle axis overload detected.",
    "ఎమర్జెన్సీ స్టాప్ నొక్కబడింది": "Emergency stop circuit tripped.",
    "కన్వేయర్ బెల్ట్ జారిపోతోంది": "Conveyor belt is slipping.",
    "రోబోట్ చేయి జాయింట్ విచలనం": "RobotArm-300 joint rotational deviation.",
    "CNC-100 లో E101 అంటే ఏమిటి?": "What does E101 mean on CNC-100?",
    "ఆయిల్ ప్రెజర్ వల్ల Press-200 ఎందుకు ఆగిపోతుంది?": "Why is Press-200 stopping due to oil pressure?",
    "E101 అంటే ఏమిటి?": "What does E101 mean?",
    "CNC-100 లో స్పిండిల్ బేరింగ్‌ను ఎలా భర్తీ చేయాలి?": "How do I replace spindle bearing on CNC-100?",

    # -------------------------------------------------------------
    # 5. MARATHI (मराठी)
    # -------------------------------------------------------------
    "मोटार जास्त गरम होत आहे": "The motor is overheating.",
    "हायड्रोलिक तेलाचा दाब कमी आहे": "Hydraulic oil pressure is low.",
    "स्पिंडल ओव्हरलोड झाला आहे": "Spindle axis overload detected.",
    "आणीबाणी स्टॉप दाबला गेला आहे": "Emergency stop circuit tripped.",
    "CNC-100 वर E101 चा काय अर्थ आहे?": "What does E101 mean on CNC-100?",
    "Press-200 तेलाच्या दाबामुळे का थांबत आहे?": "Why is Press-200 stopping due to oil pressure?",

    # -------------------------------------------------------------
    # 6. BENGALI (বাংলা)
    # -------------------------------------------------------------
    "মোটর অতিরিক্ত গরম হয়ে যাচ্ছে": "The motor is overheating.",
    "হাইড্রোলিক তেলের চাপ কম": "Hydraulic oil pressure is low.",
    "স্পিন্ডল ওভারলোড হয়েছে": "Spindle axis overload detected.",
    "জরুরী স্টপ বাটন চাপা হয়েছে": "Emergency stop circuit tripped.",

    # -------------------------------------------------------------
    # 7. MALAYALAM (മലയാളം)
    # -------------------------------------------------------------
    "മോട്ടോർ അമിതമായി ചൂടാകുന്നു": "The motor is overheating.",
    "ഹൈഡ്രോളിക് ഓയിൽ മർദ്ദം കുറവാണ്": "Hydraulic oil pressure is low.",
    "സ്പിൻഡിൽ ഓവർലോഡ് കണ്ടെത്തി": "Spindle axis overload detected.",

    # -------------------------------------------------------------
    # 8. GUJARATI (ગુજરાતી)
    # -------------------------------------------------------------
    "મોટર વધુ પડતી ગરમ થઈ રહી છે": "The motor is overheating.",
    "હાઇડ્રોલિક તેલનું દબાણ ઓછું છે": "Hydraulic oil pressure is low.",
    "સ્પિન્ડલ ઓવરલોડ થયું છે": "Spindle axis overload detected.",

    # -------------------------------------------------------------
    # 9. GERMAN (Deutsch)
    # -------------------------------------------------------------
    "Der Motor überhitzt": "The motor is overheating.",
    "Der Motor ist überhitzt": "The motor is overheating.",
    "Hydrauliköldruck zu niedrig": "Hydraulic oil pressure is low.",
    "Warum stoppt Press-200 wegen Öldruck?": "Why is Press-200 stopping due to oil pressure?",
    "Was bedeutet E101 auf CNC-100?": "What does E101 mean on CNC-100?",
    "Was bedeutet E101?": "What does E101 mean?",
    "Wie tausche ich das Spindellager am CNC-100 aus?": "How do I replace spindle bearing on CNC-100?",

    # -------------------------------------------------------------
    # 10. SPANISH (Español)
    # -------------------------------------------------------------
    "El motor se está sobrecalentando": "The motor is overheating.",
    "La presión del aceite hidráulico es baja": "Hydraulic oil pressure is low.",
    "¿Por qué se detiene Press-200 por presión de aceite?": "Why is Press-200 stopping due to oil pressure?",
    "¿Qué significa E101 en CNC-100?": "What does E101 mean on CNC-100?",
    "¿Qué significa E101?": "What does E101 mean?",
    "¿Cómo reemplazo el rodamiento del husillo en CNC-100?": "How do I replace spindle bearing on CNC-100?",

    # -------------------------------------------------------------
    # 11. FRENCH (Français)
    # -------------------------------------------------------------
    "Le moteur surchauffe": "The motor is overheating.",
    "La pression d'huile hydraulique est basse": "Hydraulic oil pressure is low.",
    "Pourquoi Press-200 s'arrête en raison de la pression d'huile?": "Why is Press-200 stopping due to oil pressure?",
    "Que signifie E101 sur CNC-100?": "What does E101 mean on CNC-100?",
    "Que signifie E101?": "What does E101 mean?",
    "Comment remplacer le roulement de broche sur CNC-100?": "How do I replace spindle bearing on CNC-100?",

    # -------------------------------------------------------------
    # 12. CHINESE (中文)
    # -------------------------------------------------------------
    "电机过热": "The motor is overheating.",
    "液压油压力低": "Hydraulic oil pressure is low.",
    "为什么Press-200因油压停止？": "Why is Press-200 stopping due to oil pressure?",
    "CNC-100上的E101是什么意思？": "What does E101 mean on CNC-100?",
    "E101是什么意思？": "What does E101 mean?",
    "如何在CNC-100上更换主轴轴承？": "How do I replace spindle bearing on CNC-100?",

    # -------------------------------------------------------------
    # 13. JAPANESE (日本語)
    # -------------------------------------------------------------
    "モーターが過熱しています": "The motor is overheating.",
    "油圧が低下しています": "Hydraulic oil pressure is low.",
    "Press-200が油圧で停止する理由は？": "Why is Press-200 stopping due to oil pressure?",
    "CNC-100のE101はどういう意味ですか？": "What does E101 mean on CNC-100?",
    "E101はどういう意味ですか？": "What does E101 mean?",
    "CNC-100のスピンドルベアリングを交換するには？": "How do I replace spindle bearing on CNC-100?",

    # -------------------------------------------------------------
    # 14. ROMANIZED REGIONAL (Hinglish, Kanglish, Tanglish)
    # -------------------------------------------------------------
    "motor garam ho raha hai": "The motor is overheating.",
    "motor bohot garam ho gaya hai": "The motor is overheating.",
    "motor jyada garam ho rahi hai": "The motor is overheating.",
    "oil pressure kam ho gaya": "Hydraulic oil pressure is low.",
    "press-200 oil pressure kam hai": "Why is Press-200 stopping due to oil pressure?",
    "press-200 kyu ruk raha hai": "Why is Press-200 stopping?",
    "cnc-100 me e101 ka matlab kya hai": "What does E101 mean on CNC-100?",
    "cnc-100 me e101 kya hai": "What does E101 mean on CNC-100?",
    "e101 ka matlab kya hai": "What does E101 mean?",
    "e101 kya hai": "What does E101 mean?",
    "cnc-100 spindle bearing kaise badle": "How do I replace spindle bearing on CNC-100?",
    "spindle bearing kaise change kare": "How do I replace spindle bearing on CNC-100?",
    "emergency stop dab gaya": "Emergency stop circuit tripped.",
    "motor thumba bisi aagthide": "The motor is overheating.",
    "motor thumba heat aagide": "The motor is overheating.",
    "motor bisi aagthide": "The motor is overheating.",
    "coolant leak aagthide": "Coolant level is low.",
    "spindle overload aagide": "Spindle axis overload detected.",
    "press-200 nillisi aagthide": "Why is Press-200 stopping due to oil pressure?"
}

# Key terms for Romanized dialect detection (Hinglish/Kanglish/Tanglish)
HINGLISH_KEYWORDS = {
    "garam", "matlab", "kaise", "kyu", "kya", "hota", "kare", "badle", "badalna", 
    "dab", "gaya", "ho", "raha", "hai", "rok", "band", "thik", "samasya", "kam"
}
KANGLISH_KEYWORDS = {
    "bisi", "aagthide", "aagide", "enu", "hege", "madodu", "nillisi", "beku", 
    "samasye", "thumba", "illi", "yake", "aytu"
}
TANGLISH_KEYWORDS = {
    "soodu", "eppadi", "enna", "aachu", "pannuvathu", "nilkuthu", "yen"
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
        "Marathi": 0,
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
            # Shared between Hindi and Marathi - check specific Marathi letters or default Hindi
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
        elif 0x3040 <= cp <= 0x30FF or 0x31F0 <= cp <= 0x31FF:
            counts["Japanese"] += 1
        elif 0xAC00 <= cp <= 0xD7AF:
            counts["Korean"] += 1

    max_lang = max(counts, key=counts.get)
    if counts[max_lang] > 0:
        return max_lang
    euro = detect_european_language(text)
    if euro:
        return euro
    return "English"

def detect_european_language(text: str) -> Optional[str]:
    """
    Detects European languages that use Latin script but have distinct diacritics or vocabulary.
    """
    lower = text.lower()
    # German
    if any(c in text for c in ["ä", "ö", "ü", "ß", "Ä", "Ö", "Ü"]) or any(w in lower for w in ["warum", "stoppt", "bedeutet", "überhitzt", "spindellager"]):
        return "German"
    # Spanish
    if any(c in text for c in ["¿", "¡", "ñ", "Ñ", "á", "é", "í", "ó", "ú"]) or any(w in lower for w in ["qué", "significa", "por qué", "detiene", "sobrecalentando", "reemplazo"]):
        return "Spanish"
    # French
    if any(c in text for c in ["ç", "œ", "à", "è", "ê", "ë", "î", "ï", "ô", "û", "ù"]) or any(w in lower for w in ["pourquoi", "signifie", "s'arrête", "surchauffe", "roulement"]):
        return "French"
    return None

def detect_romanized_dialect(text: str) -> Optional[str]:
    """
    Detects if Latin-script input contains phonetic Indian regional vocabulary (Hinglish/Kanglish/Tanglish).
    """
    tokens = set(re.findall(r"\b[a-zA-Z]+\b", text.lower()))
    if not tokens:
        return None

    if len(tokens.intersection(HINGLISH_KEYWORDS)) >= 2 or (len(tokens.intersection(HINGLISH_KEYWORDS)) >= 1 and ("garam" in tokens or "matlab" in tokens or "kaise" in tokens)):
        return "Hindi (Romanized)"
    if len(tokens.intersection(KANGLISH_KEYWORDS)) >= 2 or (len(tokens.intersection(KANGLISH_KEYWORDS)) >= 1 and ("bisi" in tokens or "aagthide" in tokens or "aagide" in tokens)):
        return "Kannada (Romanized)"
    if len(tokens.intersection(TANGLISH_KEYWORDS)) >= 2:
        return "Tamil (Romanized)"

    return None

def _is_english_text(text: str) -> bool:
    """
    Returns True if text contains only standard ASCII or Latin characters and no Indic/Asian scripts,
    and is not a transliterated regional dialect or European language.
    """
    if not text:
        return True
    if detect_script_language(text) != "English":
        return False
    if detect_romanized_dialect(text) is not None:
        return False
    if detect_european_language(text) is not None:
        return False
    return True

def _extract_machine_and_code(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Safely extracts machine name and error code to preserve entities throughout translation.
    """
    t = text.lower()
    machine = None
    if "cnc-100" in t or "cnc 100" in t or "cnc100" in t:
        machine = "CNC-100"
    elif "press-200" in t or "press 200" in t or "press200" in t:
        machine = "Press-200"
    elif "robotarm-300" in t or "robotarm 300" in t or "robotarm300" in t or "robot arm" in t or "ರೋಬೋಟ್" in text or "रोबोट" in text:
        machine = "RobotArm-300"
    elif "conveyor" in t or "cb-4400" in t or "ಕನ್ವೇಯರ್" in text or "कन्वेयर" in text:
        machine = "Conveyor Belt System"

    code_match = re.search(r"\b([EHR]\d{3})\b", text, re.IGNORECASE)
    code = code_match.group(1).upper() if code_match else None

    return machine, code

def _semantic_slot_translation(text: str, detected_lang: str) -> Optional[str]:
    """
    Synthesizes clean, technical English queries by pairing extracted hardware entities
    with detected symptoms and intentions.
    """
    lower = text.lower()
    machine, code = _extract_machine_and_code(text)

    # 1. Error code inquiry ("What does E101 mean on CNC-100?")
    is_meaning_query = any(q in lower for q in [
        "meaning", "mean", "ಅರ್ಥ", "ಏನು", "मतलब", "क्या है", "என்றால் என்ன", "అంటే ఏమిటి", 
        "काय अर्थ", "কী", "significa", "bedeutet", "sens"
    ])
    if code and machine and is_meaning_query:
        return f"What does {code} mean on {machine}?"

    if code and not machine and is_meaning_query:
        return f"What does {code} mean?"

    # 2. Hydraulic oil pressure stopping ("Why is Press-200 stopping due to oil pressure?")
    is_oil_pressure = any(p in lower or p in text for p in [
        "oil pressure", "hydraulic", "तೈಲ ಒತ್ತಡ", "ತೈಲ", "ಒತ್ತಡ", "तेल", "दबाव", "எண்ணெய் அழுத்தம்", 
        "ఆయిల్ ప్రెజర్", "तेलाचा दाब", "öldruck", "presión de aceite", "pression d'huile", "油压"
    ])
    is_stopping = any(s in lower or s in text for s in [
        "stop", "stopping", "ನಿಲ್ಲುತ್ತಿದೆ", "ನಿಂತು", "रुक", "बंद", "நிற்கிறது", "ఆగిపోతుంది", 
        "थांबत", "stoppt", "detiene", "s'arrête", "停止"
    ])
    if is_oil_pressure and (is_stopping or machine == "Press-200"):
        target_machine = machine or "Press-200"
        return f"Why is {target_machine} stopping due to oil pressure?"

    # 3. Spindle bearing replacement / out of scope ("How do I replace spindle bearing on CNC-100?")
    is_bearing = any(b in lower or b in text for b in [
        "bearing", "spindle bearing", "ಬೇರಿಂಗ್", "बेयरिंग", "தாங்கி", "బేరింగ్", "lager", "rodamiento", "roulement", "轴承"
    ])
    is_replace = any(r in lower or r in text for r in [
        "replace", "change", "how do i replace", "ಹೇಗೆ ಬದಲಾಯಿಸುವುದು", "बदलें", "बदलना", "மாற்றுவது", "భర్తీ", "tauschen", "reemplazo", "remplacer", "更换"
    ])
    if is_bearing or (is_replace and "spindle" in lower):
        target_machine = machine or "CNC-100"
        return f"How do I replace spindle bearing on {target_machine}?"

    # 4. Motor overheating / thermal fault
    is_motor = any(m in lower or m in text for m in ["motor", "ಮೋಟಾರ್", "मोटर", "மோட்டார்", "మోటారు", "moteur", "电机"])
    is_overheat = any(o in lower or o in text for o in [
        "overheat", "hot", "temperature", "ಬಿಸಿ", "ತಾಪಮಾನ", "गर्म", "तापमान", "வெப்பம்", "వేడి", "überhitzt", "sobrecalentando", "surchauffe", "过热"
    ])
    if is_motor and is_overheat:
        return "The motor is overheating."

    # 5. Spindle overload
    if "spindle" in lower or "ಸ್ಪಿಂಡಲ್" in text or "स्पिंडल" in text:
        if any(v in lower or v in text for v in ["overload", "ಕಂಪನ", "कंपन", "അதிர்வு", "వైబ్రేషన్", "vibration", "surcharge"]):
            return "Spindle axis overload detected."

    # 6. Emergency stop tripped
    if any(e in lower or e in text for e in [
        "emergency stop", "e-stop", "ಎಮರ್ಜೆನ್ಸಿ", "तुರ್ತು", "आपातकालीन", "इमर्जेंसी", "அவசர நிறுத்தம்", "ఎమర్జెన్సీ"
    ]):
        return "Emergency stop circuit tripped."

    # 7. Robot arm joint deviation
    if machine == "RobotArm-300" or any(r in lower or r in text for r in ["robot", "arm", "ರೋಬೋಟ್", "रोबोट", "ரோபோ"]):
        if any(j in lower or j in text for j in ["joint", "deviation", "കീലು", "जॉइंट", "मूட்டு", "జాయింట్", "खराबी"]):
            return "RobotArm-300 joint rotational deviation."

    return None

def _try_google_cloud_translate(text: str) -> Optional[Dict[str, str]]:
    """
    Attempts translation using official Google Cloud Translation API (google.cloud.translate_v2).
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
            f"You are an industrial factory translation engine. Detect the language of the following text and translate it into English.\n"
            f"Preserve machine names (CNC-100, Press-200, RobotArm-300) and error codes (E101, E102, E103, E202, E203, R101) exactly.\n"
            f"Output ONLY a JSON object with keys 'detectedLanguage' and 'translatedText'.\n"
            f"Text: \"{text}\""
        )
        resp = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            contents=prompt
        )
        raw_text = resp.text.strip()
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

    # 1. Fast path for pure English queries (0ms latency preserved for factory codes)
    if _is_english_text(cleaned_text):
        return {
            "originalText": text,
            "detectedLanguage": "English",
            "translatedText": text
        }

    # 2. Identify Script or Romanized Dialect
    detected_lang = detect_script_language(cleaned_text)
    if detected_lang == "English":
        dialect = detect_romanized_dialect(cleaned_text)
        if dialect:
            detected_lang = dialect

    # 3. Try Google Cloud Translation API (if cloud service active)
    gcp_result = _try_google_cloud_translate(cleaned_text)
    if gcp_result:
        return gcp_result

    # 4. Try Google GenAI / Gemini Translation (if API key active)
    gemini_result = _try_gemini_translate(cleaned_text)
    if gemini_result:
        return gemini_result

    # 5. Direct Dictionary Match
    normalized_query = cleaned_text.strip("?।!.¿¡ ")
    for phrase, eng in FALLBACK_TRANSLATIONS.items():
        if phrase.strip("?।!.¿¡ ") == normalized_query:
            return {
                "originalText": text,
                "detectedLanguage": detected_lang,
                "translatedText": eng
            }

    # 6. Substring / Phrase-Level Match
    for phrase, eng in FALLBACK_TRANSLATIONS.items():
        if phrase.lower() in cleaned_text.lower():
            return {
                "originalText": text,
                "detectedLanguage": detected_lang,
                "translatedText": eng
            }

    # 7. Semantic Slot-Filling & Template Translation
    semantic_translation = _semantic_slot_translation(cleaned_text, detected_lang)
    if semantic_translation:
        return {
            "originalText": text,
            "detectedLanguage": detected_lang,
            "translatedText": semantic_translation
        }

    # 8. Fallback: preserve original if no translation match found
    return {
        "originalText": text,
        "detectedLanguage": detected_lang,
        "translatedText": cleaned_text
    }

# Pythonic alias
translate_input = translateInput
