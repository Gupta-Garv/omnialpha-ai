import time
from typing import List
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockSnapshotRequest
from config import config


UNIVERSE = [
    "SPY", "QQQ", "NVDA", "AAPL", "TSLA", "AMD", "MSFT", "AMZN", "META", "GOOGL",
    "COIN", "MARA", "MSTR", "PLTR", "ARM", "CRWD", "NFLX", "UBER", "HOOD", "RIVN",
    "GLD", "XOM", "SMCI", "AVGO", "DELL", "ORCL", "DIS", "PYPL", "SQ", "ROKU"
]
DEFAULT_TARGETS = ["NVDA", "MSTR", "COIN", "TSLA", "PLTR", "CRWD"]


class ScreenerAgent:
    """
    Relative Volume (RVOL) & Momentum Screener.
    Ranks universe by intraday volatility % and relative volume surge.
    Selects top names experiencing institutional volume flow.
    """

    def __init__(self):
        self._client = StockHistoricalDataClient(config.ALPACA_API_KEY, config.ALPACA_SECRET_KEY)
        self._last_scan = 0
        self._scan_interval = 300  # 5-minute dynamic scan interval
        self._current = list(DEFAULT_TARGETS)

    def get_targets(self) -> List[str]:
        if time.time() - self._last_scan < self._scan_interval:
            return self._current

        try:
            req = StockSnapshotRequest(symbol_or_symbols=UNIVERSE)
            snapshots = self._client.get_stock_snapshot(req)

            scored = []
            for sym, snap in snapshots.items():
                if not snap.latest_trade or not snap.previous_daily_bar:
                    continue
                prev = snap.previous_daily_bar.close
                curr = snap.latest_trade.price
                if prev <= 0:
                    continue
                pct = abs((curr - prev) / prev * 100)
                vol = snap.daily_bar.volume if snap.daily_bar else 0
                # Score combines % price change and volume intensity
                score = pct * 3.0 + (vol / 500_000)
                scored.append((sym, score))

            scored.sort(key=lambda x: x[1], reverse=True)
            top_symbols = [s[0] for s in scored[:6]]
            if len(top_symbols) == 6:
                self._current = top_symbols
                self._last_scan = time.time()
                print(f"  [SCREENER] RVOL Momentum targets: {self._current}")
        except Exception as e:
            print(f"  [SCREENER] Error: {e}. Keeping current targets.")

        return self._current


screener_agent = ScreenerAgent()
