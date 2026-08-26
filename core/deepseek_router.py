import time
import threading
from typing import List, Dict, Any, Optional
from openai import OpenAI
from config import config
try:
    from google import genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

class DeepSeekRouter:
    """
    Round-robin load balancer for unlimited API rate limits.
    Distributes traffic across multiple Nvidia NIM DeepSeek V4 Flash keys.
    Max 35 requests per minute per key to avoid strict 40 RPM limits.
    """
    def __init__(self):
        self.keys = [
            "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",
            "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",
            "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"
        ]
        self.clients = [
            OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=key) 
            for key in self.keys
        ]
        
        # Usage tracking: key_index -> list of timestamps
        self.usage_history = {i: [] for i in range(len(self.keys))}
        self.lock = threading.Lock()
        self.max_rpm = 35
        self.current_idx = 0

    def _get_available_client_index(self) -> int:
        with self.lock:
            now = time.time()
            
            # Clean up old history (> 60 seconds)
            for i in range(len(self.keys)):
                self.usage_history[i] = [t for t in self.usage_history[i] if now - t < 60]
                
            # Find the next available key starting from current_idx
            for _ in range(len(self.keys)):
                if len(self.usage_history[self.current_idx]) < self.max_rpm:
                    idx = self.current_idx
                    self.usage_history[idx].append(now)
                    # Advance to next for round-robin
                    self.current_idx = (self.current_idx + 1) % len(self.keys)
                    return idx
                    
                self.current_idx = (self.current_idx + 1) % len(self.keys)
                
            # If all are exhausted, fallback to 0 (might hit rate limit, but better than crashing)
            # Alternatively, we could sleep, but we want hyper-reactive.
            print("⚠️ DEEPSEEK ROUTER WARNING: All keys hit 35 RPM. Pushing through Key 0.")
            self.usage_history[0].append(now)
            return 0

    def query(self, prompt: str, system_prompt: str = "You are a quantitative AI agent.") -> str:
        """Sends a query to DeepSeek V4 Flash using the next available key."""
        idx = self._get_available_client_index()
        client = self.clients[idx]
        
        try:
            completion = client.chat.completions.create(
                model="deepseek-ai/deepseek-v4-flash-0731",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                top_p=0.95,
                max_tokens=2048,
                extra_body={"chat_template_kwargs": {"thinking": True, "reasoning_effort": "high"}},
                stream=False
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ DEEPSEEK API ERROR on Key {idx}: {str(e)}")
            
            # FALLBACK TO GEMINI
            if HAS_GEMINI and config.GEMINI_API_KEY:
                try:
                    print(f"🔄 FALLING BACK TO GEMINI for this request...")
                    gemini_client = genai.Client(api_key=config.GEMINI_API_KEY)
                    gemini_prompt = f"{system_prompt}\n\n{prompt}"
                    response = gemini_client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=gemini_prompt
                    )
                    return response.text.strip() if response and response.text else ""
                except Exception as gemini_e:
                    print(f"❌ GEMINI FALLBACK ALSO FAILED: {str(gemini_e)}")
            
            return ""

deepseek_router = DeepSeekRouter()
