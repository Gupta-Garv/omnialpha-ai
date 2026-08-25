from config import config
from alpaca.trading.client import TradingClient

def test_connection():
    try:
        client = TradingClient(config.ALPACA_API_KEY, config.ALPACA_SECRET_KEY, paper=config.ALPACA_PAPER)
        account = client.get_account()
        print("STATUS: SUCCESS")
        print(f"ACCOUNT_ID: {account.id}")
        print(f"EQUITY: ${float(account.equity):,.2f}")
        print(f"BUYING_POWER: ${float(account.buying_power):,.2f}")
        print(f"STATUS: {account.status}")
    except Exception as e:
        print("STATUS: FAILED")
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    test_connection()
