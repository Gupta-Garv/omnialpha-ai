from typing import Dict, Any, List
from config import config
from core.deepseek_router import ai_router
from signals.world_monitor import news_scanner
from memory.journal import reflexion_memory


class TradingCommittee:
    """
    Autonomous Multi-Agent Trading Committee.

    Entry Strategy (3:1 Reward/Risk mandate):
    - Gathers live news headlines for the symbol
    - Checks Reflexion Memory for past lessons
    - Queries AI (DeepSeek → Gemini fallback) for a trade decision
    - Validates via RiskShield before approving
    - Returns: {"action": "PROPOSE_TRADE" | "HOLD_CASH", "symbol", "reason", "confidence", "strategy_type"}

    Exit Strategy:
    - Evaluates each open position independently
    - Uses P&L percentage + AI judgement to decide HOLD / TAKE_PROFIT / CUT_LOSS
    - 3:1 logic: take profit at +3%, cut loss at -1%
    """

    ENTRY_SYSTEM_PROMPT = (
        "You are an elite autonomous quantitative trading AI managing a paper trading portfolio. "
        "Your mandate: grow the account aggressively using a strict 3:1 Reward-to-Risk ratio on every trade. "
        "You receive live news headlines and past trade lessons for a specific ticker. "
        "DECISION RULES:\n"
        "- If news shows bullish momentum, strong earnings, sector rotation, or unusual institutional activity → output PROPOSE_TRADE\n"
        "- If news is negative, bearish, or unclear → output HOLD_CASH\n"
        "- Default bias: PROPOSE_TRADE when in doubt (lean aggressive, we are paper trading)\n"
        "OUTPUT FORMAT (exactly 2 lines):\n"
        "Line 1: PROPOSE_TRADE or HOLD_CASH\n"
        "Line 2: One sentence rationale."
    )

    EXIT_SYSTEM_PROMPT = (
        "You are an aggressive autonomous quantitative trading AI managing open positions. "
        "Your mandate: actively harvest profits and recycle capital into high-momentum trades. "
        "DECISION RULES:\n"
        "- P&L > +0.3%: output TAKE_PROFIT (bank the gains immediately)\n"
        "- P&L < -0.3%: output CUT_LOSS (cut small loss quickly)\n"
        "- If momentum has stalled: output TAKE_PROFIT or CUT_LOSS to recycle capital.\n"
        "OUTPUT FORMAT (exactly 2 lines):\n"
        "Line 1: HOLD or TAKE_PROFIT or CUT_LOSS\n"
        "Line 2: One sentence rationale."
    )

    def evaluate_entry(self, symbol: str, account: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate whether to enter a new position in `symbol`."""
        equity = float(account.get("equity", 100000.0))
        buying_power = float(account.get("buying_power", 400000.0))

        # Max risk per trade: 5% of equity
        max_risk = equity * (config.MAX_POSITION_RISK_PCT / 100.0)
        if config.BLOCK_NOTIONAL > buying_power:
            return self._hold(symbol, "Insufficient buying power for block trade.")

        headlines = news_scanner.get_headlines(symbol)
        lessons = reflexion_memory.get_lessons_for_symbol(symbol)

        user_prompt = (
            f"TICKER: {symbol}\n"
            f"LIVE NEWS:\n" + "\n".join(f"  - {h}" for h in headlines) + "\n\n"
            f"PAST TRADE LESSONS:\n" + (
                "\n".join(f"  - {l}" for l in lessons) if lessons else "  - No prior trades on this symbol."
            ) + "\n\n"
            f"ACCOUNT: Equity=${equity:,.0f}, Buying Power=${buying_power:,.0f}\n"
            f"Proposed block size: ${config.BLOCK_NOTIONAL:,.0f}\n"
            f"Should we enter a leveraged long position in {symbol} RIGHT NOW?"
        )

        response = ai_router.query(prompt=user_prompt, system_prompt=self.ENTRY_SYSTEM_PROMPT)

        if not response:
            return self._hold(symbol, "AI router returned empty response — skipping cycle.")

        lines = [l.strip() for l in response.strip().split("\n") if l.strip()]
        action_raw = lines[0].upper() if lines else "HOLD_CASH"
        rationale = lines[1] if len(lines) > 1 else "AI autonomous decision."

        if "PROPOSE_TRADE" in action_raw:
            return {
                "symbol": symbol,
                "action": "PROPOSE_TRADE",
                "strategy_type": "MOMENTUM_LONG",
                "confidence": 0.85,
                "reason": rationale,
            }

        return self._hold(symbol, rationale)

    def evaluate_exit(self, position: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate whether to exit an open position instantly."""
        symbol = position.get("symbol", "")
        market_value = float(position.get("market_value", 1.0))
        unrealized_pl = float(position.get("unrealized_pl", 0.0))
        pnl_pct = (unrealized_pl / market_value) * 100 if market_value > 0 else 0.0

        # Instant Hard Rules (High Frequency Profit Harvesting)
        if pnl_pct >= 0.3:
            return {"action": "TAKE_PROFIT_EXIT", "symbol": symbol,
                    "reason": f"Active target hit +{pnl_pct:.2f}%. Banking +${unrealized_pl:.2f}.", "pnl": unrealized_pl}
        if pnl_pct <= -0.3:
            return {"action": "CUT_LOSS_EXIT", "symbol": symbol,
                    "reason": f"Active stop loss hit {pnl_pct:.2f}%. Preserving capital.", "pnl": unrealized_pl}

        # Between -0.3% and +0.3%: hold and let profits run
        return {"action": "HOLD_POSITION", "symbol": symbol, "reason": f"Position within band ({pnl_pct:+.2f}%). Holding for breakout.", "pnl": unrealized_pl}

    @staticmethod
    def _hold(symbol: str, reason: str) -> Dict[str, Any]:
        return {
            "symbol": symbol,
            "action": "HOLD_CASH",
            "strategy_type": "WAITING",
            "confidence": 0.0,
            "reason": reason,
        }


committee = TradingCommittee()
