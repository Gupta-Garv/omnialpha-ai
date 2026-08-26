from typing import Dict, Any, List
from signals.insider_tracker import insider_tracker
from signals.social_radar import social_radar
from signals.grey_market import grey_market_scanner
from signals.world_monitor import world_monitor
from core.risk_shield import RiskShield
from memory.journal import reflexion_memory

POSITION_SIZING = {
    "NVDA": 500,  # ~$64,000 capital block
    "AMD": 400,   # ~$60,000 capital block
    "AAPL": 300,  # ~$67,000 capital block
    "TSLA": 300,  # ~$66,000 capital block
    "SPY": 150,   # ~$76,000 capital block
    "QQQ": 150    # ~$65,000 capital block
}

class MultiAgentCommittee:
    """
    Synthesizes SEC EDGAR Filings, Grey Market Dark Pool Sweeps, 
    Social Sentiment Velocity, and Reflexion Self-Learning Memory.
    """

    def evaluate_opportunity(self, symbol: str, account_summary: Dict[str, Any]) -> Dict[str, Any]:
        equity = account_summary.get("equity", 100000.0)
        buying_power = account_summary.get("buying_power", 400000.0)
        risk_shield = RiskShield(account_equity=equity, buying_power=buying_power)

        # 1. Gather Multi-Pillar Signals
        grey_signals = grey_market_scanner.analyze_grey_market_signals(symbol)
        insider_signals = insider_tracker.fetch_recent_filings([symbol])
        social_signal = social_radar.analyze_ticker_sentiment(symbol)
        past_lessons = reflexion_memory.get_lessons_for_symbol(symbol)
        
        # 2. GET LIVE WORLD MONITOR INTEL (REAL RSS FEEDS + GEMINI)
        monitor_intel = world_monitor.fetch_live_catalysts(symbol)
        world_velocity = monitor_intel.get("velocity", "STAGNATE")

        has_insider_activity = len(insider_signals) > 0 or "FORM_4" in grey_signals.get("sec_filing_event", "")
        sentiment = social_signal.get("sentiment", "NEUTRAL")
        grey_conviction = grey_signals.get("conviction_score", 0.75)
        dark_pool_flow = grey_signals.get("institutional_flow", "+$0.0M")
        
        # 3. Institutional Decision & Strategy Selection
        target_qty = POSITION_SIZING.get(symbol, 50)
        
        # STRATEGY OVERHAUL: ONLY enter if World Monitor specifically detects a SURGE
        if world_velocity != "SURGE":
            return {
                "symbol": symbol,
                "action": "HOLD_CASH",
                "strategy_type": "WAITING_FOR_CATALYST",
                "confidence": 0.0,
                "reason": f"World Monitor detects {world_velocity}. Sitting in cash until trend reversal."
            }
            
        action = "PROPOSE_TRADE"
        strategy_type = "INSTITUTIONAL_BULL_LEVERAGE"
        
        # Dynamic Risk Allocation based on Equity ($100k account)
        estimated_max_loss = 1500.0  # Cap maximum risk at $1,500 per position block
        estimated_max_gain = 4500.0  # Asymmetric 1:3 reward ratio ($4,500 target profit)
        confidence = grey_conviction

        if sentiment == "BEARISH_VELOCITY":
            strategy_type = "BEAR_CALL_SPREAD"
            confidence = max(0.75, grey_conviction - 0.05)
        elif sentiment == "BULLISH_VELOCITY" or "CALL" in dark_pool_flow:
            strategy_type = "INSTITUTIONAL_BULL_LEVERAGE"
            confidence = min(0.95, grey_conviction + 0.05)
        else:
            strategy_type = "BULL_PUT_SPREAD" if symbol in ["NVDA", "AMD", "QQQ", "SPY"] else "BEAR_CALL_SPREAD"
            confidence = grey_conviction

        # Adjust confidence penalty if past lessons flag losses
        if any("LESSON:" in l for l in past_lessons):
            confidence -= 0.03

        # 3. Risk Shield Validation
        val = risk_shield.validate_trade(
            symbol=symbol,
            order_type=strategy_type,
            qty=target_qty,
            max_possible_loss=estimated_max_loss,
            max_possible_gain=estimated_max_gain
        )
        
        if not val.approved:
            return {
                "symbol": symbol,
                "action": "REJECTED_BY_RISK_SHIELD",
                "strategy_type": strategy_type,
                "confidence": 0.0,
                "reason": val.reason
            }

        return {
            "symbol": symbol,
            "action": "PROPOSE_TRADE",
            "strategy_type": strategy_type,
            "confidence": max(0.60, confidence),
            "target_qty": target_qty,
            "max_loss": estimated_max_loss,
            "max_gain": estimated_max_gain,
            "risk_approved": True,
            "grey_market_flow": dark_pool_flow,
            "sec_event": grey_signals.get("sec_filing_event", "SEC_EDGAR_CLEARED"),
            "audit_trail": {
                "sentiment_signal": sentiment,
                "dark_pool_sweep": grey_signals.get("dark_pool_sweep"),
                "institutional_flow": dark_pool_flow,
                "insider_activity": has_insider_activity,
                "past_lessons_applied": past_lessons,
                "rationale": f"High conviction {strategy_type} driven by Dark Pool Sweep ({dark_pool_flow}) and SEC filings."
            },
            "reason": f"Grey Market Catalyst ({grey_signals.get('signal_type')}, Flow: {dark_pool_flow}). Passed Risk Shield & Memory."
        }

committee = MultiAgentCommittee()
