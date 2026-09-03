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
                mkt_val = float(p.market_value) if p.market_value else 0.0
                unreal_pl = float(p.unrealized_pl) if p.unrealized_pl else 0.0
                cost_b = float(p.cost_basis) if getattr(p, "cost_basis", None) else (mkt_val - unreal_pl)
                formatted.append({
                    "symbol": p.symbol,
                    "qty": str(p.qty),
                    "current_price": float(p.current_price) if p.current_price else 0.0,
                    "market_value": mkt_val,
                    "unrealized_pl": unreal_pl,
                    "cost_basis": cost_b,
                    "avg_entry_price": float(p.avg_entry_price) if getattr(p, "avg_entry_price", None) else 0.0,
                    "unrealized_plpc": (unreal_pl / cost_b * 100.0) if cost_b > 0 else 0.0,
                })
            return formatted
        except Exception:
            return []

    def get_pending_order_symbols(self) -> List[str]:
        """Fetch list of tickers with currently open/pending orders."""
        if not self.client:
            return []
        try:
            open_orders = self.client.get_orders()
            return [o.symbol for o in open_orders if hasattr(o, "symbol")]
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

            # Check if an open order already exists for this symbol to prevent buying power lockup
            try:
                open_orders = self.client.get_orders()
                for o in open_orders:
                    if o.symbol == symbol and str(o.side).lower().endswith(side.lower()):
                        print(f"  [ALPACA] Order already pending for {symbol} ({o.side}), skipping duplicate.")
                        return {"status": "SKIPPED", "reason": "Order already pending"}
            except Exception:
                pass
            
            # Default to institutional block sizing if neither qty nor notional is specified
            if qty is None and notional is None:
                qty = 50

            if qty is not None:
                req = MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=order_side,
                    time_in_force=TimeInForce.DAY
                )
            else:
                req = MarketOrderRequest(
                    symbol=symbol,
                    notional=notional,
                    side=order_side,
                    time_in_force=TimeInForce.DAY
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
            print(f"  [ALPACA ERROR] {symbol} Order failed: {e}")
            return {
                "status": "FAILED",
                "symbol": symbol,
                "error": str(e)
            }

    def close_position(self, symbol: str) -> Dict[str, Any]:
        """Close an individual ticker position."""
        if not self.client:
            return {"status": "FAILED", "reason": "Client not initialized"}
        try:
            res = self.client.close_position(symbol)
            return {"status": "SUCCESS", "message": f"Position {symbol} closed."}
        except Exception as e:
            return {"status": "FAILED", "reason": str(e)}

alpaca_client = AlpacaClient()
