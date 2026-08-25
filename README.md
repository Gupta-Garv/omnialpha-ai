# 🚀 OmniAlpha AI — Pre-Catalyst Predictive Options Agent

> **Autonomous Multi-Agent Options Trading System for Alpaca Paper Trading ($100,000 Balance)**  
> Built for the **Alpaca AI Trading Agents Hackathon** (lablab.ai × Alpaca)

---

## 🌟 Overview

**OmniAlpha AI** is an institutional-grade options trading agent designed to run autonomously during US market hours (**7:00 PM - 1:30 AM IST** / 9:30 AM - 4:00 PM ET). 

Instead of reacting to news *after* prices move, OmniAlpha AI uses a **Pre-Catalyst Swarm Committee** to spot insider SEC Form 4 filings, sentiment velocity spikes, and option chain mispricings **before** public announcements break.

---

## 🔑 Key Features

* **Multi-Agent Signal Committee:** Synthesizes SEC EDGAR Form 4 insider transactions, social news velocity, and Alpaca option chains.
* **Defined-Risk Vertical Spreads:** Executes high-probability Bull Put & Bear Call Spreads with mathematically capped risk.
* **Unbreakable Risk Shield:** Hardcoded 2.0% position risk cap ($2,000 max loss on $100k account) that cannot be bypassed by LLMs.
* **Real-Time Visual Command Center:** Sleek, dark-mode web dashboard (`http://localhost:5000`) with live account equity tracking and an **Emergency Kill Switch**.
* **Alpaca Platform Integration:** Full compatibility with `alpaca-py`, Alpaca CLI, and `alpaca-mcp-server`.

---

## ⚡ Quickstart & Setup

### 1. Clone & Environment Setup
```bash
git clone https://github.com/your-username/alpaca-ai-trading-agent.git
cd alpaca-ai-trading-agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Credentials
Copy `.env.example` to `.env` and enter your Alpaca Paper API Keys:
```env
ALPACA_API_KEY=PKXXXXXXXXXXXXXXXXXX
ALPACA_SECRET_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
ALPACA_PAPER=true
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

### 3. Run Connection Test
```bash
python test_conn.py
```

### 4. Launch Command Center Dashboard & Agent
```bash
# Launch visual dashboard
python dashboard/app.py

# In another terminal: Launch daemon scanner
python main.py
```

---

## 📊 System Verification Tests

Run the full automated test suite across all checkpoints:
```bash
# Run all unit and integration tests
PYTHONPATH=. python tests/test_insider_tracker.py
PYTHONPATH=. python tests/test_social_radar.py
PYTHONPATH=. python tests/test_option_flow.py
PYTHONPATH=. python tests/test_risk_shield.py
PYTHONPATH=. python tests/test_committee.py
PYTHONPATH=. python tests/test_dashboard.py
```

---

## 📄 License
MIT License. Built for lablab.ai × Alpaca AI Trading Agents Hackathon 2026.
