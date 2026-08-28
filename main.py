"""
OmniAlpha Autonomous Trading Engine
====================================
Single entry point. Starts the Flask dashboard in a background thread,
then runs the trading loop in the main thread.

Architecture (no circular imports):
  main.py
    ├── dashboard/app.py  (Flask server, read-only SYSTEM_STATE access)
    ├── core/alpaca_client.py
    ├── brain/committee.py  (entry + exit decisions)
    ├── signals/screener_agent.py
    └── memory/journal.py
"""

import sys
import time
import threading
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import config
from core.alpaca_client import alpaca_client
from brain.committee import committee
from signals.screener_agent import screener_agent
from memory.journal import reflexion_memory

# ── Shared state (dashboard reads from this dict) ──────────────────────────
SYSTEM_STATE = {
    "kill_switch_engaged": False,
    "status": "ACTIVE",
    "realized_banked_profit": 0.0,
    "recent_signals": [],
    "console_logs": [],
}

EQUITY_HISTORY = []


def log(msg: str):
    """Print to stdout AND push to the dashboard console stream."""
    from datetime import datetime
    ts = datetime.now().strftime("%H:%M:%S")
    entry = f"[{ts}] {msg}"
    print(entry)
    SYSTEM_STATE["console_logs"].append(entry)
    if len(SYSTEM_STATE["console_logs"]) > 50:
        SYSTEM_STATE["console_logs"].pop(0)


# ── Dashboard Server ────────────────────────────────────────────────────────
def _start_dashboard():
    """Run Flask app in a daemon thread."""
    import importlib.util, os
    os.environ["OMNI_STATE_MODULE"] = "main"
    from dashboard.app import app
    app.run(host="0.0.0.0", port=config.PORT, debug=False, use_reloader=False)


# ── Keep-Alive Ping (Render free tier) ────────────────────────────────────
def _keep_alive():
    while True:
        time.sleep(300)
        try:
            requests.get("https://omnialpha-ai.onrender.com", timeout=10)
        except Exception:
            pass


# ── Core Trading Cycle ─────────────────────────────────────────────────────
def run_trading_cycle(cycle: int):
    """
    One complete trading cycle:
    1. Screener → update watchlist
    2. Fetch account & open positions
    3. AI Exit Predictor → close positions that hit targets
    4. AI Entry Committee → open new positions where conviction is high
    5. Update SYSTEM_STATE.recent_signals for the dashboard
    """
    if SYSTEM_STATE["kill_switch_engaged"]:
        log("KILL_SWITCH active — trading halted.")
        return

    log(f"=== CYCLE #{cycle} START ===")

    # 1. Dynamic Screener (runs at most once per hour)
    targets = screener_agent.get_targets()
    config.TARGET_SYMBOLS = targets
    log(f"Watchlist: {targets}")

    # 2. Account & Positions
    account = alpaca_client.get_account_summary()
    if "error" in account:
        log(f"Account error: {account['error']}")
        return

    equity = float(account.get("equity", 0))
    buying_power = float(account.get("buying_power", 0))
    log(f"Equity=${equity:,.2f}  Buying Power=${buying_power:,.2f}")

    # Append equity to chart history
    from datetime import datetime
    EQUITY_HISTORY.append({"time": datetime.now().strftime("%H:%M:%S"), "equity": round(equity, 2)})
    if len(EQUITY_HISTORY) > 60:
        EQUITY_HISTORY.pop(0)

    open_positions = alpaca_client.get_positions()
    held_symbols = {p["symbol"] for p in open_positions}

    # 3. Exit Predictor
    realized_gain = 0.0
    for pos in open_positions:
        sym = pos["symbol"]
        decision = committee.evaluate_exit(pos)
        action = decision["action"]
        pnl = decision["pnl"]
        reason = decision["reason"]
        log(f"  EXIT [{sym}] → {action} | P&L=${pnl:.2f} | {reason}")

        if action in ("TAKE_PROFIT_EXIT", "CUT_LOSS_EXIT"):
            try:
                alpaca_client.client.close_position(sym)
                held_symbols.discard(sym)
                reflexion_memory.record_outcome(
                    symbol=sym,
                    pnl_dollars=pnl,
                    pnl_pct=(pnl / float(pos.get("market_value", 1))) * 100,
                )
                realized_gain += pnl
                log(f"  ✅ CLOSED {sym}: ${pnl:+.2f}")
            except Exception as e:
                log(f"  ⚠️  Close failed for {sym}: {e}")

    SYSTEM_STATE["realized_banked_profit"] = round(
        SYSTEM_STATE.get("realized_banked_profit", 0.0) + realized_gain, 2
    )

    # 4. Entry Evaluator
    current_signals = []
    for sym in targets:
        if sym in held_symbols:
            log(f"  ENTRY [{sym}] → already held, skipping.")
            current_signals.append({"symbol": sym, "action": "HOLD_POSITION", "reason": "Already in portfolio.", "confidence": 0, "strategy_type": "HOLDING"})
            continue

        if len(held_symbols) >= 2:
            log(f"  ENTRY [{sym}] → max active Tier-1 positions (2) reached.")
            break

        decision = committee.evaluate_entry(sym, account)
        action = decision["action"]
        reason = decision["reason"]
        log(f"  ENTRY [{sym}] → {action} | {reason}")
        current_signals.append(decision)

        if action == "PROPOSE_TRADE":
            trade_notional = decision.get("notional", config.BLOCK_NOTIONAL)
            result = alpaca_client.submit_paper_trade(sym, side="buy", notional=trade_notional)
            if result.get("status") == "SUBMITTED":
                held_symbols.add(sym)
                reflexion_memory.record_entry(sym, decision.get("strategy_type", "MOMENTUM_LONG"), decision.get("confidence", 0.85))
                log(f"  🚀 ORDER SENT: {sym} ${trade_notional:,.0f} | ID={result.get('order_id')}")
            else:
                log(f"  ⚠️  Order failed for {sym}: {result.get('error', 'Unknown error')}")

    SYSTEM_STATE["recent_signals"] = current_signals
    log(f"=== CYCLE #{cycle} END ===\n")


# ── Main Loop ──────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("🚀  OmniAlpha Autonomous Trading Engine")
    print(f"    Paper Mode: {config.ALPACA_PAPER}")
    print(f"    Block Size: ${config.BLOCK_NOTIONAL:,.0f}")
    print(f"    Dashboard:  http://0.0.0.0:{config.PORT}")
    print("=" * 60)

    # Boot dashboard in background
    threading.Thread(target=_start_dashboard, daemon=True).start()
    threading.Thread(target=_keep_alive, daemon=True).start()
    time.sleep(2)  # Let Flask start

    log("SYS_INIT: OmniAlpha engine online.")

    cycle = 1
    while True:
        try:
            run_trading_cycle(cycle)
            cycle += 1
        except KeyboardInterrupt:
            log("SHUTDOWN: KeyboardInterrupt received.")
            break
        except Exception as e:
            import traceback
            log(f"CYCLE ERROR: {e}")
            traceback.print_exc()

        time.sleep(15)  # 15s between cycles → well within Gemini free-tier limits


if __name__ == "__main__":
    main()
