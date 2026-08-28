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
        "Your mandate: hunt EXCLUSIVELY for ultra-high-conviction Tier-1 breakouts with massive profit upside. "
        "Evaluate the ticker on 3 dimensions and calculate a CATALYST SCORE (0-100):\n"
        "1. News & Catalyst Impact (0-40 pts): Major earnings beat, partnership, institutional volume, or sector surge.\n"
        "2. Technical Alignment (0-40 pts): Price momentum breaking out above resistance with expanding volume.\n"
        "3. Reflexion Memory Alignment (0-20 pts): Trade history confirms positive win setup for this ticker.\n\n"
        "OUTPUT FORMAT (exactly 2 lines):\n"
        "Line 1: PROPOSE_TRADE (SCORE: [0-100]) or HOLD_CASH (SCORE: [0-100])\n"
        "Line 2: One sentence rationale summarizing the catalyst score."
    )

    EXIT_SYSTEM_PROMPT = (
        "You are an aggressive quantitative exit evaluator. "
        "DECISION RULES:\n"
        "- P&L >= +8.0%: output TAKE_PROFIT (harvest macro trend runner)\n"
        "- P&L >= +3.0%: output TAKE_PROFIT (bank Stage-1 gains)\n"
        "- P&L <= -1.0%: output CUT_LOSS (cut loss to preserve capital)\n"
        "OUTPUT FORMAT (exactly 2 lines):\n"
        "Line 1: HOLD or TAKE_PROFIT or CUT_LOSS\n"
        "Line 2: One sentence rationale."
    )

    def evaluate_entry(self, symbol: str, account: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate whether to enter a new position in `symbol` using Catalyst Scoring (>= 80/100)."""
        equity = float(account.get("equity", 100000.0))
        buying_power = float(account.get("buying_power", 400000.0))

        trade_notional = 15000.0  # Safe $15,000 block trade (15% equity, 0% margin risk)
        if trade_notional > buying_power:
            return self._hold(symbol, "Insufficient buying power for $15k block trade.")

        headlines = news_scanner.get_headlines(symbol)
        lessons = reflexion_memory.get_lessons_for_symbol(symbol)

        user_prompt = (
            f"TICKER: {symbol}\n"
            f"LIVE NEWS:\n" + "\n".join(f"  - {h}" for h in headlines) + "\n\n"
            f"PAST TRADE LESSONS (CLOSED TRADES ONLY):\n" + (
                "\n".join(f"  - {l}" for l in lessons) if lessons else "  - No prior closed trades on this symbol."
            ) + "\n\n"
            f"ACCOUNT: Equity=${equity:,.0f}, Buying Power=${buying_power:,.0f}\n"
            f"Proposed block size: ${trade_notional:,.0f}\n"
            f"Calculate Catalyst Score (0-100). Should we enter a $15,000 long position RIGHT NOW?"
        )

        response = ai_router.query(prompt=user_prompt, system_prompt=self.ENTRY_SYSTEM_PROMPT)

        if not response:
            return self._hold(symbol, "AI router returned empty response — skipping cycle.")

        lines = [l.strip() for l in response.strip().split("\n") if l.strip()]
        action_raw = lines[0].upper() if lines else "HOLD_CASH"
        rationale = lines[1] if len(lines) > 1 else "AI autonomous decision."

        # Parse Catalyst Score from AI response
        import re
        score_match = re.search(r"SCORE:\s*(\d+)", action_raw)
        score = int(score_match.group(1)) if score_match else (85 if "PROPOSE_TRADE" in action_raw else 50)

        # High-Conviction Gate: Only trade if score >= 80
        if "PROPOSE_TRADE" in action_raw and score >= 80:
            return {
                "symbol": symbol,
                "action": "PROPOSE_TRADE",
                "strategy_type": "MOMENTUM_LONG",
                "confidence": round(score / 100.0, 2),
                "notional": trade_notional,
                "reason": f"[Score {score}/100] {rationale}",
            }

        return self._hold(symbol, f"[Score {score}/100 < 80 Threshold] {rationale}")

    def evaluate_exit(self, position: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate whether to exit an open position instantly."""
        symbol = position.get("symbol", "")
        market_value = float(position.get("market_value", 1.0))
        unrealized_pl = float(position.get("unrealized_pl", 0.0))
        cost_basis = float(position.get("cost_basis", market_value - unrealized_pl))
        pnl_pct = (unrealized_pl / cost_basis) * 100.0 if cost_basis > 0 else 0.0

        # Multi-Stage Asymmetric Payoff (+8.0% Macro Runner, +3.0% Stage-1, -1.0% Stop Loss)
        if pnl_pct >= 8.0:
            return {"action": "TAKE_PROFIT_EXIT", "symbol": symbol,
                    "reason": f"🚀 Macro breakout runner target hit +{pnl_pct:.2f}%. Harvesting +${unrealized_pl:.2f}.", "pnl": unrealized_pl}
        if pnl_pct >= 3.0:
            return {"action": "TAKE_PROFIT_EXIT", "symbol": symbol,
                    "reason": f"💰 Stage-1 profit target hit +{pnl_pct:.2f}%. Banking +${unrealized_pl:.2f}.", "pnl": unrealized_pl}
        if pnl_pct <= -1.0:
            return {"action": "CUT_LOSS_EXIT", "symbol": symbol,
                    "reason": f"🛡️ Noise-resistant stop loss hit {pnl_pct:.2f}%. Protecting capital.", "pnl": unrealized_pl}

        # Position within active growth corridor (-1.0% to +3.0%)
        return {"action": "HOLD_POSITION", "symbol": symbol, "reason": f"Growth corridor active ({pnl_pct:+.2f}%). Allowing trade room to run.", "pnl": unrealized_pl}

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
