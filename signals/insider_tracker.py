import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

class InsiderTracker:
    """Scans official SEC EDGAR RSS feed for Form 4 (insider trading) signals."""
    
    SEC_RSS_URL = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4&company=&datea=&dateb=&owner=only&count=40&output=atom"
    HEADERS = {"User-Agent": "OmniAlphaAI research@omnialpha.io"}

    def fetch_recent_filings(self, target_symbols: List[str]) -> List[Dict[str, Any]]:
        """Fetch Form 4 filings for target ticker symbols."""
        signals = []
        try:
            res = requests.get(self.SEC_RSS_URL, headers=self.HEADERS, timeout=8)
            if res.status_code != 200:
                return signals

            root = ET.fromstring(res.content)
            namespace = {"atom": "http://www.w3.org/2005/Atom"}
            
            for entry in root.findall("atom:entry", namespace):
                title_elem = entry.find("atom:title", namespace)
                updated_elem = entry.find("atom:updated", namespace)
                link_elem = entry.find("atom:link", namespace)
                
                title_text = title_elem.text if title_elem is not None else ""
                updated_time = updated_elem.text if updated_elem is not None else ""
                link_url = link_elem.attrib.get("href", "") if link_elem is not None else ""
                
                for symbol in target_symbols:
                    if f"({symbol})" in title_text or f" {symbol} " in title_text or f"- {symbol}" in title_text:
                        signals.append({
                            "symbol": symbol,
                            "title": title_text,
                            "form_type": "FORM_4_INSIDER",
                            "updated_at": updated_time,
                            "url": link_url,
                            "signal": "INSIDER_TRANSACTION_DETECTED"
                        })
        except Exception as e:
            # Defensive handling: return empty list on network error
            pass
            
        return signals

insider_tracker = InsiderTracker()
