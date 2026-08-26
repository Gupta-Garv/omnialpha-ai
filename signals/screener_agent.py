import time
from typing import List
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockSnapshotRequest
from config import config

class ScreenerAgent:
    """
    Dynamic Market Screener
    Scans a broad universe of highly liquid institutional stocks once every hour.
    Ranks them by absolute momentum (highest % gain or % loss) and trading volume.
    Automatically updates the trading terminal's focus to the TOP 6 most active assets.
    """
    
    def __init__(self):
        self.universe = [
            # Indices & Core Tech
            "SPY", "QQQ", "NVDA", "AAPL", "TSLA", "AMD", "MSFT", "AMZN", "META", "GOOGL",
            # High Beta & Crypto
            "COIN", "MARA", "MSTR", "PLTR", "SMCI", "ARM", "CRWD",
            # Retail / Growth
            "NFLX", "UBER", "HOOD", "RIVN", "LCID", "SOFI", "AFRM"
        ]
        self.client = StockHistoricalDataClient(config.ALPACA_API_KEY, config.ALPACA_SECRET_KEY)
        self.last_scan_time = 0
        self.scan_interval = 3600  # 1 hour
        self.current_top_6 = ["SPY", "QQQ", "NVDA", "AAPL", "TSLA", "AMD"] # Default fallback

    def get_dynamic_targets(self) -> List[str]:
        """
        Returns the top 6 most active/volatile stocks to trade right now.
        Only queries Alpaca API once an hour to conserve rate limits.
        """
        current_time = time.time()
        
        # If market is closed or cache is valid, return the current targets
        if current_time - self.last_scan_time < self.scan_interval:
            return self.current_top_6
            
        try:
            req = StockSnapshotRequest(symbol_or_symbols=self.universe)
            res = self.client.get_stock_snapshot(req)
            
            scored_stocks = []
            for sym, snap in res.items():
                if not snap.latest_trade or not snap.previous_daily_bar:
                    continue
                    
                prev_close = snap.previous_daily_bar.close
                curr_price = snap.latest_trade.price
                
                # Avoid division by zero
                if prev_close <= 0:
                    continue
                    
                pct_change = abs(((curr_price - prev_close) / prev_close) * 100)
                vol = snap.daily_bar.volume if snap.daily_bar else 0
                
                # Score formula: Heavily weight momentum magnitude, blend with volume for liquidity safety
                score = (pct_change * 1000) + (vol / 100000)
                scored_stocks.append({"symbol": sym, "score": score, "pct": pct_change, "vol": vol})
            
            # Sort by highest score
            scored_stocks.sort(key=lambda x: x["score"], reverse=True)
            
            # Extract top 6
            new_targets = [s["symbol"] for s in scored_stocks[:6]]
            
            if len(new_targets) == 6:
                self.current_top_6 = new_targets
                self.last_scan_time = current_time
                print(f"🔄 SCREENER AGENT: Selected new Top 6 dynamic targets: {self.current_top_6}")
                
        except Exception as e:
            print(f"⚠️ SCREENER ERROR: Failed to fetch dynamic targets. Using fallback. ({str(e)})")
            
        return self.current_top_6

screener_agent = ScreenerAgent()
