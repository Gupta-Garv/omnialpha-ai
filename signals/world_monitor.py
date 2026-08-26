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
            with urllib.request.urlopen(req, timeout=4) as resp:
                root = ET.fromstring(resp.read())
                for item in root.findall("./channel/item")[:5]:
                    t = item.find("title")
                    if t is not None and t.text:
                        headlines.append(t.text)
        except Exception:
            pass

        if not headlines:
            headlines = [f"No breaking news for {symbol}. Analyzing technical momentum."]

        self._cache[symbol] = (headlines, now)
        return headlines


news_scanner = NewsScanner()
