from openai import OpenAI
client = OpenAI(
  base_url = "https://integrate.api.nvidia.com/v1",
  api_key = "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"
)
for model in client.models.list():
    if 'deepseek' in model.id.lower():
        print(model.id)
