from dataclasses import dataclass
from typing import Optional
from config import config

@dataclass
class TradeValidationResult:
    approved: bool
    max_loss: float
    max_gain: float
    reason: str

class RiskShield:
    """Hardcoded Quantitative Risk Shield — Enforces unbreakable trading limits."""
    
    def __init__(self, account_equity: float, buying_power: float):
        self.account_equity = account_equity
        self.buying_power = buying_power

    def validate_trade(
        self, 
        symbol: str, 
        order_type: str, 
        qty: int, 
        max_possible_loss: float,
        max_possible_gain: float
    ) -> TradeValidationResult:
        
        # Rule 1: Buying Power Check
        if max_possible_loss > self.buying_power:
            return TradeValidationResult(
                approved=False,
                max_loss=max_possible_loss,
                max_gain=max_possible_gain,
                reason=f"REJECTED: Insufficient buying power (${max_possible_loss:.2f} required, ${self.buying_power:.2f} available)"
            )
            
        # Rule 2: Max Single Position Risk Limit (2% of equity = $2,000 on $100k account)
        max_allowed_risk = self.account_equity * (config.MAX_POSITION_RISK_PCT / 100.0)
        if max_possible_loss > max_allowed_risk:
            return TradeValidationResult(
                approved=False,
                max_loss=max_possible_loss,
                max_gain=max_possible_gain,
                reason=f"REJECTED: Risk (${max_possible_loss:.2f}) exceeds {config.MAX_POSITION_RISK_PCT}% position cap (${max_allowed_risk:.2f})"
            )

        # Rule 3: Defined Risk Requirement
        if max_possible_loss <= 0:
            return TradeValidationResult(
                approved=False,
                max_loss=max_possible_loss,
                max_gain=max_possible_gain,
                reason="REJECTED: Trade must have a mathematically defined maximum loss."
            )

        return TradeValidationResult(
            approved=True,
            max_loss=max_possible_loss,
            max_gain=max_possible_gain,
            reason=f"APPROVED: Trade meets all risk guardrails (Risk: ${max_possible_loss:.2f} <= Cap: ${max_allowed_risk:.2f})"
        )

risk_shield = RiskShield(account_equity=100000.0, buying_power=400000.0)
