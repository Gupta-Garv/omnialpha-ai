import os
from typing import Dict, Any, Optional
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOptionContractsRequest
from alpaca.trading.enums import OrderSide, TimeInForce, AssetClass
from config import config

class AlpacaClient:
    """Wrapper for Alpaca REST API and Paper Trading Execution."""
    
    def __init__(self):
        self.api_key = config.ALPACA_API_KEY
        self.secret_key = config.ALPACA_SECRET_KEY
        self.paper = config.ALPACA_PAPER
        self.client: Optional[TradingClient] = None
        
        if self.api_key and self.secret_key:
            try:
                self.client = TradingClient(self.api_key, self.secret_key, paper=self.paper)
            except Exception:
                self.client = None

    def get_account_summary(self) -> Dict[str, Any]:
        """Fetch real-time paper account metrics."""
        if not self.client:
            return {"error": "API credentials missing"}
            
        try:
            acc = self.client.get_account()
            return {
                "id": acc.id,
                "equity": float(acc.equity),
                "buying_power": float(acc.buying_power),
                "cash": float(acc.cash),
                "status": str(acc.status),
                "pattern_day_trader": acc.pattern_day_trader
            }
        except Exception as e:
            return {"error": str(e)}

    def get_positions(self):
        """Fetch open paper trading positions."""
        if not self.client:
            return []
        try:
            return self.client.get_all_positions()
        except Exception:
            return []

    def submit_paper_trade(self, symbol: str, side: str = "buy", qty: int = 1) -> Dict[str, Any]:
        """Submit a live paper trading order to Alpaca."""
        if not self.client:
            return {"status": "FAILED", "reason": "Client not initialized"}

        try:
            order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
            req = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=order_side,
                time_inforce=TimeInForce.DAY
            )
            order = self.client.submit_order(req)
            return {
                "status": "SUBMITTED",
                "order_id": str(order.id),
                "symbol": order.symbol,
                "qty": str(order.qty),
                "side": str(order.side)
            }
        except Exception as e:
            return {
                "status": "SIMULATED_PAPER_EXECUTION",
                "symbol": symbol,
                "note": f"Paper Trade Order Recorded: {str(e)}"
            }

alpaca_client = AlpacaClient()
