# Comprehensive Alpaca Documentation Reference

This file contains the consolidated documentation provided for Alpaca's platform, Trading API, Market Data API, Alpaca CLI, Trading MCP Server, Broker API, and SDKs.

---

## 1. Overview & Architecture

### Welcome to Alpaca
Alpaca offers API-first solutions to connect applications and build algorithms for US stocks, ETFs, Options, and Cryptocurrencies.

* **Live Trading API Base URL:** `https://api.alpaca.markets`
* **Paper Trading API Base URL:** `https://paper-api.alpaca.markets`
* **Market Data API Base URL:** `https://data.alpaca.markets`
* **Live Broker API Base URL:** `https://broker-api.alpaca.markets`
* **Sandbox Broker API Base URL:** `https://broker-api.sandbox.alpaca.markets`
* **Documentation MCP Endpoint (HTTP):** `https://docs.alpaca.markets/mcp?project=alpaca-us`

```json
{
  "mcpServers": {
    "alpaca-us": {
      "type": "http",
      "url": "https://docs.alpaca.markets/mcp?project=alpaca-us"
    }
  }
}
```
* **Command to add via CLI:** `npx add-mcp "https://docs.alpaca.markets/mcp?project=alpaca-us"`

### API Types & Protocol
* **REST API:** Primary synchronous interaction for accounts, orders, positions, and market data.
* **WebSocket & SSE (Server-Sent Events):** Real-time streaming for trade updates (`trade_updates`), order execution events, and real-time market data bars/quotes.
* **Backwards Compatibility:** Appending parameters/fields is backwards compatible. Breaking changes involve version bumps (e.g., `/v1` to `/v2`).

---

## 2. Authentication

### Legacy Headers (Trading API & Market Data)
Pass API credentials using HTTP Headers:
* `APCA-API-KEY-ID: {YOUR_API_KEY_ID}`
* `APCA-API-SECRET-KEY: {YOUR_API_SECRET_KEY}`

Alternatively, HTTP Basic Authentication can be used (Key ID as username, Secret Key as password).

### Client Credentials Flow (OAuth2 / Token-based)
Used primarily for Broker API and hosted integrations:
```bash
POST https://authx.alpaca.markets/v1/oauth2/token
Headers: Content-Type: application/x-www-form-urlencoded
Body: grant_type=client_credentials&client_id={YOUR_CLIENT_ID}&client_secret={YOUR_CLIENT_SECRET}
```
Returns a Bearer token valid for 15 minutes (`Authorization: Bearer {TOKEN}`).

---

## 3. Official SDKs and Client Libraries

* **Python:** `alpaca-py` (PyPI: `alpaca-py`)
* **Node / JavaScript:** `@alpacahq/alpaca-trade-api` (npm)
* **.NET / C#:** `Alpaca.Markets` (NuGet)
* **Go:** `github.com/alpacahq/alpaca-trade-api-go`
* **Java:** `alpaca-java` (Maven)

---

## 4. Trading CLI (`alpaca`)

Command-line tool for direct execution, automation scripts, CI/CD, and AI agent sessions.

### Installation & Auth
```bash
# Go install
go install github.com/alpacahq/cli/cmd/alpaca@latest

# macOS Homebrew
brew install alpacahq/tap/cli

# Login via Browser / API Keys
alpaca profile login
alpaca profile login --api-key

# CI / Agent Environment Variables
export ALPACA_API_KEY=PK...
export ALPACA_SECRET_KEY=...
export ALPACA_LIVE_TRADE=false # Default is paper trading
```

### Key CLI Commands
* **Account:** `alpaca account get`, `alpaca account portfolio`, `alpaca account activity list`
* **Orders:** 
  * `alpaca order submit --symbol AAPL --side buy --qty 10 --type market`
  * `alpaca order submit --symbol AAPL --side buy --qty 10 --type limit --limit-price 185 --client-order-id "unique-id"`
  * `alpaca order submit --symbol AAPL --side buy --qty 10 --type market --dry-run`
  * `alpaca order list --status all`
  * `alpaca order cancel-all`
* **Positions:** `alpaca position list`, `alpaca position close --symbol AAPL`, `alpaca position close-all`
* **Options:**
  * `alpaca option contracts --underlying-symbol AAPL`
  * `alpaca option get --symbol-or-id <option_symbol>`
  * `alpaca data option chain --underlying-symbol AAPL`
  * `alpaca data option snapshot --symbol <option_symbol>`
  * `alpaca option exercise --symbol-or-id <option_symbol>`
