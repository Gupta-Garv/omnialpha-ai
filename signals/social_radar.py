import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

class SocialRadar:
    """Scans public news & sentiment streams for real-time velocity signals."""
    
    HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

    def analyze_ticker_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Fetch Google News RSS for symbol and compute sentiment velocity."""
        url = f"https://news.google.com/rss/search?q={symbol}+stock+market&hl=en-US&gl=US&ceid=US:en"
        
        bull_keywords = [
            "breakthrough", "record", "upgrade", "outperform", "surge", "growth", 
            "profit", "rally", "gain", "higher", "rise", "beat", "buy", "bull", 
            "target", "positive", "ai", "tech", "strong", "lead"
        ]
        bear_keywords = [
            "resigns", "lawsuit", "investigation", "downgrade", "plunge", "sec", 
            "loss", "recall", "drop", "fall", "lower", "cut", "warn", "risk", 
            "bear", "fear", "sell", "sink", "decline"
        ]
        
        bull_score = 0
        bear_score = 0
        headlines = []
        
        try:
            res = requests.get(url, headers=self.HEADERS, timeout=8)
            if res.status_code == 200:
                root = ET.fromstring(res.content)
                for item in root.findall(".//item")[:15]:
                    title_elem = item.find("title")
                    if title_elem is not None and title_elem.text:
                        title_text = title_elem.text
                        text_lower = title_text.lower()
                        headlines.append(title_text)
                        
                        for kw in bull_keywords:
                            if kw in text_lower:
                                bull_score += 1
                        for kw in bear_keywords:
                            if kw in text_lower:
                                bear_score += 1
        except Exception:
            pass # Return neutral state on network issue

        sentiment = "NEUTRAL"
        if bull_score > bear_score:
            sentiment = "BULLISH_VELOCITY"
        elif bear_score > bull_score:
            sentiment = "BEARISH_VELOCITY"
        elif len(headlines) > 0:
            # Default to moderate bullish velocity on market momentum
            sentiment = "BULLISH_VELOCITY" if symbol in ["NVDA", "AMD", "QQQ", "SPY"] else "NEUTRAL"

        return {
            "symbol": symbol,
            "sentiment": sentiment,
            "bull_score": bull_score,
            "bear_score": bear_score,
            "headline_count": len(headlines),
            "sample_headline": headlines[0] if headlines else None
        }

social_radar = SocialRadar()
