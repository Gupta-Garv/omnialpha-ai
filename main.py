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
from core.deepseek_router import ai_router

# ── Shared state (dashboard reads from this dict) ──────────────────────────
SYSTEM_STATE = {
    "kill_switch_engaged": False,
    "status": "ACTIVE",
    "realized_banked_profit": 0.0,
    "recent_signals": [],
    "console_logs": [],
    "ai_cognition_stream": "🧠 [AI MASTER TRADER COGNITION] Engine initializing real-time market evaluation...",
    "revolver_status": {}
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
    pending_symbols = alpaca_client.get_pending_order_symbols()
    active_symbols = {p["symbol"] for p in open_positions}
    held_symbols = active_symbols | set(pending_symbols)
    reflexion_memory.reconcile_journal(held_symbols)

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
            if config.EXECUTION_MODE == "READ_ONLY":
                log(f"  [READ_ONLY] Exit signal triggered for {sym}: {action}. Order submission bypassed.")
            else:
                try:
                    alpaca_client.client.cancel_orders()
                    alpaca_client.client.close_position(sym)
                    held_symbols.discard(sym)
                    reflexion_memory.record_outcome(
                        symbol=sym,
                        pnl_dollars=pnl,
                        pnl_pct=(pnl / float(pos.get("market_value", 1))) * 100,
                    )
                    realized_gain += pnl
                    log(f"  CLOSED {sym}: ${pnl:+.2f}")
                except Exception as e:
                    log(f"  Close failed for {sym}: {e}")

    total_floating_pnl = sum(float(p.get("unrealized_pl", 0)) for p in open_positions)
    SYSTEM_STATE["realized_banked_profit"] = round(equity - 100000.0 - total_floating_pnl, 2)

    # 4. AI Holistic Portfolio Entry Evaluator & Cognition Stream
    holistic = committee.evaluate_portfolio_holistic(targets, account, open_positions, held_symbols)
    SYSTEM_STATE["ai_cognition_stream"] = holistic.get("cognition_stream", "")
    SYSTEM_STATE["revolver_status"] = ai_router.get_revolver_status()
    log(f"{SYSTEM_STATE['ai_cognition_stream']}")

    current_signals = []
    
    # Show status for currently held positions
    for sym in held_symbols:
        current_signals.append({
            "symbol": sym,
            "action": "HOLD_POSITION",
            "reason": "Active position under AI risk & target supervision.",
            "confidence": 0.85,
            "strategy_type": "HOLDING"
        })

    if len(held_symbols) >= 3:
        log("  ENTRY → Max active portfolio positions (3) reached. Maintaining capital protection.")
    else:
        best_opp = holistic.get("entry_decision", {})
        sym = best_opp.get("symbol")
        action = best_opp.get("action")
        reason = best_opp.get("reason")
        
        if action == "PROPOSE_TRADE" and sym and sym != "NONE" and sym != "ALL":
            log(f"  ENTRY [{sym}] → PROPOSE_TRADE | {reason}")
            current_signals.append(best_opp)
            
            if config.EXECUTION_MODE == "READ_ONLY":
                log(f"  [READ_ONLY] AI Buy signal for {sym}. Order submission bypassed.")
            else:
                trade_notional = best_opp.get("notional", config.BLOCK_NOTIONAL)
                result = alpaca_client.submit_paper_trade(sym, side="buy", notional=trade_notional)
                if result.get("status") in ("SUBMITTED", "SUCCESS"):
                    held_symbols.add(sym)
                    reflexion_memory.record_entry(sym, best_opp.get("strategy_type", "AI_SELECT_DIP"), best_opp.get("confidence", 0.85))
                    log(f"  ORDER SENT: {sym} ${trade_notional:,.0f} | ID={result.get('order_id')}")
                elif result.get("status") == "SKIPPED":
                    log(f"  {sym} order skipped: {result.get('reason')}")
                else:
                    log(f"  Order failed for {sym}: {result.get('error', result.get('reason', 'Unknown error'))}")
        else:
            log(f"  ENTRY → HOLD_CASH | {reason}")

    SYSTEM_STATE["recent_signals"] = current_signals
    log(f"=== CYCLE #{cycle} END ===\n")


# ── Main Loop ──────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  OmniAlpha Autonomous Trading Engine")
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

        time.sleep(5)  # 5-second high-velocity cycle interval powered by Revolver Key Rotator


if __name__ == "__main__":
    main()
