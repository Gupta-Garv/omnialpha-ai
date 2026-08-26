import os
from dotenv import load_dotenv
load_dotenv()
from alpaca.trading.client import TradingClient

client = TradingClient(os.getenv("ALPACA_API_KEY"), os.getenv("ALPACA_SECRET_KEY"), paper=True)
client.close_all_positions(cancel_orders=True)
print("All positions liquidated. Fresh slate.")
