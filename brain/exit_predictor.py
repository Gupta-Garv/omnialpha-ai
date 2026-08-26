from typing import Dict, Any, List
from config import config
from signals.world_monitor import world_monitor

from core.deepseek_router import deepseek_router

class AIExitPredictor:
    """
    AI Dynamic Exit Predictor & Profit Harvester — 
    Analyzes live open positions to determine optimal profit-taking exits,
    trailing stop levels, and capital reinvestment timing using Gemini AI.
    """
    
    def __init__(self):
        pass

    def evaluate_position_exit(self, position: Dict[str, Any], market_sentiment: str) -> Dict[str, Any]:
        """
        100% Autonomous LLM Decision Engine.
        Feeds live context to DeepSeek and lets the AI decide based on a 3:1 Risk/Reward mandate.
        """
        symbol = position.get("symbol", "")
        qty = int(float(position.get("qty", 1)))
        current_price = float(position.get("current_price", 0.0))
        market_value = float(position.get("market_value", 0.0))
        unrealized_pl = float(position.get("unrealized_pl", 0.0))
        entry_price = float(position.get("avg_entry_price", 0.0))
        
        # Pull live World Monitor predictive data (news)
        monitor_intel = world_monitor.fetch_live_catalysts(symbol)
        world_prediction = monitor_intel.get("world_prediction", "No news")

        system_prompt = (
            "You are an elite, autonomous Quantitative Trading AI managing a highly leveraged portfolio. "
            "Your non-negotiable directive is to MAKE MONEY and recover all losses. "
            "You must enforce a strict 3:1 Reward-to-Risk ratio logic to minimize losses. "
            "Analyze the position and breaking news. If the momentum is breaking, CUT LOSS immediately to prevent bleeding. "
            "If the trend is strong, HOLD to maximize profit. If the news is turning bad on a winning trade, TAKE_PROFIT. "
            "Respond ONLY with one of these three exact words on the first line: HOLD, TAKE_PROFIT, or CUT_LOSS. "
            "On the second line, provide a 1-sentence aggressive rationale for your decision."
        )

        user_prompt = (
            f"LIVE POSITION STATUS for {symbol}:\n"
            f"- Entry Price: ${entry_price:.2f}\n"
            f"- Current Price: ${current_price:.2f}\n"
            f"- Market Value: ${market_value:.2f}\n"
            f"- Unrealized P&L: ${unrealized_pl:.2f}\n"
            f"\nLIVE NEWS INTELLIGENCE:\n{world_prediction}\n\n"
            f"Based on your mathematical analysis and the news, what is your executive decision?"
        )

        response = deepseek_router.query(prompt=user_prompt, system_prompt=system_prompt)
        
        # Parse output
        lines = response.split('\n')
        action_raw = lines[0].strip().upper() if lines else "HOLD"
        rationale = lines[1].strip() if len(lines) > 1 else "DeepSeek Autonomous Execution"

        action = "HOLD_POSITION"
        if "TAKE_PROFIT" in action_raw or "TAKE PROFIT" in action_raw:
            action = "TAKE_PROFIT_EXIT"
        elif "CUT_LOSS" in action_raw or "CUT LOSS" in action_raw:
            action = "CUT_LOSS_EXIT"

        return {
            "action": action,
            "symbol": symbol,
            "reason": f"AI AUTONOMY: {rationale}",
            "banked_pnl": unrealized_pl if action != "HOLD_POSITION" else 0.0,
            "confidence": 0.99
        }

exit_predictor = AIExitPredictor()
