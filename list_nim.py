from openai import OpenAI

keys = [
    "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",
    "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",
    "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"
]

for i, k in enumerate(keys):
    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=k)
    try:
        models = client.models.list()
        print(f"KEY {i} MODELS COUNT: {len(models.data)}")
        for m in models.data[:10]:
            print(f"   - {m.id}")
    except Exception as e:
        print(f"KEY {i} ERROR: {e}")
