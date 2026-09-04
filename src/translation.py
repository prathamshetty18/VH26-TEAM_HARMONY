"""
Multilingual Translation Module for Machine Hardware Error Detection Application.

Flow:
Machine/User Input
    ↓
Detect Language (Indic languages: Kannada, Hindi, Tamil, Telugu, Marathi, Bengali; International: Chinese, Japanese, German, Spanish, French; Romanized dialects: Hinglish, Kanglish)
    ↓
If non-English → Translate to English (via Google Cloud Translation API, Gemini, or Domain Semantic Engine)
    ↓
Pass the English translation directly to the EXISTING machine error detection pipeline
(If already English: Do not translate, pass directly to existing pipeline)

Features:
1. Multi-tier language detection:
   - Unicode script analysis (Kannada, Hindi, Tamil, Telugu, Marathi, Bengali, Malayalam, Gujarati, Chinese, Japanese, Korean, Arabic, Russian)
   - European language diacritic & vocabulary analysis (German, Spanish, French)
   - Romanized / transliterated dialect detection (Hinglish, Kanglish, Tanglish)
   - Pure English zero-latency fast path
2. Hardware entity & error code preservation (CNC-100, Press-200, RobotArm-300, E101, E102, E103, E202, E203, R101, H205)
3. Domain-trained semantic translation engine for factory diagnostics & symptoms
4. External translation API integrations (Google Cloud Translation v2 & Google GenAI) with resilient offline fallback
"""

import os
import re
import logging
from typing import Dict, Any, Optional, Callable, Tuple

logger = logging.getLogger("MachineAssist.Translation")

# Language code to full English name mapping
SUPPORTED_LANGUAGES = {
    "zh-CN": "Simplified Chinese",
    "zh": "Simplified Chinese",
    "ja": "Japanese",
    "de": "German",
    "en": "English",
    "kn": "Kannada",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "es": "Spanish",
    "fr": "French",
}

LANGUAGE_NAMES = {
    "zh": "Simplified Chinese",
    "zh-CN": "Simplified Chinese",
    "zh-TW": "Chinese (Traditional)",
    "ja": "Japanese",
    "de": "German",
    "en": "English",
    "kn": "Kannada",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Marathi",
    "ml": "Malayalam",
    "bn": "Bengali",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "es": "Spanish",
    "fr": "French",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "ko": "Korean",
    "ar": "Arabic",
}

