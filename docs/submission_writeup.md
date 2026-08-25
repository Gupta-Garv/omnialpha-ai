# OmniAlpha AI — Pre-Catalyst Options Swarm Agent
> **Alpaca AI Trading Agents Hackathon Submission**

## 1. Executive Summary
**OmniAlpha AI** is an autonomous, institutional-grade options trading agent designed for Alpaca's $100,000 Paper Trading platform. Unlike standard reactive trading bots that trade *after* news is published, OmniAlpha AI utilizes a **Pre-Catalyst Multi-Agent Architecture** to spot market anomalies, insider transactions, and social velocity *before* public catalysts occur.

---

## 2. Architecture & Technical Integration

OmniAlpha AI combines Alpaca's developer platform with a multi-agent decision swarm:

```
  ┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
  │ SEC EDGAR Form 4  │     │  Google News /    │     │ Alpaca Option     │
  │ Insider Tracker   │     │  Social Radar     │     │ Chains & Greeks   │
  └─────────┬─────────┘     └─────────┬─────────┘     └─────────┬─────────┘
            │                         │                         │
            └─────────────────────────┼─────────────────────────┘
                                      ▼
                      ┌───────────────────────────────┐
                      │   Multi-Agent AI Brain        │
                      │   (Gemini Flash/Pro Engine)   │
                      └───────────────┬───────────────┘
                                      ▼
                      ┌───────────────────────────────┐
                      │   Quantitative Risk Shield    │
                      │   (Hardcoded 2% Risk Cap)     │
                      └───────────────┬───────────────┘
                                      ▼
                      ┌───────────────────────────────┐
                      │   Alpaca Order Execution      │
                      │   (alpaca-py / CLI / MCP)     │
                      └───────────────────────────────┘
```

* **Alpaca Python SDK (`alpaca-py`):** Drives REST API order submission, account state tracking, and live option chain queries.
* **Alpaca CLI (`alpaca`):** Enables headless background execution and dry-run order validation.
* **Alpaca MCP Server Bridge:** Exposes real-time account data and trade reasoning to AI assistants for interactive judging.

---

## 3. Pre-Catalyst Signal Engine

1. **Pillar 1 — SEC EDGAR Insider Tracker (`signals/insider_tracker.py`):** Scans official SEC Atom feeds for Form 4 insider transactions, detecting executive buys/sells prior to public news releases.
2. **Pillar 2 — Social Velocity Radar (`signals/social_radar.py`):** Measures keyword sentiment velocity and news volume acceleration on key underlyings (`SPY`, `QQQ`, `NVDA`, `AAPL`, `TSLA`, `AMD`).
3. **Pillar 3 — Option Chain & Greeks Scanner (`signals/option_flow.py`):** Scans Alpaca option chains to select defined-risk vertical spreads (Bull Put / Bear Call Spreads).

---

## 4. Hardcoded Quantitative Risk Shield

To guarantee portfolio safety and protect the $100,000 paper balance:
* **Position Size Cap:** Maximum risk per trade is hard-capped at **2.0% of portfolio equity** ($2,000 max risk).
* **Defined-Risk Requirement:** Only vertical option spreads with mathematically capped maximum loss are permitted. Naked options are strictly rejected.
* **Buying Power Guardrail:** Automatic pre-flight verification prevents over-leverage or day-trading margin calls.
* **Emergency Kill Switch:** A 1-click manual override halts all trading and liquidates active positions immediately.

---

## 5. Account & Live Execution Metrics

* **Paper Account ID:** `ae811ce4-f4dc-47a9-975f-fa2e6b42c169`
* **Starting Capital:** $100,000.00 Paper USD
* **Intraday Buying Power:** $400,000.00
* **Target Underlyings:** `SPY`, `QQQ`, `NVDA`, `AAPL`, `TSLA`, `AMD`
