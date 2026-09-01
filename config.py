import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ALPACA_API_KEY: str = os.getenv("ALPACA_API_KEY", "")
    ALPACA_SECRET_KEY: str = os.getenv("ALPACA_SECRET_KEY", "")
    ALPACA_PAPER: bool = os.getenv("ALPACA_PAPER", "true").lower() == "true"

    BASE_URL: str = "https://paper-api.alpaca.markets" if ALPACA_PAPER else "https://api.alpaca.markets"
    DATA_URL: str = "https://data.alpaca.markets"

    EXECUTION_MODE: str = os.getenv("EXECUTION_MODE", "FULL").upper()
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Nvidia NIM API Keys for DeepSeek V4 Flash
    NVIDIA_KEYS = [
        "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",
        "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",
        "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",
    ]

    # AI Model Names (verified working)
    DEEPSEEK_MODEL: str = "deepseek-ai/deepseek-v4-flash-0731"
    GEMINI_MODELS: list = [
        "models/gemini-3.5-flash-lite",
        "models/gemini-3.1-flash-lite",
        "models/gemini-flash-lite-latest",
        "models/gemini-3.5-flash"
    ]

    # Risk Parameters
    MAX_PORTFOLIO_RISK_PCT: float = float(os.getenv("MAX_PORTFOLIO_RISK_PCT", "3.0"))
    MAX_POSITION_RISK_PCT: float = float(os.getenv("MAX_POSITION_RISK_PCT", "5.0"))  # 5% of equity per trade
    STOP_LOSS_PCT: float = float(os.getenv("STOP_LOSS_PCT", "50.0"))

    # Block Trade Size ($15k per Tier-1 trade, 0% margin risk)
    BLOCK_NOTIONAL: float = 15000.0

    PORT: int = int(os.getenv("PORT", "8080"))

    # High-Velocity Breakout Targets
    TARGET_SYMBOLS = ["NVDA", "MSTR", "COIN", "TSLA", "PLTR", "CRWD"]

    @staticmethod
    def is_market_open() -> bool:
        """Check if US Market is open (9:30 AM - 4:00 PM EST, Mon-Fri)."""
        import datetime
        import pytz
        est = pytz.timezone("US/Eastern")
        now = datetime.datetime.now(est)
        if now.weekday() > 4:
            return False
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        return market_open <= now <= market_close


config = Config()
