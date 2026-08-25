# Alpaca AI Trading Agents Hackathon — Master Winning Plan

## 1. What the Hackathon Demands
* **Core Goal:** Build an autonomous AI trading agent that trades **options** on Alpaca's **$100,000 Paper Trading Platform**.
* **Duration:** Aug 28 – Sep 4, 2026 (7 Days).
* **Required Alpaca Tech:** Must use **Alpaca MCP Server** or **Alpaca CLI**.
* **Key Deliverables:** 
  1. Fresh $100k Alpaca Paper Trading Account ID (for judging live P&L).
  2. Public GitHub Repository with complete source code.
  3. 1-Page Write-up (AI logic, risk gates, infrastructure).
  4. Video Presentation & Pitch Deck.
  5. *(Bonus)* Up to 5 social posts on X/LinkedIn tagging `@lablabai` and `@AlpacaHQ`.

---

## 2. Solving the "24/7 Running & AI Execution" Problem

### The Misconception vs. Reality
* **Options Market Hours:** US Stock & Options markets only operate **Monday–Friday, 9:30 AM to 4:00 PM Eastern Time**. Options do NOT trade 24/7 (unlike crypto).
* **AI Chat vs. Background Bot:** You don't need an open chat session 24/7. We will write an **autonomous background Python daemon script** that runs automatically during market hours.
* **How It Works:**
  1. The script wakes up every 5–15 minutes during US market open hours.
  2. It queries market data via **Alpaca CLI / MCP**.
  3. It feeds data to an **LLM Reasoning Engine** (Gemini / Claude API) to analyze options chains and market regime.
  4. It places/manages options orders with strict **Risk Gates** (stop-losses, max position limits).
  5. It logs all trades and updates a **Web Dashboard** live!

---

## 3. Recommended Winning Strategy: "Options Alpha Sentinel AI"

### Strategic Pillars
1. **Multi-Regime Options Strategy:**
   * **Bullish/Bearish Trend:** Executes Credit Spreads or Momentum Calls/Puts on high-liquidity underlyings (`SPY`, `QQQ`, `NVDA`, `AAPL`, `TSLA`).
   * **High Volatility (Earnings/News):** Sells defined-risk spreads (Iron Condors / Vertical Spreads) to capture Volatility Crush (Implied Volatility decay).
2. **AI Reasoning + Quantitative Guardrails:**
   * **Quant Layer:** Calculates Option Greeks ($\Delta, \Theta, \Gamma$) and Implied Volatility Rank (IVR).
   * **AI Layer:** Analyzes market news + technical sentiment to confirm trade direction.
   * **Risk Shield:** Hard stop at 3% max loss per trade, max 10% total portfolio allocation at any time.
3. **Dual Alpaca Integration (CLI + MCP):**
   * Uses **Alpaca CLI** for fast JSON data retrieval & background order execution.
   * Exposes an **Alpaca MCP Server** bridge so you (and the judges) can inspect and chat with the bot in real-time.

---

## 4. Key Milestones & Workflow

| Phase | Tasks |
| :--- | :--- |
| **Phase 1: Environment & Account Setup** | Create fresh Alpaca Paper account ($100k), generate API keys, test CLI connection. |
| **Phase 2: Strategy Engine & Quant Logic** | Build options scanner (retrieves option chains, Delta, IV) using `alpaca-py` & CLI. |
| **Phase 3: AI Brain & Risk Guardrails** | Integrate LLM API for market analysis, set up automated stop-loss / profit-taking rules. |
| **Phase 4: Autonomous Background Daemon** | Build market-hours scheduler daemon that executes autonomously without human intervention. |
| **Phase 5: Live Dashboard & Visuals** | Build a sleek, real-time web dashboard displaying equity curve, active option positions, and AI trade logs. |
| **Phase 6: Submission & Social Media** | Draft 1-page write-up, record 2-minute demo video, post 5 social progress updates for $1k bonus pool. |