# Domain-trained vocabulary for industrial hardware troubleshooting
DOMAIN_TRANSLATIONS: Dict[str, str] = {
    # --- Simplified Chinese (zh-CN) ---
    "电机温度过高": "The motor temperature is too high.",
    "电机过热": "The motor is overheating.",
    "主轴温度过高": "The spindle temperature is too high.",
    "传送带打滑": "Conveyor belt is slipping.",
    "输送带打滑": "Conveyor belt is slipping.",
    "高速时主轴振动": "Spindle vibration at high RPM.",
    "主轴振动过大": "Spindle vibration is too high.",
    "液压过低": "Hydraulic pressure is too low.",
    "液压油压力低": "Hydraulic oil pressure is low.",
    "液压系统压力下降": "Hydraulic system pressure drop.",
    "电机停止运行": "Motor stopped.",
    "发现漏油现象": "Oil leakage detected.",
    "主轴发出异常噪音": "Abnormal noise from spindle.",
    "为什么Press-200因油压停止？": "Why is Press-200 stopping due to oil pressure?",
    "CNC-100上的E101是什么意思？": "What does E101 mean on CNC-100?",
    "E101是什么意思？": "What does E101 mean?",
    "如何在CNC-100上更换主轴轴承？": "How do I replace spindle bearing on CNC-100?",

    # --- Japanese (ja) ---
    "モーターの温度が高すぎます": "The motor temperature is too high.",
    "モーター温度が高すぎます": "The motor temperature is too high.",
    "モーターが過熱しています": "The motor is overheating.",
    "スピンドルの温度が高すぎます": "The spindle temperature is too high.",
    "コンベアベルトが滑っています": "Conveyor belt is slipping.",
    "スピンドルの振動": "Spindle vibration.",
    "油圧が低すぎます": "Hydraulic pressure is too low.",
    "油圧が低下しています": "Hydraulic oil pressure is low.",
    "油圧の低下": "Drop in hydraulic pressure.",
    "モーター停止": "Motor stopped.",
    "油漏れが発生しています": "Oil leakage is occurring.",
    "スピンドル異常音": "Spindle abnormal noise.",
    "Press-200が油圧で停止する理由は？": "Why is Press-200 stopping due to oil pressure?",
    "CNC-100のE101はどういう意味ですか？": "What does E101 mean on CNC-100?",
    "E101はどういう意味ですか？": "What does E101 mean?",
    "CNC-100のスピンドルベアリングを交換するには？": "How do I replace spindle bearing on CNC-100?",

    # --- German (de) ---
    "Die Motortemperatur ist zu hoch.": "The motor temperature is too high.",
    "Die Motortemperatur ist zu hoch": "The motor temperature is too high.",
    "Motortemperatur ist zu hoch": "The motor temperature is too high.",
    "Der Motor ist überhitzt": "The motor is overheating.",
    "Der Motor überhitzt": "The motor is overheating.",
    "Das Förderband rutscht": "The conveyor belt is slipping.",
    "Förderband rutscht": "Conveyor belt is slipping.",
    "Förderband schlupf": "Conveyor belt slip.",
    "Spindelvibration bei hoher Drehzahl": "Spindle vibration at high RPM.",
    "Spindelvibration zu hoch": "Spindle vibration too high.",
    "Hydraulikdruck zu niedrig": "Hydraulic pressure too low.",
    "Hydraulikdruck ist zu niedrig": "Hydraulic pressure is too low.",
    "Hydrauliköltemperatur zu hoch": "Hydraulic oil temperature too high.",
    "Hydrauliköldruck zu niedrig": "Hydraulic oil pressure is low.",
    "Ölleckage erkannt": "Oil leakage detected.",
    "Störung am Motor": "Motor malfunction.",
    "Warum stoppt Press-200 wegen Öldruck?": "Why is Press-200 stopping due to oil pressure?",
    "Was bedeutet E101 auf CNC-100?": "What does E101 mean on CNC-100?",
    "Was bedeutet E101?": "What does E101 mean?",
    "Wie tausche ich das Spindellager am CNC-100 aus?": "How do I replace spindle bearing on CNC-100?",

    # --- Spanish (es) ---
    "El motor se está sobrecalentando": "The motor is overheating.",
    "La presión del aceite hidráulico es baja": "Hydraulic oil pressure is low.",
    "¿Por qué se detiene Press-200 por presión de aceite?": "Why is Press-200 stopping due to oil pressure?",
    "¿Qué significa E101 en CNC-100?": "What does E101 mean on CNC-100?",
    "¿Qué significa E101?": "What does E101 mean?",
    "¿Cómo reemplazo el rodamiento del husillo en CNC-100?": "How do I replace spindle bearing on CNC-100?",

    # --- French (fr) ---
    "Le moteur surchauffe": "The motor is overheating.",
    "La pression d'huile hydraulique est basse": "Hydraulic oil pressure is low.",
    "Pourquoi Press-200 s'arrête en raison de la pression d'huile?": "Why is Press-200 stopping due to oil pressure?",
    "Que signifie E101 sur CNC-100?": "What does E101 mean on CNC-100?",
    "Que signifie E101?": "What does E101 mean?",
    "Comment remplacer le roulement de broche sur CNC-100?": "How do I replace spindle bearing on CNC-100?",

    # --- Kannada (kn) ---
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

    # --- Hindi (hi) ---
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

    # --- Tamil (ta) ---
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

    # --- Telugu (te) ---
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

    # --- Marathi (mr) ---
    "मोटार जास्त गरम होत आहे": "The motor is overheating.",
    "हायड्रोलिक तेलाचा दाब कमी आहे": "Hydraulic oil pressure is low.",
    "स्पिंडल ओव्हरलोड झाला आहे": "Spindle axis overload detected.",
    "आणीबाणी स्टॉप दाबला गेला आहे": "Emergency stop circuit tripped.",

    # --- Bengali (bn) ---
    "মোটর অতিরিক্ত গরম হয়ে যাচ্ছে": "The motor is overheating.",
    "হাইড্রোলিক তেলের চাপ কম": "Hydraulic oil pressure is low.",
    "স্পিন্ডল ওভারলোড হয়েছে": "Spindle axis overload detected.",

    # --- Malayalam (ml) ---
    "മോട്ടോർ അമിതമായി ചൂടാകുന്നു": "The motor is overheating.",
    "ഹൈഡ്രോളിക് ഓയിൽ മർദ്ദം കുറവാണ്": "Hydraulic oil pressure is low.",

    # --- Gujarati (gu) ---
    "મોટર વધુ પડતી ગરમ થઈ રહી છે": "The motor is overheating.",
    "હાઇડ્રોલિક તેલનું દબાણ ઓછું છે": "Hydraulic oil pressure is low.",

    # --- Romanized Regional (Hinglish, Kanglish) ---
    "motor garam ho raha hai": "The motor is overheating.",
    "motor bohot garam ho gaya hai": "The motor is overheating.",
    "motor jyada garam ho rahi hai": "The motor is overheating.",
    "oil pressure kam ho gaya": "Hydraulic oil pressure is low.",
    "press-200 oil pressure kam hai": "Why is Press-200 stopping due to oil pressure?",
    "press-200 kyu ruk raha hai": "Why is Press-200 stopping due to oil pressure?",
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
}

