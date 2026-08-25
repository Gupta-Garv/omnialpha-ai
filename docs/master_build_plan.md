# OmniAlpha AI — Master Architecture & Implementation Plan

> **Project Name:** OmniAlpha AI — Pre-Catalyst Predictive Options Swarm Agent  
> **Target Event:** Alpaca AI Trading Agents Hackathon (lablab.ai × Alpaca)  
> **Workspace Directory:** `/Users/apple/.gemini/antigravity/scratch/alpaca-ai-trading-agent`

---

## 1. Project Philosophy & Coding Principles

To prevent "vibe-coding bloat" and keep the codebase clean, robust, and maintainable:
* **Zero-Fluff Principle:** Write compact, highly focused Python code without redundant wrapper classes or dead code.
* **Modular Separation:** Each module has exactly one job (Data Fetching, Signal Detection, Risk Shield, AI Committee, Execution).
* **Strict Typing & Schema Validation:** Use `pydantic` schemas for structured AI outputs and trade validation.
* **Defensive Execution:** All trades pass through a local pre-flight validator before touching Alpaca's paper API.

---

## 2. Integration of Official Alpaca Repositories

We leverage Alpaca's official GitHub repositories directly:

| Official Repository | GitHub URI | How OmniAlpha AI Integrates It |
| :--- | :--- | :--- |
| **`alpacahq/alpaca-py`** | `https://github.com/alpacahq/alpaca-py` | Core Python SDK for options market data, option chains, snapshots (Greeks/IV), and REST order execution. |
| **`alpacahq/cli`** | `https://github.com/alpacahq/cli` | Terminal CLI tool (`alpaca`) used by background daemon scripts for fast JSON execution & quiet order verification. |
| **`alpacahq/alpaca-mcp-server`** | `https://github.com/alpacahq/alpaca-mcp-server` | MCP Server bridge allowing judges to interactively chat with our agent during demo evaluation. |
| **`alpacahq/alpaca-trade-api-js`** | `https://github.com/alpacahq/alpaca-trade-api-js` | Lightweight Node/JS integration for real-time WebSocket dashboard metrics if needed. |

---

## 3. Free External Tools & Data Sources

To keep the project 100% free with zero API costs:

* **Alpaca Paper Trading Account:** Free $100,000 simulated capital for options trading.
* **SEC EDGAR Public API:** Free, official SEC endpoint for tracking Form 4 (insider buy/sell) and 8-K (executive management changes).
* **Google News RSS & Reddit Public Feeds:** Free sentiment and social momentum velocity tracking without paid subscriptions.
* **Google Gemini API (Free Tier / LiteLLM):** Fast, high-reasoning LLM engine for multi-agent synthesis.
* **Vanilla HTML/CSS/JS + Chart.js:** Ultra-fast, lightweight visual Web Dashboard hosted locally (and previewable live).

---

## 4. Hackathon Submission Requirements Checklist

| Deliverable Field | Status / Plan |
| :--- | :--- |
| **Project Title** | `OmniAlpha AI — Pre-Catalyst Predictive Options Swarm Agent` |
| **Short Description** | Pre-catalyst autonomous options trading committee using Alpaca CLI/MCP to detect insider filings, social momentum velocity, and unusual options flow before news breaks. |
| **Long Description** | Comprehensive write-up covering system architecture, multi-agent committee logic, mathematical risk gates, and Alpaca infrastructure. |
| **Tech & Category Tags** | `AI Trading`, `Options Trading`, `Alpaca Trading API`, `MCP Server`, `Alpaca CLI`, `Python`, `Multi-Agent System` |
| **Cover Image & Slides** | High-impact graphic cover image + 5-slide PDF deck detailing architecture and P&L results. |
| **Video Presentation** | 2-minute clean video showing live dashboard execution & Alpaca MCP interactive query. |
| **GitHub Repository** | Public GitHub repo containing compact, fully-documented code and 1-page write-up. |
| **Application / Demo URL** | Live dashboard URL / preview link. |
| **Alpaca Paper Account ID** | Fresh $100,000 paper trading account ID dedicated strictly to hackathon evaluation. |

---

## 5. System Architecture Overview

```
                      ┌──────────────────────────────────────────┐
                      │    7:00 PM - 1:30 AM IST Market Daemon   │
                      └──────────────────────────────────────────┘
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         ▼                                 ▼                                 ▼
┌──────────────────┐             ┌──────────────────┐             ┌──────────────────┐
│  Pillar 1: SEC   │             │  Pillar 2: Social│             │ Pillar 3: Option │
│  Insider Tracker │             │  Velocity Radar  │             │ Sweeps & Greeks  │
│  (Form 4 / 8-K)  │             │  (Reddit/Google) │             │ (Alpaca SDK/CLI) │
└──────────────────┘             └──────────────────┘             └──────────────────┘
         │                                 │                                 │
         └─────────────────────────────────┼─────────────────────────────────┘
                                           ▼
                         ┌───────────────────────────────────┐
                         │   Multi-Agent AI Committee        │
                         │   (Gemini Flash/Pro Synthesis)    │
                         └───────────────────────────────────┘
                                           │
                                           ▼
                         ┌───────────────────────────────────┐
                         │   Asymmetric Risk Shield          │
                         │   (Max 3% risk, Defined Spreads)  │
                         └───────────────────────────────────┘
                                           │
                                           ▼
                         ┌───────────────────────────────────┐
                         │   Alpaca Order Execution          │
                         │   (SDK / CLI / MCP Bridge)        │
                         └───────────────────────────────────┘
                                           │
                                           ▼
                         ┌───────────────────────────────────┐
                         │   Real-Time Visual Web UI         │
                         │   (P&L, Active Spreads, Logs)     │
                         └───────────────────────────────────┘
```

---

## 6. Step-by-Step Implementation Roadmap

### Phase 1: Environment & Project Foundation (Step 1)
* Set up directory structure and `.env` configuration file.
* Install required dependencies (`alpaca-py`, `pydantic`, `flask`/`fastapi`, `requests`).
* Create core configuration parser (`config.py`).

### Phase 2: Alpaca Client & Order Execution Layer (Step 2)
* Build `core/alpaca_client.py`: Wrapper for Alpaca REST API, CLI execution, and Options chain lookup.
* Build `core/risk_shield.py`: Hardcoded risk validator (position size cap, max 3% portfolio risk, stop-loss calculations).

### Phase 3: Pre-Catalyst Signal Modules (Step 3)
* Build `signals/insider_tracker.py`: SEC EDGAR Form 4 & 8-K scraper.
* Build `signals/social_radar.py`: Public sentiment velocity analyzer.
* Build `signals/option_flow.py`: Option Greeks ($\Delta, \Theta, \text{IV}$) & unusual volume scanner via Alpaca SDK.

### Phase 4: Multi-Agent AI Committee (Step 4)
* Build `brain/committee.py`: Synthesizes signals from all 3 pillars, calculates trade confidence score, and outputs defined-risk vertical spread orders.

### Phase 5: Autonomous Market Daemon & Health Heartbeat (Step 5)
* Build `main.py`: Background scheduler operating during US market hours (7:00 PM – 1:30 AM IST).
* Build self-diagnostic health heartbeat.

### Phase 6: Real-Time Visual Web Dashboard (Step 6)
* Build lightweight web UI (`dashboard/`): Real-time equity curve, open option spreads, AI audit log stream, and emergency manual kill switch.

### Phase 7: Hackathon Packaging & Submission (Step 7)
* Finalize 1-page write-up (`docs/submission_writeup.md`).
* Prepare GitHub repo README, presentation slides outline, and demo video script.
