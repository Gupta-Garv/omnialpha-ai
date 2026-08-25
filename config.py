import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ALPACA_API_KEY: str = os.getenv("ALPACA_API_KEY", "")
    ALPACA_SECRET_KEY: str = os.getenv("ALPACA_SECRET_KEY", "")
    ALPACA_PAPER: bool = os.getenv("ALPACA_PAPER", "true").lower() == "true"
    
    # API URLs
    BASE_URL: str = "https://paper-api.alpaca.markets" if ALPACA_PAPER else "https://api.alpaca.markets"
    DATA_URL: str = "https://data.alpaca.markets"
    
    # AI Engine
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Risk Parameters
    MAX_PORTFOLIO_RISK_PCT: float = float(os.getenv("MAX_PORTFOLIO_RISK_PCT", "3.0"))
    MAX_POSITION_RISK_PCT: float = float(os.getenv("MAX_POSITION_RISK_PCT", "2.0"))
    STOP_LOSS_PCT: float = float(os.getenv("STOP_LOSS_PCT", "50.0"))
    
    # Dashboard Configuration (Port 8080 avoids macOS AirPlay conflict on 5000)
    PORT: int = int(os.getenv("PORT", "8080"))
    
    # Target Focus Underlyings (High Liquidity Options)
    TARGET_SYMBOLS = ["SPY", "QQQ", "NVDA", "AAPL", "TSLA", "AMD"]

config = Config()
