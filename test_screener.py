from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockSnapshotRequest
from config import config

client = StockHistoricalDataClient(config.ALPACA_API_KEY, config.ALPACA_SECRET_KEY)
universe = ["SPY", "QQQ", "NVDA", "AAPL", "TSLA", "AMD", "MSFT", "AMZN", "META", "GOOGL"]
req = StockSnapshotRequest(symbol_or_symbols=universe)
res = client.get_stock_snapshot(req)
for sym, snap in res.items():
    prev_close = snap.previous_daily_bar.close if snap.previous_daily_bar else 1.0
    curr_price = snap.latest_trade.price
    pct_change = ((curr_price - prev_close) / prev_close) * 100
    print(f"{sym}: {pct_change:.2f}% (Vol: {snap.daily_bar.volume if snap.daily_bar else 0})")
