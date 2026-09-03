import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import time
from typing import Dict, Any, List


class NewsScanner:
    """
    Fetches live Yahoo Finance RSS headlines for a symbol.
    Results are cached for 5 minutes to avoid hammering the feed on every cycle.
    Does NOT call any AI — purely data gathering.
    """

    def __init__(self):
        self._cache: Dict[str, tuple] = {}   # symbol -> (headlines, timestamp)
        self._ttl = 300  # 5-minute cache

    def get_headlines(self, symbol: str) -> List[str]:
        now = time.time()
        if symbol in self._cache:
            headlines, ts = self._cache[symbol]
            if now - ts < self._ttl:
                return headlines

        url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={urllib.parse.quote(symbol)}&region=US&lang=en-US"
        headlines = []
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                root = ET.fromstring(resp.read())
                for item in root.findall("./channel/item")[:3]:
                    t = item.find("title")
                    if t is not None and t.text:
                        headlines.append(t.text)
        except Exception:
            pass

        if not headlines:
            headlines = [f"No breaking news for {symbol}. Analyzing technical momentum."]

        self._cache[symbol] = (headlines, now)
        return headlines

    def get_sentiment_summary(self, symbol: str) -> Dict[str, Any]:
        """Calculates dynamic news sentiment score and categorization for candidate ticker."""
        headlines = self.get_headlines(symbol)
        text = " ".join(headlines).lower()
        bull_words = ["growth", "surge", "record", "beat", "rally", "buy", "upgrade", "outperform", "bullish", "jump", "ai", "expansion", "profit"]
        bear_words = ["drop", "fall", "decline", "cut", "miss", "sell", "downgrade", "bearish", "plunge", "risk", "lawsuit", "investigation", "loss"]
        
        bull_score = sum(1 for w in bull_words if w in text)
        bear_score = sum(1 for w in bear_words if w in text)
        
        if bull_score > bear_score:
            sentiment = "BULLISH"
            score = 0.75 + min(0.2, bull_score * 0.05)
        elif bear_score > bull_score:
            sentiment = "BEARISH"
            score = max(0.1, 0.25 - min(0.15, bear_score * 0.05))
        else:
            sentiment = "NEUTRAL"
            score = 0.50
            
        return {
            "symbol": symbol,
            "sentiment": sentiment,
            "sentiment_score": round(score, 2),
            "headlines": headlines[:3]
        }


news_scanner = NewsScanner()