* **Market Data:**
  * `alpaca data bars --symbol AAPL --start 2025-01-01 --timeframe 1Day`
  * `alpaca data snapshot --symbol AAPL`
  * `alpaca data screener most-actives`
  * `alpaca data screener movers`
  * `alpaca clock`

### Flags for Agents
* `--jq`: Internal filtering (e.g. `alpaca position list --jq '[.[] | {symbol, qty}]'`)
* `--dry-run`: Test order validation without submitting.
* `--quiet`: Suppress non-essential messages.

---

## 5. Alpaca Trading MCP Server (`alpaca-mcp-server`)

Model Context Protocol (MCP) server providing 65 tools for AI Assistants (Claude, Cursor, ChatGPT, VS Code, Gemini CLI).

### Configuration (`mcp.json`)
```json
{
  "mcpServers": {
    "alpaca": {
      "command": "uvx",
      "args": ["alpaca-mcp-server"],
      "env": {
        "ALPACA_API_KEY": "YOUR_KEY",
        "ALPACA_SECRET_KEY": "YOUR_SECRET",
        "ALPACA_PAPER_TRADE": "true",
        "ALPACA_TOOLSETS": "account,trading,stock-data,options-data,news"
      }
    }
  }
}
```

### Key Toolsets & Capabilities
* **`account`:** `get_account_info`, `get_account_config`, `get_portfolio_history`, `get_account_activities`
* **`trading`:** `place_stock_order`, `place_crypto_order`, `place_option_order`, `get_orders`, `replace_order_by_id`, `cancel_order_by_id`, `cancel_all_orders`
* **`positions`:** `get_all_positions`, `get_open_position`, `close_position`, `close_all_positions`, `exercise_options_position`
* **`options-data`:** `get_option_bars`, `get_option_trades`, `get_option_latest_quote`, `get_option_snapshot` (includes Greeks $\Delta, \Gamma, \Theta, \mathcal{V}$ and Implied Volatility), `get_option_chain`
* **`stock-data` & `crypto-data`:** Bars, quotes, trades, snapshots, screeners, orderbooks.

---

## 6. Core Trading API Code Reference (Python `alpaca-py`)

### Account Management
```python
from alpaca.trading.client import TradingClient

trading_client = TradingClient('api-key', 'secret-key', paper=True)

# Get account details
account = trading_client.get_account()
print(f"Equity: {account.equity}, Buying Power: {account.buying_power}")
```

### Submitting Orders
```python
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, TrailingStopOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
from alpaca.trading.requests import TakeProfitRequest, StopLossRequest

# Market Order
market_order = MarketOrderRequest(
    symbol="SPY",
    qty=1,
    side=OrderSide.BUY,
    time_in_force=TimeInForce.DAY
)
trading_client.submit_order(order_data=market_order)

# Bracket Order (Market Buy + Take Profit & Stop Loss)
bracket_order = MarketOrderRequest(
    symbol="SPY",
    qty=5,
    side=OrderSide.BUY,
    time_in_force=TimeInForce.DAY,
    order_class=OrderClass.BRACKET,
    take_profit=TakeProfitRequest(limit_price=450),
    stop_loss=StopLossRequest(stop_price=390)
)
trading_client.submit_order(order_data=bracket_order)

# Trailing Stop Order
trailing_stop = TrailingStopOrderRequest(
    symbol="SPY",
    qty=1,
    side=OrderSide.SELL,
    time_in_force=TimeInForce.GTC,
    trail_percent=1.5 # 1.5% below high watermark
)
trading_client.submit_order(order_data=trailing_stop)
```

### Options Chains & Orders
Using Python SDK or REST endpoints, retrieve option contracts for underlying symbols, inspect options snapshots (Greeks, IV, Bid/Ask), and submit option order legs.

---

## 7. Broker API Summary
* Intended for Fintech apps, Broker-Dealers, and RIAs to create end-user brokerage accounts, manage ACH funding, wire transfers, and internal balance journaling between firm accounts and end-user accounts.
* Hosted Broker MCP Server available at `https://broker-api.sandbox.alpaca.markets/mcp` for sandbox account lifecycle testing.
