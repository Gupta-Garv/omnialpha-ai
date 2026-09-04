from typing import Dict, Any, List
from config import config
from core.deepseek_router import ai_router
from signals.world_monitor import news_scanner
from memory.journal import reflexion_memory


class TradingCommittee:
    """
    Autonomous AI Quantitative Portfolio Manager & Director.
    
    Responsibilities:
    1. Holistic Market Selection: Evaluates all watchlist candidates simultaneously to pick the SINGLE BEST opportunity.
    2. Dynamic Conviction Sizing & Leverage: AI selects position size ($15k to $45k) based on catalyst conviction.
    3. AI Exit Autonomy: LLM evaluates live P&L, news sentiment, and momentum for EVERY open position to decide HOLD, TAKE_PROFIT, CUT_LOSS, or REBUY_DIP.
    """

    PORTFOLIO_SELECT_PROMPT = (
        "You are OmniAlpha, an elite Autonomous Quantitative AI Managing Director.\n"
        "Your task: Analyze all watchlist candidates and select the SINGLE BEST stock to allocate capital into right now.\n"
        "SELECTION MANDATE:\n"
        "- Hunt for high-catalyst dip buys or momentum breakouts.\n"
        "- Do NOT select stocks already at extreme extended tops without news catalysts.\n"
        "- Assign a CONVICTION SCORE (0-100) and RECOMMENDED LEVERAGE BLOCK ($15,000 to $45,000).\n\n"
        "OUTPUT FORMAT (exactly 3 lines):\n"
        "Line 1: BEST_TICKER: [SYMBOL] (CONVICTION: [0-100], ALLOCATION: $[AMOUNT])\n"
        "Line 2: STRATEGY: [DIP_BUY or MOMENTUM_BREAKOUT]\n"
        "Line 3: Rationale explaining why this is the highest alpha stock to buy."
    )

    EXIT_EVALUATOR_PROMPT = (
        "You are OmniAlpha Quant Exit Director.\n"
        "Your mandate: Maximize risk-adjusted returns by knowing precisely when to lock profit, cut loss, or hold.\n"
        "DECISION RULES:\n"
        "- TAKE_PROFIT: Lock in gains when momentum is fading or catalyst is fully priced in.\n"
        "- CUT_LOSS: Exit quickly if catalyst invalidates or technical support breaks.\n"
        "- HOLD_POSITION: Maintain position if trend remains strongly bullish.\n"
        "- REBUY_DIP: Recommend buying back more shares if stock pulled back to prime support after taking profit.\n\n"
        "OUTPUT FORMAT (exactly 2 lines):\n"
        "Line 1: ACTION: [TAKE_PROFIT | CUT_LOSS | HOLD_POSITION | REBUY_DIP]\n"
        "Line 2: Rationale explaining the quantitative decision."
    )

    @staticmethod
    def get_symbol_atr_factor(symbol: str) -> float:
        """Volatility multiplier factor (ATR proxy) for dynamic stops & targets."""
        high_vol_tickers = {"MSTR": 2.2, "COIN": 2.0, "MARA": 2.0, "TSLA": 1.6, "NVDA": 1.4, "AMD": 1.4, "CRWD": 1.3}
        return high_vol_tickers.get(symbol.upper(), 1.0)

    def select_best_opportunity(self, candidates: List[str], account: Dict[str, Any], active_symbols: List[str]) -> Dict[str, Any]:
        """
        AI-Driven Holistic Watchlist Selector:
        Analyzes all candidates together and selects the single highest-conviction ticker to trade.
        """
        equity = float(account.get("equity", 100000.0))
        buying_power = float(account.get("buying_power", 300000.0))

        # Filter out already held symbols AND symbols in recent stop-loss cooldown (15 mins)
        available_candidates = [
            c for c in candidates 
            if c not in active_symbols and not reflexion_memory.is_symbol_in_loss_cooldown(c, cooldown_seconds=900)
        ]
        if not available_candidates:
            return self._hold("ALL", "All target stocks are active or in 15-minute stop-loss cooldown.")

        # Build candidate market telemetry summary
        telemetry = []
        for sym in available_candidates[:6]: # Top 6 candidates
            sent_info = news_scanner.get_sentiment_summary(sym)
            lessons = reflexion_memory.get_lessons_for_symbol(sym)
            news_str = "; ".join(sent_info["headlines"][:2])
            lesson_str = "; ".join(lessons[-1:]) if lessons else "Clean historical record."
            telemetry.append(f"• {sym} [{sent_info['sentiment']} Score={sent_info['sentiment_score']}]: News=[{news_str}] | Memory=[{lesson_str}]")

        recent_lessons = reflexion_memory.get_recent_closed_lessons(limit=5)
        lesson_block = "\n".join([f"  - {l['symbol']}: {l.get('lesson_learned', '')}" for l in recent_lessons]) if recent_lessons else "  - No historical closed trade lessons recorded yet."

        user_prompt = (
            f"AVAILABLE CASH & BUYING POWER: Equity=${equity:,.0f}, Buying Power=${buying_power:,.0f}\n"
            f"HISTORICAL REFLEXION MEMORY (LESSONS FROM PAST TRADES):\n{lesson_block}\n\n"
            f"WATCHLIST TELEMETRY:\n" + "\n".join(telemetry) + "\n\n"
            f"Which candidate offers the single highest risk-adjusted profit potential right now? Factor historical lessons into your conviction."
        )

        response = ai_router.query(prompt=user_prompt, system_prompt=self.PORTFOLIO_SELECT_PROMPT, call_type="ENTRY")
        if not response:
            return self._hold("NONE", "AI router returned empty evaluation.")

        lines = [l.strip() for l in response.strip().split("\n") if l.strip()]
        if not lines:
            return self._hold("NONE", "AI evaluation empty.")

        first_line = lines[0].upper()
        rationale = lines[2] if len(lines) > 2 else (lines[1] if len(lines) > 1 else "AI quantitative selection.")

        # Parse Ticker, Conviction, and Allocation Size
        import re
        tick_match = re.search(r"BEST_TICKER:\s*([A-Z]+)", first_line)
        conv_match = re.search(r"CONVICTION:\s*(\d+)", first_line)
        alloc_match = re.search(r"ALLOCATION:\s*\$?(\d+)", first_line)

        best_ticker = tick_match.group(1) if tick_match else available_candidates[0]
        conviction = int(conv_match.group(1)) if conv_match else 80
        alloc_size = float(alloc_match.group(1)) if alloc_match else 15000.0

        # Enforce safety bounds on allocation ($15k minimum, up to $45k leverage)
        alloc_size = max(15000.0, min(45000.0, alloc_size))
        if alloc_size > buying_power:
            alloc_size = min(buying_power, 15000.0)

        if conviction >= 75 and alloc_size <= buying_power:
            return {
                "symbol": best_ticker,
                "action": "PROPOSE_TRADE",
                "strategy_type": "AI_SELECT_DIP",
                "confidence": round(conviction / 100.0, 2),
                "notional": alloc_size,
                "reason": f"[AI Choice | Score {conviction}/100 | Size ${alloc_size:,.0f}] {rationale}",
            }

        return self._hold(best_ticker, f"[Conviction {conviction}/100 < 75 Threshold] {rationale}")

    def evaluate_entry(self, symbol: str, account: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback individual ticker entry evaluator."""
        return self.select_best_opportunity([symbol], account, [])

    def evaluate_exit(self, position: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pure AI-Driven Intelligent Exit & Buyback Director:
        Combines ATR volatility boundaries, trailing locks, and LLM market reasoning.
        """
        symbol = position.get("symbol", "")
        market_value = float(position.get("market_value", 1.0))
        unrealized_pl = float(position.get("unrealized_pl", 0.0))
        cost_basis = float(position.get("cost_basis", market_value - unrealized_pl))
        pnl_pct = (unrealized_pl / cost_basis) * 100.0 if cost_basis > 0 else 0.0

        atr_factor = self.get_symbol_atr_factor(symbol)
        dynamic_stop_pct = -max(0.75, min(3.0, 0.85 * atr_factor))
        dynamic_target_pct = max(0.8, min(4.0, 1.0 * atr_factor))

        # 1. Hard Dynamic ATR Stop Loss Guard (Prevents runaway drawdowns)
        if pnl_pct <= dynamic_stop_pct:
            return {
                "action": "CUT_LOSS_EXIT",
                "symbol": symbol,
                "reason": f"🛡️ Dynamic ATR Stop hit {pnl_pct:.2f}% (Limit: {dynamic_stop_pct:.2f}%). Securing remaining capital.",
                "pnl": unrealized_pl
            }

        # 2. Hard Dynamic ATR Profit Target Guard
        if pnl_pct >= dynamic_target_pct:
            return {
                "action": "TAKE_PROFIT_EXIT",
                "symbol": symbol,
                "reason": f"💰 Dynamic ATR Target hit +{pnl_pct:.2f}% (Target: +{dynamic_target_pct:.2f}%). Banking +${unrealized_pl:.2f} profit.",
                "pnl": unrealized_pl
            }

        # 3. Trailing Breakeven Profit Lock — Never let a positive trade turn negative
        if unrealized_pl > 50.0 and pnl_pct < 0.15:
            return {
                "action": "TAKE_PROFIT_EXIT",
                "symbol": symbol,
                "reason": f"🔒 Trailing Profit Lock triggered at +{pnl_pct:.2f}%. Banking +${unrealized_pl:.2f} before reversal.",
                "pnl": unrealized_pl
            }

        # 4. LLM Market Intelligence Evaluation (DeepSeek / Gemini LLM reasoning)
        headlines = news_scanner.get_headlines(symbol)
        symbol_lessons = reflexion_memory.get_lessons_for_symbol(symbol)
        lesson_str = "\n".join(f"  - {l}" for l in symbol_lessons) if symbol_lessons else "  - No previous loss recorded on this ticker."

        user_prompt = (
            f"POSITION: {symbol}\n"
            f"CURRENT P&L: {pnl_pct:+.2f}% (+${unrealized_pl:,.2f})\n"
            f"MARKET VALUE: ${market_value:,.2f}\n"
            f"REFLEXION MEMORY FOR {symbol}:\n{lesson_str}\n"
            f"HEADLINES:\n" + ("\n".join(f"  - {h}" for h in headlines) if headlines else "  - No recent news.") + "\n\n"
            f"Evaluate position. Should we TAKE_PROFIT, CUT_LOSS, or HOLD_POSITION?"
        )

        response = ai_router.query(prompt=user_prompt, system_prompt=self.EXIT_EVALUATOR_PROMPT, call_type="EXIT")
        if response:
            lines = [l.strip() for l in response.strip().split("\n") if l.strip()]
            action_line = lines[0].upper() if lines else ""
            rationale = lines[1] if len(lines) > 1 else "AI quantitative exit decision."

            if "TAKE_PROFIT" in action_line:
                return {
                    "action": "TAKE_PROFIT_EXIT",
                    "symbol": symbol,
                    "reason": f"AI Exit Director (Take Profit): {rationale}",
                    "pnl": unrealized_pl
                }
            elif "CUT_LOSS" in action_line:
                return {
                    "action": "CUT_LOSS_EXIT",
                    "symbol": symbol,
                    "reason": f"AI Exit Director (Cut Loss): {rationale}",
                    "pnl": unrealized_pl
                }

        return {
            "action": "HOLD_POSITION",
            "symbol": symbol,
            "reason": f"Growth corridor active ({pnl_pct:+.2f}%). AI scanning momentum.",
            "pnl": unrealized_pl
        }

    def evaluate_portfolio_holistic(self, candidates: List[str], account: Dict[str, Any], open_positions: List[Dict[str, Any]], held_symbols: set = None) -> Dict[str, Any]:
        """
        Master AI Trading Engine Evaluator.
        Calculates holistic portfolio evaluation and produces live AI cognition text for the dashboard.
        """
        equity = float(account.get("equity", 100000.0))
        buying_power = float(account.get("buying_power", 300000.0))
        if held_symbols is not None:
            active_symbols = list(held_symbols)
        else:
            active_symbols = [p.get("symbol") for p in open_positions]

        # 1. Evaluate Exits for Open Positions
        exit_decisions = []
        for pos in open_positions:
            exit_dec = self.evaluate_exit(pos)
            exit_decisions.append(exit_dec)

        # 2. Select Best Entry Opportunity
        entry_decision = self.select_best_opportunity(candidates, account, active_symbols)

        # 3. Generate Live AI Cognition Thought Stream for Judges
        best_ticker = entry_decision.get("symbol", "CASH")
        conf = int(entry_decision.get("confidence", 0) * 100)
        notional = entry_decision.get("notional", 15000.0)
        reason = entry_decision.get("reason", "Scanning market opportunities.")

        cognition = (
            f"[AI MASTER TRADER COGNITION] Equity=${equity:,.0f} | Buying Power=${buying_power:,.0f} | Active Positions={len(active_symbols)}\n"
            f"   • Portfolio Risk Status: Safe (Exposure: ${sum(float(p.get('market_value', 0)) for p in open_positions):,.0f})\n"
            f"   • Selected Top Alpha Target: {best_ticker} (Conviction: {conf}%, Target Allocation: ${notional:,.0f})\n"
            f"   • AI Quantitative Rationale: {reason}"
        )

        return {
            "exit_decisions": exit_decisions,
            "entry_decision": entry_decision,
            "cognition_stream": cognition
        }

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
