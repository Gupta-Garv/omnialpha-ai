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

    @staticmethod
    def is_market_open() -> bool:
        """
        Check if US Market is currently open (9:30 AM - 4:00 PM EST).
        """
        import datetime
        import pytz
        
        est = pytz.timezone('US/Eastern')
        now_est = datetime.datetime.now(est)
        
        if now_est.weekday() > 4:
            return False
            
        market_open = now_est.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now_est.replace(hour=16, minute=0, second=0, microsecond=0)
        
        return market_open <= now_est <= market_close

config = Config()
