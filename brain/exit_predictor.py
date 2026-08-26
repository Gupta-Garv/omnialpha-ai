from typing import Dict, Any, List
from config import config
from signals.world_monitor import world_monitor

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
            
        self.ai_cache = {}
        self.ai_cache_ttl = 1200  # 20 minute cache (keeps daily quota exactly at ~50%)

    def evaluate_position_exit(self, position: Dict[str, Any], market_sentiment: str) -> Dict[str, Any]:
        """
        Determines whether to HOLD, TAKE_PROFIT, or CUT_LOSS for an active position.
        """
        symbol = position.get("symbol", "")
        qty = int(float(position.get("qty", 1)))
        current_price = float(position.get("current_price", 0.0))
        market_value = float(position.get("market_value", 0.0))
        unrealized_pl = float(position.get("unrealized_pl", 0.0))
        
        # Pull live World Monitor predictive data
        monitor_intel = world_monitor.fetch_live_catalysts(symbol)
        world_velocity = monitor_intel.get("velocity", "SURGE")
        world_prediction = monitor_intel.get("world_prediction", "")
        
        # PROACTIVE EXIT 1: Predictive Collapse Escape
        # If the AI world monitor predicts a collapse based on live grey market news, dump immediately before the drop!
        if world_velocity == "COLLAPSE" and unrealized_pl > 0:
            return {
                "action": "TAKE_PROFIT_EXIT",
                "symbol": symbol,
                "reason": f"PROACTIVE PREDICTION: World Monitor detected impending drop. Pulling out to bank ${unrealized_pl:.2f}. Intel: {world_prediction[:80]}...",
                "banked_pnl": unrealized_pl,
                "confidence": 0.99
            }

        # PROACTIVE EXIT 2: High Profit Target Exit (Locking in $350 - $3,000+ gains)
        if unrealized_pl >= 350.0:
            return {
                "action": "TAKE_PROFIT_EXIT",
                "symbol": symbol,
                "reason": f"Target profit threshold reached (+${unrealized_pl:.2f}). Banking realized gains to cash reserve.",
                "banked_pnl": unrealized_pl,
                "confidence": 0.92
            }
            
        # PROACTIVE EXIT 3: Gemini 3.1 Pro High-Frequency AI Deep Sentiment Exits
        if self.client and (unrealized_pl > 100.0 or unrealized_pl < -50.0):
            import time
            current_time = time.time()
            
            # Check AI Cache first
            if symbol in self.ai_cache:
                cached_res, timestamp = self.ai_cache[symbol]
                if current_time - timestamp < self.ai_cache_ttl:
                    return cached_res

            try:
                prompt = (
                    f"You are a Senior Quantitative Portfolio Manager using Gemini 3.1 Pro capability. Evaluate open position in {symbol}.\n"
                    f"Qty: {qty}, Market Value: ${market_value}, Unrealized Profit: ${unrealized_pl}.\n"
                    f"World News Intel: {world_prediction}.\n"
                    f"Predict if the asset will fall in the next 10 seconds. Should we HOLD or TAKE_PROFIT / CUT_LOSS right now before it moves? Reply with short rationale."
                )
                response = self.client.models.generate_content(
                    model="gemini-2.5-pro",
                    contents=prompt
                )
                rationale = response.text.strip() if response and response.text else "AI Exit Evaluation Completed."
                
                if "TAKE_PROFIT" in rationale.upper() or "CUT_LOSS" in rationale.upper():
                    action_type = "TAKE_PROFIT_EXIT" if unrealized_pl > 0 else "CUT_LOSS_EXIT"
                    result = {
                        "action": action_type,
                        "symbol": symbol,
                        "reason": f"AI PREDICTIVE EXIT: {rationale[:120]}",
                        "banked_pnl": unrealized_pl,
                        "confidence": 0.95
                    }
                    self.ai_cache[symbol] = (result, time.time())
                    return result
                    
                # Cache the HOLD decision too to prevent rapid re-evaluation
                hold_result = {
                    "action": "HOLD_POSITION",
                    "symbol": symbol,
                    "reason": f"AI evaluation: {rationale[:80]}",
                    "banked_pnl": 0.0,
                    "confidence": 0.85
                }
                self.ai_cache[symbol] = (hold_result, time.time())
                return hold_result
                
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
