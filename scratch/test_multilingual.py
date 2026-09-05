import sys
import requests

sys.stdout.reconfigure(encoding='utf-8')

test_cases = [
    {
        'lang': 'Chinese (Simplified)',
        'input': '电机温度过高',
        'expected_lang': 'Simplified Chinese',
        'expected_trans': 'The motor temperature is too high.'
    },
    {
        'lang': 'Japanese',
        'input': 'モーターの温度が高すぎます',
        'expected_lang': 'Japanese',
        'expected_trans': 'The motor temperature is too high.'
    },
    {
        'lang': 'German',
        'input': 'Die Motortemperatur ist zu hoch.',
        'expected_lang': 'German',
        'expected_trans': 'The motor temperature is too high.'
    },
    {
        'lang': 'English',
        'input': 'The motor temperature is too high.',
        'expected_lang': 'English',
        'expected_trans': 'The motor temperature is too high.'
    }
]

if __name__ == '__main__':
    for tc in test_cases:
        # 1. Test /translate
        t_res = requests.post('http://127.0.0.1:8000/translate', json={'text': tc['input']}).json()
        print(f"[{tc['lang']}] /translate ->", t_res)
        assert t_res['detectedLanguage'] == tc['expected_lang'], f"Expected {tc['expected_lang']}, got {t_res['detectedLanguage']}"
        assert 'motor temperature' in t_res['translatedText'].lower(), f"Expected motor temperature in {t_res['translatedText']}"

        # 2. Test /query (should pass directly to existing pipeline)
        q_res = requests.post('http://127.0.0.1:8000/query', json={'message': tc['input']}).json()
        sources = [s['section'] for s in q_res.get('sources', [])]
        print(f"[{tc['lang']}] /query -> retrieved: {sources[:2]}")
        assert len(sources) > 0, f"Expected sources for {tc['lang']}"

    print('\nSUCCESS: ALL 4 LANGUAGES (Chinese, Japanese, German, English) PASS VERIFICATION!')