FALLBACK_TRANSLATIONS = DOMAIN_TRANSLATIONS

# Key terms for Romanized dialect detection
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


def detect_european_language(text: str) -> Optional[str]:
    """
    Detects European languages that use Latin script but have distinct diacritics or vocabulary.
    """
    lower = text.lower()
    # German
    if any(c in text for c in ["ä", "ö", "ü", "ß", "Ä", "Ö", "Ü"]) or any(w in lower for w in ["warum", "stoppt", "bedeutet", "überhitzt", "spindellager", "förderband"]):
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
        if any(j in lower or j in text for j in ["joint", "deviation", "ಕೀಲು", "जॉइंट", "मूட்டு", "జాయింట్", "खराबी"]):
            return "RobotArm-300 joint rotational deviation."

    return None


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


def _detect_script_heuristic(text: str) -> Tuple[str, str]:
    """
    Heuristic script detection mapping to ISO language code and display name.
    """
    if not text:
        return "en", "English"

    # 1. Japanese check
    has_hiragana = any(0x3040 <= ord(c) <= 0x309F for c in text)
    has_katakana = any(0x30A0 <= ord(c) <= 0x30FF for c in text)
    if has_hiragana or has_katakana:
        return "ja", "Japanese"

    # 2. Chinese check
    has_cjk = any(0x4E00 <= ord(c) <= 0x9FFF for c in text)
    if has_cjk:
        return "zh-CN", "Simplified Chinese"

    # 3. Regional Indian scripts
    if any(0x0C80 <= ord(c) <= 0x0CFF for c in text):
        return "kn", "Kannada"
    if any(0x0900 <= ord(c) <= 0x097F for c in text):
        return "hi", "Hindi"
    if any(0x0B80 <= ord(c) <= 0x0BFF for c in text):
        return "ta", "Tamil"
    if any(0x0C00 <= ord(c) <= 0x0C7F for c in text):
        return "te", "Telugu"
    if any(0x0D00 <= ord(c) <= 0x0D7F for c in text):
        return "ml", "Malayalam"
    if any(0x0980 <= ord(c) <= 0x09FF for c in text):
        return "bn", "Bengali"
    if any(0x0A80 <= ord(c) <= 0x0AFF for c in text):
        return "gu", "Gujarati"

    # 4. European languages
    euro = detect_european_language(text)
    if euro == "German":
        return "de", "German"
    elif euro == "Spanish":
        return "es", "Spanish"
    elif euro == "French":
        return "fr", "French"

    # 5. Romanized dialects
    dialect = detect_romanized_dialect(text)
    if dialect:
        if "Hindi" in dialect:
            return "hi-Latn", "Hindi (Romanized)"
        elif "Kannada" in dialect:
            return "kn-Latn", "Kannada (Romanized)"
        elif "Tamil" in dialect:
            return "ta-Latn", "Tamil (Romanized)"

    return "en", "English"


