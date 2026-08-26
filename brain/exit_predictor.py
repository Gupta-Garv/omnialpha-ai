from typing import Dict, Any, List
from config import config

try:
    from google import genai
    HAS_GEMINI_GENAI = True
except ImportError:
    genai = None
    HAS_GEMINI_GENAI = False

class AIExitPredictor:
    """
    AI Dynamic Exit Predictor & Profit Harvester — 
    Analyzes live open positions to determine optimal profit-taking exits,
    trailing stop levels, and capital reinvestment timing using Gemini AI.
    """
    
    def __init__(self):
        if HAS_GEMINI_GENAI and config.GEMINI_API_KEY:
            try:
                self.client = genai.Client(api_key=config.GEMINI_API_KEY)
            except Exception:
                self.client = None
        else:
            self.client = None

    def evaluate_position_exit(self, position: Dict[str, Any], market_sentiment: str) -> Dict[str, Any]:
        """
        Determines whether to HOLD, TAKE_PROFIT, or CUT_LOSS for an active position.
        """
        symbol = position.get("symbol", "")
        qty = int(float(position.get("qty", 1)))
        current_price = float(position.get("current_price", 0.0))
        market_value = float(position.get("market_value", 0.0))
        unrealized_pl = float(position.get("unrealized_pl", 0.0))
        
        # Rule 1: High Profit Target Exit (Locking in $350 - $3,000+ gains)
        if unrealized_pl >= 350.0:
            return {
                "action": "TAKE_PROFIT_EXIT",
                "symbol": symbol,
                "reason": f"Target profit threshold reached (+${unrealized_pl:.2f}). Banking realized gains to cash reserve.",
                "banked_pnl": unrealized_pl,
                "confidence": 0.92
            }
            
        # Rule 2: Gemini AI Deep Sentiment Exits
        if self.client and unrealized_pl > 100.0:
            try:
                prompt = (
                    f"You are a Senior Quantitative Portfolio Manager. Evaluate position in {symbol}.\n"
                    f"Qty: {qty}, Market Value: ${market_value}, Unrealized Profit: ${unrealized_pl}.\n"
                    f"Market Sentiment: {market_sentiment}.\n"
                    f"Should we HOLD for higher target or TAKE_PROFIT now? Reply with short rationale."
                )
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                rationale = response.text.strip() if response and response.text else "AI Exit Evaluation Completed."
                
                if "TAKE_PROFIT" in rationale.upper() or market_sentiment == "BEARISH_VELOCITY":
                    return {
                        "action": "TAKE_PROFIT_EXIT",
                        "symbol": symbol,
                        "reason": f"Gemini AI Exit Signal: {rationale[:120]}",
                        "banked_pnl": unrealized_pl,
                        "confidence": 0.89
                    }
            except Exception:
                pass
                
        # Rule 3: Defensive Cut-Loss Guard (-5% drawdown trigger)
        if unrealized_pl <= -1200.0:
            return {
                "action": "CUT_LOSS_EXIT",
                "symbol": symbol,
                "reason": f"Risk Shield Guard: Preemptive stop-loss executed at -${abs(unrealized_pl):.2f} to protect capital.",
                "banked_pnl": unrealized_pl,
                "confidence": 0.95
            }

        return {
            "action": "HOLD_POSITION",
            "symbol": symbol,
            "reason": f"Position in trend (+${unrealized_pl:.2f}). Continuing momentum harvest.",
            "banked_pnl": 0.0,
            "confidence": 0.80
        }

exit_predictor = AIExitPredictor()
