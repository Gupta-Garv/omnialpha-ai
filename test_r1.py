from openai import OpenAI
client = OpenAI(
  base_url = "https://integrate.api.nvidia.com/v1",
  api_key = "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"
)
try:
    completion = client.chat.completions.create(
      model="meta/llama-3.1-70b-instruct",
      messages=[{"role":"user","content":"Write a limerick"}],
      temperature=1, max_tokens=100
    )
    print("LLAMA WORKS:", completion.choices[0].message.content)
except Exception as e:
    print("LLAMA ERROR:", e)
