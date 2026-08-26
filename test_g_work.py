from google import genai
from config import config

client = genai.Client(api_key=config.GEMINI_API_KEY)
models = ["gemini-3.5-flash", "gemini-flash-latest", "gemini-3.6-flash", "gemini-2.5-flash"]
for m in models:
    try:
        res = client.models.generate_content(model=m, contents="Say TEST")
        print(f"✅ WORKING MODEL: {m} -> {res.text.strip()}")
    except Exception as e:
        print(f"❌ FAILED: {m} -> {e}")
