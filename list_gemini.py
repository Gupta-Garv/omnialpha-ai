from google import genai
from config import config

client = genai.Client(api_key=config.GEMINI_API_KEY)
for m in client.models.list():
    if "generateContent" in m.supported_actions:
        print("AVAILABLE GEMINI MODEL:", m.name)
