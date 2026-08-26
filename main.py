import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import time
import threading
import requests
import random
from config import config
from core.alpaca_client import alpaca_client
from brain.committee import committee
from brain.exit_predictor import exit_predictor
from memory.journal import reflexion_memory
from dashboard.app import app, add_console_log
from signals.screener_agent import screener_agent



def run_dashboard_server():
    """Run Flask Web Dashboard in background thread."""
    app.run(host="0.0.0.0", port=config.PORT, debug=False, use_reloader=False)

def keep_alive_ping():
    """Periodically ping the web server every 5 minutes to prevent cloud sleeping."""
    url = "https://omnialpha-ai.onrender.com"
    while True:
        try:
            time.sleep(300)
            requests.get(url, timeout=10)
        except Exception:
            pass

def run_autonomous_trading_cycle(scan_cycle: int = 1):
    """Execute a single autonomous trading cycle: screener -> exits -> entries -> signals -> logs."""
    print(f"\n--- [SCAN CYCLE #{scan_cycle}] ---")
    
    # 0. DYNAMIC PRE-MARKET/MARKET SCREENER
    config.TARGET_SYMBOLS = screener_agent.get_dynamic_targets()
    
    account = alpaca_client.get_account_summary()
    
    # Fetch current open positions
    open_positions = alpaca_client.get_positions()
    existing_symbols = [p.get("symbol") for p in open_positions]
    
    # 1. AI EXIT PREDICTOR & DYNAMIC HARVESTING ENGINE
    for pos in open_positions:
        sym = pos.get("symbol")
        eval_exit = exit_predictor.evaluate_position_exit(pos, "BULLISH_VELOCITY")
        exit_action = eval_exit.get("action")
        reason = eval_exit.get("reason")
        pnl = float(pos.get("unrealized_pl", 0.0))

        if exit_action in ["TAKE_PROFIT_EXIT", "CUT_LOSS_EXIT"]:
            print(f"🎯 AI EXIT SIGNAL [{sym}]: {exit_action} | {reason}")
            add_console_log(f"AI_EXIT_PREDICTOR: Closing {sym} position (+${pnl:.2f}). Reason: {reason}")
            try:
                alpaca_client.client.close_position(sym)
                if sym in existing_symbols:
                    existing_symbols.remove(sym)
                reflexion_memory.record_outcome(sym, pnl_dollars=pnl, pnl_pct=(pnl / float(pos.get("market_value", 1.0))) * 100)
            except Exception as e:
                print(f"    Exit Order Note: {str(e)}")

    current_signals = []
    
    # 2. DYNAMIC ALPHA HUNTER
    for symbol in config.TARGET_SYMBOLS:
        # Add local safety limits
        if len(existing_symbols) >= 6 and symbol not in existing_symbols:
            continue
            
        decision = committee.evaluate_opportunity(symbol, account)
        action = decision.get("action")
        reason = decision.get("reason")
        current_signals.append(decision)
        
        print(f"[{symbol}] Action: {action} | Reason: {reason}")
        add_console_log(f"AI_SCAN [{symbol}]: Action={action}. Reason: {reason[:60]}...")
        
        # Execute new trade if symbol is not currently held
        if action == "PROPOSE_TRADE" and symbol not in existing_symbols:
            strat = decision.get("strategy_type")
            conf = decision.get("confidence", 0.75)
            audit = decision.get("audit_trail", {})
            # Record entry in Reflexion Memory
            entry_id = reflexion_memory.record_entry(symbol, strat, conf, audit)
            print(f"🧠 REFLEXION MEMORY LOGGED: {entry_id}")
            
            print(f"⚡ EXECUTING INSTITUTIONAL ALPHA ORDER: $65,000 block of {symbol} ({strat})...")
            exec_res = alpaca_client.submit_paper_trade(symbol, side="buy", notional=65000.0)
            add_console_log(f"ORDER_EXEC: Submitted order for $65,000 block of {symbol} ({strat}).")
            print(f"    Result: {exec_res}")
        elif symbol in existing_symbols:
            print(f"    [HOLDING ACTIVE POSITION] {symbol} active in portfolio. Monitoring price momentum.")

    from dashboard.app import SYSTEM_STATE
    SYSTEM_STATE["recent_signals"] = current_signals

def main_loop():
    print("=" * 60)
    print("🚀 OmniAlpha AI — Autonomous Paper Trading Agent (Reflexion Memory Active)")
    print(f"Target Underlyings: {', '.join(config.TARGET_SYMBOLS)}")
    print(f"Paper Mode: {config.ALPACA_PAPER} | Base URL: {config.BASE_URL}")
    print("=" * 60)

    # Start Web Dashboard server thread
    print(f"\n🌐 Starting Visual Web Dashboard at http://localhost:{config.PORT}...")
    dash_thread = threading.Thread(target=run_dashboard_server, daemon=True)
    dash_thread.start()

    # Start Keep-Alive Self-Ping thread
    ping_thread = threading.Thread(target=keep_alive_ping, daemon=True)
    ping_thread.start()
    time.sleep(1.5)

    account = alpaca_client.get_account_summary()
    if "error" in account:
        print(f"⚠️ Account Connect Note: {account['error']}")
    else:
        print(f"Connected Account Equity: ${account.get('equity', 0):,.2f}")
        print(f"Buying Power: ${account.get('buying_power', 0):,.2f}")

    print("\n[LIVE MONITORING LOOP ACTIVE] Scanning signals & executing paper trades with Self-Learning Memory...")
    
    try:
        scan_cycle = 1
        while True:
            run_autonomous_trading_cycle(scan_cycle)
            scan_cycle += 1
            print(f"\nSleeping 10 seconds before next scan cycle...")
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\nHalting OmniAlpha AI System... Goodbye!")
    except Exception as e:
        print(f"\nCRITICAL ERROR IN MAIN LOOP: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Don't let the script die entirely in production, just wait and retry
        time.sleep(10)
        main_loop()

if __name__ == "__main__":
    main_loop()
