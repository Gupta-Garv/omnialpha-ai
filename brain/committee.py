from typing import Dict, Any, List
from signals.insider_tracker import insider_tracker
from signals.social_radar import social_radar
from signals.option_flow import option_flow_scanner
from core.risk_shield import RiskShield

class MultiAgentCommittee:
    """Synthesizes Insider, Social, and Option Market Data signals into defined-risk decisions."""

    def evaluate_opportunity(self, symbol: str, account_summary: Dict[str, Any]) -> Dict[str, Any]:
        equity = account_summary.get("equity", 100000.0)
        buying_power = account_summary.get("buying_power", 400000.0)
        risk_shield = RiskShield(account_equity=equity, buying_power=buying_power)

        # 1. Gather Signals
        insider_signals = insider_tracker.fetch_recent_filings([symbol])
        social_signal = social_radar.analyze_ticker_sentiment(symbol)
        option_chain = option_flow_scanner.get_option_chain_summary(symbol)

        has_insider_activity = len(insider_signals) > 0
        sentiment = social_signal.get("sentiment", "NEUTRAL")
        contracts_available = option_chain.get("total_contracts", 0) > 0

        action = "HOLD"
        strategy_type = "NONE"
        estimated_max_loss = 250.0  # $250 max loss per spread contract
        estimated_max_gain = 500.0  # $500 max profit
        confidence = 0.50

        # 2. Decision Logic
        if sentiment == "BULLISH_VELOCITY" or (has_insider_activity and sentiment != "BEARISH_VELOCITY"):
            action = "PROPOSE_TRADE"
            strategy_type = "BULL_PUT_SPREAD"
            confidence = 0.85 if has_insider_activity else 0.75
        elif sentiment == "BEARISH_VELOCITY":
            action = "PROPOSE_TRADE"
            strategy_type = "BEAR_CALL_SPREAD"
            confidence = 0.78

        # 3. Risk Shield Validation
        if action == "PROPOSE_TRADE":
            if not contracts_available:
                return {
                    "symbol": symbol,
                    "action": "HOLD",
                    "reason": "Option contracts unavailable for underlying."
                }

            val = risk_shield.validate_trade(
                symbol=symbol,
                order_type=strategy_type,
                qty=1,
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
                "confidence": confidence,
                "max_loss": estimated_max_loss,
                "max_gain": estimated_max_gain,
                "risk_approved": True,
                "audit_trail": {
                    "sentiment_signal": sentiment,
                    "insider_activity": has_insider_activity,
                    "sample_option_symbol": option_chain.get("sample_call_symbol"),
                    "rationale": f"High probability {strategy_type} based on {sentiment} velocity & SEC filings."
                },
                "reason": f"Signals aligned ({sentiment}, Insiders: {has_insider_activity}). Passed Risk Shield."
            }

        return {
            "symbol": symbol,
            "action": "HOLD",
            "reason": "Insufficient pre-catalyst signal edge."
        }

committee = MultiAgentCommittee()
