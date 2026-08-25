from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOptionContractsRequest
from alpaca.trading.enums import ContractType
from config import config

class OptionFlowScanner:
    """Scans Alpaca Option Chains and filters contracts for defined-risk spreads."""

    def __init__(self):
        self.client = None
        if config.ALPACA_API_KEY and config.ALPACA_SECRET_KEY:
            try:
                self.client = TradingClient(config.ALPACA_API_KEY, config.ALPACA_SECRET_KEY, paper=config.ALPACA_PAPER)
            except Exception:
                self.client = None

    def get_option_chain_summary(self, underlying_symbol: str) -> Dict[str, Any]:
        """Fetch active option contracts for an underlying ticker."""
        if not self.client:
            return {"symbol": underlying_symbol, "contracts_found": 0, "status": "NO_API_KEYS"}

        try:
            # Request near-term option contracts (expiring within 30 days)
            req = GetOptionContractsRequest(
                underlying_symbol=[underlying_symbol],
                expiration_date_gte=datetime.now().date(),
                expiration_date_lte=(datetime.now() + timedelta(days=30)).date(),
                limit=20
            )
            res = self.client.get_option_contracts(req)
            contracts = res.option_contracts if res and res.option_contracts else []
            
            call_contracts = [c for c in contracts if c.type == ContractType.CALL]
            put_contracts = [c for c in contracts if c.type == ContractType.PUT]

            sample_call = call_contracts[0].symbol if call_contracts else None
            sample_put = put_contracts[0].symbol if put_contracts else None

            return {
                "symbol": underlying_symbol,
                "total_contracts": len(contracts),
                "calls_found": len(call_contracts),
                "puts_found": len(put_contracts),
                "sample_call_symbol": sample_call,
                "sample_put_symbol": sample_put,
                "status": "ACTIVE_CHAIN_RETRIEVED"
            }
        except Exception as e:
            return {
                "symbol": underlying_symbol,
                "total_contracts": 0,
                "status": f"OPTION_CHAIN_QUERY_NOTE: {str(e)}"
            }

option_flow_scanner = OptionFlowScanner()
