import os
from dotenv import load_dotenv
load_dotenv()
from alpaca.trading.client import TradingClient

client = TradingClient(os.getenv("ALPACA_API_KEY"), os.getenv("ALPACA_SECRET_KEY"), paper=True)

account = client.get_account()
print(f"Equity: ${account.equity}")
print(f"Buying Power: ${account.buying_power}")

positions = client.get_all_positions()
print(f"\nOpen Positions ({len(positions)}):")
for p in positions:
    print(f"- {p.symbol}: Qty {p.qty}, Market Value ${p.market_value}, Unrealized P&L ${p.unrealized_pl}, Current Price ${p.current_price}, Avg Entry ${p.avg_entry_price}")
