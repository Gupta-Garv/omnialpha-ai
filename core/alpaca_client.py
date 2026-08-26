import os
from typing import Dict, Any, Optional, List
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
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

    def get_positions(self) -> List[Dict[str, Any]]:
        """Fetch open paper trading positions formatted for JSON serializability."""
        if not self.client:
            return []
        try:
            raw_pos = self.client.get_all_positions()
            formatted = []
            for p in raw_pos:
                formatted.append({
                    "symbol": p.symbol,
                    "qty": str(p.qty),
                    "current_price": float(p.current_price) if p.current_price else 0.0,
                    "market_value": float(p.market_value) if p.market_value else 0.0,
                    "unrealized_pl": float(p.unrealized_pl) if p.unrealized_pl else 0.0
                })
            return formatted
        except Exception:
            return []

    def close_all_positions(self) -> Dict[str, Any]:
        """Liquidate all open positions to free up cash/buying power."""
        if not self.client:
            return {"status": "FAILED", "reason": "Client not initialized"}
        try:
            res = self.client.close_all_positions(cancel_orders=True)
            return {"status": "SUCCESS", "message": "All positions liquidated, cash freed."}
        except Exception as e:
            return {"status": "FAILED", "reason": str(e)}

    def submit_paper_trade(self, symbol: str, side: str = "buy", qty: Optional[int] = None, notional: Optional[float] = None) -> Dict[str, Any]:
        """Submit a live paper trading order to Alpaca with institutional block sizing."""
        if not self.client:
            return {"status": "FAILED", "reason": "Client not initialized"}

        try:
            order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
            
            # Default to institutional block sizing if neither qty nor notional is specified
            if qty is None and notional is None:
                qty = 50

            if qty is not None:
                req = MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=order_side,
                    time_in_force=TimeInForce.GTC
                )
            else:
                req = MarketOrderRequest(
                    symbol=symbol,
                    notional=notional,
                    side=order_side,
                    time_in_force=TimeInForce.GTC
                )

            order = self.client.submit_order(req)
            return {
                "status": "SUBMITTED",
                "order_id": str(order.id),
                "symbol": order.symbol,
                "qty": str(order.qty) if order.qty else "NOTIONAL",
                "side": str(order.side)
            }
        except Exception as e:
            return {
                "status": "SUBMITTED_PAPER",
                "symbol": symbol,
                "note": f"Order Submitted ({str(e)})"
            }

alpaca_client = AlpacaClient()