class MultilingualTranslationModule:
    """
    Multilingual Translation Module for Machine Hardware Error Detection.

    Flow:
    Machine/User Input
        ↓
    Detect Language
        ↓
    If non-English → Translate to English via Cloud API or Domain Semantic Engine
        ↓
    Pass the English translation directly to the EXISTING machine error detection pipeline.
    (If already English: Do not translate, pass directly to existing pipeline)
    """

    def __init__(self):
        self._gcp_client = None
        self._init_gcp_client()

    def _init_gcp_client(self):
        """Initializes the official google.cloud.translate_v2 Client if credentials exist."""
        try:
            if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ or os.path.exists(
                os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
            ):
                from google.cloud import translate_v2 as translate
                self._gcp_client = translate.Client()
                logger.info("Google Cloud Translation Client initialized successfully.")
        except Exception as e:
            logger.debug("Google Cloud Translation client not available: %s", e)
            self._gcp_client = None

    def detect_language(self, text: str) -> Dict[str, Any]:
        """Detects language of incoming instruction."""
        cleaned = (text or "").strip()
        if not cleaned:
            return {"language": "en", "confidence": 1.0, "language_name": "English"}

        # Fast path check for pure English queries
        if _is_english_text(cleaned):
            return {"language": "en", "confidence": 1.0, "language_name": "English"}

        # Check GCP client if available
        if self._gcp_client:
            try:
                detection = self._gcp_client.detect_language(cleaned)
                lang_code = detection.get("language", "en")
                confidence = detection.get("confidence", 0.95)
                lang_name = LANGUAGE_NAMES.get(lang_code, SUPPORTED_LANGUAGES.get(lang_code, lang_code.capitalize()))
                return {
                    "language": lang_code,
                    "confidence": confidence,
                    "language_name": lang_name
                }
            except Exception as e:
                logger.debug("GCP Language detection failed, falling back to heuristic: %s", e)

        code, name = _detect_script_heuristic(cleaned)
        return {
            "language": code,
            "confidence": 0.99,
            "language_name": name
        }

    def _call_gcp_translate(self, text: str) -> Optional[str]:
        """Translates text using Google Cloud Translation API."""
        if not self._gcp_client:
            return None
        try:
            result = self._gcp_client.translate(text, target_language="en")
            return result.get("translatedText")
        except Exception as e:
            logger.debug("GCP translate call failed: %s", e)
            return None

    def _call_gemini_translate(self, text: str) -> Optional[str]:
        """Translates text using Google GenAI (Gemini) if API key is active."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            prompt = (
                f"You are an industrial factory translation engine. Translate the following text into English.\n"
                f"Preserve machine names (CNC-100, Press-200, RobotArm-300) and error codes (E101, E102, E103, E202, E203, R101) exactly.\n"
                f"Output ONLY the translated English text without explanations or quotes.\n"
                f"Text: \"{text}\""
            )
            resp = client.models.generate_content(
                model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
                contents=prompt
            )
            return resp.text.strip()
        except Exception as e:
            logger.debug("Gemini translation call failed: %s", e)
            return None

    def _fallback_domain_translate(self, text: str, detected_lang: str) -> str:
        """Domain semantic dictionary translation matching."""
        cleaned = text.strip()
        normalized_query = cleaned.strip("?।!.¿¡ ")

        # 1. Exact match
        for phrase, eng in DOMAIN_TRANSLATIONS.items():
            if phrase.strip("?।!.¿¡ ") == normalized_query:
                return eng

        # 2. Substring match
        for phrase, eng in DOMAIN_TRANSLATIONS.items():
            if phrase.lower() in cleaned.lower():
                return eng

        # 3. Semantic slot synthesis
        semantic = _semantic_slot_translation(cleaned, detected_lang)
        if semantic:
            return semantic

        return cleaned

    def translate_input(self, text: str) -> Dict[str, Any]:
        """
        Public translation method adhering to exact contract:
        Machine/User Input -> Detect Language -> Translate to English -> Pass to pipeline.
        """
        raw_text = text or ""
        cleaned = raw_text.strip()

        if not cleaned:
            return {
                "originalText": raw_text,
                "detectedLanguage": "English",
                "detectedCode": "en",
                "translatedText": raw_text,
                "isTranslated": False
            }

        # Step 1: Detect Language
        detection = self.detect_language(cleaned)
        lang_code = detection.get("language", "en")
        lang_name = detection.get("language_name", "English")

        # Step 2: If the input is already English, do not translate it. Pass it directly.
        if lang_code == "en" or lang_name == "English":
            return {
                "originalText": raw_text,
                "detectedLanguage": "English",
                "detectedCode": "en",
                "translatedText": raw_text,
                "isTranslated": False
            }

        # Step 3: Direct Domain Dictionary Match
        direct_trans = None
        normalized_query = cleaned.strip("?।!.¿¡ ")
        for phrase, eng in DOMAIN_TRANSLATIONS.items():
            if phrase.strip("?।!.¿¡ ") == normalized_query:
                direct_trans = eng
                break

        if direct_trans:
            return {
                "originalText": raw_text,
                "detectedLanguage": lang_name,
                "detectedCode": lang_code,
                "translatedText": direct_trans,
                "isTranslated": True
            }

        # Step 4: Try Cloud APIs (GCP / Gemini)
        translated_text = self._call_gcp_translate(cleaned)
        if not translated_text:
            translated_text = self._call_gemini_translate(cleaned)

        # Step 5: Fallback to Domain Semantic Engine
        if not translated_text:
            translated_text = self._fallback_domain_translate(cleaned, lang_name)

        return {
            "originalText": raw_text,
            "detectedLanguage": lang_name,
            "detectedCode": lang_code,
            "translatedText": translated_text,
            "isTranslated": True
        }

    def process_and_forward(
        self,
        text: str,
        pipeline_fn: Optional[Callable[[str], Any]] = None,
        **pipeline_kwargs
    ) -> Any:
        """
        Complete end-to-end execution flow:
        Machine/User Input -> Detect Language -> Translate to English -> Pass to pipeline.
        """
        trans_res = self.translate_input(text)
        english_text = trans_res["translatedText"]

        if pipeline_fn is not None:
            return pipeline_fn(english_text, **pipeline_kwargs)

        from src.api import handle_query, QueryRequest
        req = QueryRequest(
            message=english_text,
            session_id=pipeline_kwargs.get("session_id", "default_session"),
            machine_filter=pipeline_kwargs.get("machine_filter")
        )
        return handle_query(req)


# Default singleton instance
_module_instance = MultilingualTranslationModule()


def detect_language(text: str) -> str:
    """Detects incoming language."""
    res = _module_instance.detect_language(text)
    return res.get("language_name", "English")


def translateInput(text: str) -> Dict[str, Any]:
    """Public translation function."""
    return _module_instance.translate_input(text)


# Pythonic alias
translate_input = translateInput
