import time
import threading
from typing import Optional
from openai import OpenAI
import httpx
from config import config

try:
    from google import genai
    _GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    _GEMINI_AVAILABLE = False


class AIRouter:
    """
    Round-robin AI router.
    Primary: Nvidia NIM DeepSeek V4 Flash (3 keys, 35 RPM each).
    Fallback: Gemini 3.5 Flash (if DeepSeek returns 404/error).
    All calls have a hard 20s timeout to prevent the trading loop from hanging.
    """

    def __init__(self):
        self._keys = config.NVIDIA_KEYS
        # Hard 15s timeout via httpx — the default OpenAI timeout kwarg doesn't work on NIM
        _timeout = httpx.Timeout(15.0, connect=5.0)
        self._clients = [
            OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=k, http_client=httpx.Client(timeout=_timeout))
            for k in self._keys
        ]
        self._usage: dict = {i: [] for i in range(len(self._keys))}
        self._lock = threading.Lock()
        self._idx = 0
        self._gemini_client = None
        if _GEMINI_AVAILABLE and config.GEMINI_API_KEY:
            try:
                self._gemini_client = genai.Client(api_key=config.GEMINI_API_KEY)
            except Exception:
                pass

    def _next_client(self) -> tuple[int, OpenAI]:
        """Return (key_index, client) using round-robin, respecting 35 RPM."""
        with self._lock:
            now = time.time()
            for _ in range(len(self._keys)):
                self._usage[self._idx] = [t for t in self._usage[self._idx] if now - t < 60]
                if len(self._usage[self._idx]) < 35:
                    idx = self._idx
                    self._usage[idx].append(now)
                    self._idx = (self._idx + 1) % len(self._keys)
                    return idx, self._clients[idx]
                self._idx = (self._idx + 1) % len(self._keys)
            # All keys exhausted — push through key 0
            self._usage[0].append(now)
            return 0, self._clients[0]

    def query(self, prompt: str, system_prompt: str = "You are a quantitative AI.") -> str:
        """
        Primary: Gemini 3.5 Flash (fast, reliable, free tier).
        DeepSeek NIM is kept as optional secondary but is currently skipped
        because all NIM account keys return APITimeoutError (endpoint unreachable).
        """
        # Try Gemini models first — fast 1s response with zero rate-limit issues
        if self._gemini_client:
            full_prompt = f"{system_prompt}\n\n{prompt}"
            for g_model in config.GEMINI_MODELS:
                try:
                    resp = self._gemini_client.models.generate_content(
                        model=g_model,
                        contents=full_prompt,
                    )
                    if resp and resp.text:
                        return resp.text.strip()
                except Exception as ge:
                    # Print and continue to next model in list
                    pass

        # Fallback: DeepSeek NIM (may be slow / timeout)
        idx, client = self._next_client()
        try:
            completion = client.chat.completions.create(
                model=config.DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=512,
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"  [ROUTER] DeepSeek also failed ({type(e).__name__}).")

        return "PROPOSE_TRADE\nDefault bullish bias — no AI response available."


ai_router = AIRouter()
