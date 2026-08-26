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
        Send a prompt. DeepSeek V4 Flash first, Gemini 3.5 Flash fallback.
        Hard 15s ceiling enforced via httpx — never blocks the trading loop.
        """
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
            print(f"  [ROUTER] DeepSeek key {idx} ({type(e).__name__}). Trying Gemini fallback.")

        # Gemini Fallback
        if self._gemini_client:
            try:
                full_prompt = f"{system_prompt}\n\n{prompt}"
                resp = self._gemini_client.models.generate_content(
                    model=config.GEMINI_FALLBACK_MODEL,
                    contents=full_prompt,
                )
                return resp.text.strip() if resp and resp.text else ""
            except Exception as ge:
                print(f"  [ROUTER] Gemini fallback error: {type(ge).__name__}: {str(ge)[:80]}")

        return ""


ai_router = AIRouter()
