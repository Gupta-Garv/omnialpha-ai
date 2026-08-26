import os
from openai import OpenAI
from google import genai
from config import config

nv_keys = [
    "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",
    "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",
    "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"
]

print("--- TESTING NVIDIA NIM MODELS ---")
models_to_test = [
    "deepseek-ai/deepseek-v4-flash-0731",
    "deepseek-ai/deepseek-r1",
    "meta/llama-3.3-70b-instruct",
    "nvidia/llama-3.1-nemotron-70b-instruct",
    "mistralai/mistral-large-2-instruct",
    "qwen/qwen2.5-72b-instruct"
]

for key in nv_keys:
    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=key)
    for m in models_to_test:
        try:
            res = client.chat.completions.create(
                model=m,
                messages=[{"role":"user","content":"Say HELLO"}],
                max_tokens=10
            )
            print(f"✅ SUCCESS NV ({m}) on key {key[:12]}... -> {res.choices[0].message.content.strip()}")
            break
        except Exception as e:
            print(f"❌ FAIL NV ({m}) -> {str(e)[:80]}")

print("\n--- TESTING GEMINI MODELS ---")
gemini_models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.5-pro"]
if config.GEMINI_API_KEY:
    g_client = genai.Client(api_key=config.GEMINI_API_KEY)
    for gm in gemini_models:
        try:
            res = g_client.models.generate_content(model=gm, contents="Say HELLO")
            print(f"✅ SUCCESS GEMINI ({gm}) -> {res.text.strip()}")
            break
        except Exception as e:
            print(f"❌ FAIL GEMINI ({gm}) -> {str(e)[:80]}")
