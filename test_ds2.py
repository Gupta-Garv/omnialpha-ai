from openai import OpenAI
client = OpenAI(
  base_url = "https://integrate.api.nvidia.com/v1",
  api_key = "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"
)
try:
    completion = client.chat.completions.create(
      model="deepseek-ai/deepseek-v4-flash-0731",
      messages=[{"role":"user","content":"Write a limerick"}],
      temperature=1, max_tokens=100
    )
    print("DS WORKS:", completion.choices[0].message.content)
except Exception as e:
    print("DS ERROR:", e)
