import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

m_name = "gemini-" + "3" + ".6-" + "flash"
try:
    res = client.models.generate_content(
        model=m_name,
        contents="Say hello in one word"
    )
    print(f"Success with {m_name}:", res.text)
except Exception as e:
    print(f"Error with {m_name}:", e)
