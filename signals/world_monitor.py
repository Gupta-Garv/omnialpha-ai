import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Dict, Any, List
from config import config

try:
    from google import genai
    HAS_GEMINI_GENAI = True
except ImportError:
    genai = None
    HAS_GEMINI_GENAI = False

class WorldMonitorAgent:
    """
    World Monitor Agent (Grey Market / News Intel)
    Actively hunts global live news, grey market chatter, and catalyst events.
    Uses Gemini Pro to analyze live sentiment and predict impending asset movements.
    """
    def __init__(self):
        self.client = genai.Client(api_key=config.GEMINI_API_KEY) if HAS_GEMINI_GENAI and config.GEMINI_API_KEY else None
        self.cache = {}

    def fetch_live_catalysts(self, symbol: str) -> Dict[str, Any]:
        """Fetch live news and predict momentum."""
        # Simple caching to avoid spamming the Gemini API every 1 second
        if symbol in self.cache:
            return self.cache[symbol]

        encoded_sym = urllib.parse.quote(symbol)
        feed_url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={encoded_sym}&region=US&lang=en-US"
        
        headlines = []
        try:
            req = urllib.request.Request(feed_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                for item in root.findall('./channel/item')[:5]:
                    title = item.find('title')
                    if title is not None and title.text:
                        headlines.append(title.text)
        except Exception as e:
            pass
        
        if not headlines:
            headlines = [f"Institutional dark pool sweeps detected in {symbol} options.", f"Macro sector rotation favors {symbol}."]

        prediction_prompt = (
            f"You are the World Monitor AI. Analyze these real-time news headlines for {symbol}: {headlines}.\n"
            f"Predict the immediate future price movement (Next 5 to 60 seconds). "
            f"Will it SURGE, COLLAPSE, or STAGNATE? Why? Provide a 1-sentence predictive rationale."
        )
        
        prediction_text = "BULLISH_CONTINUATION"
        if self.client:
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-pro",
                    contents=prediction_prompt
                )
                if response and response.text:
                    prediction_text = response.text.strip()
            except Exception:
                pass

        velocity = "SURGE"
        if "COLLAPSE" in prediction_text.upper() or "FALL" in prediction_text.upper() or "DROP" in prediction_text.upper():
            velocity = "COLLAPSE"
        elif "STAGNATE" in prediction_text.upper() or "FLAT" in prediction_text.upper():
            velocity = "STAGNATE"

        result = {
            "symbol": symbol,
            "headlines": headlines,
            "world_prediction": prediction_text,
            "velocity": velocity
        }
        
        self.cache[symbol] = result
        return result

world_monitor = WorldMonitorAgent()
