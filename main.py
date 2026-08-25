import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import time
import threading
import requests
from config import config
from core.alpaca_client import alpaca_client
from brain.committee import committee
from memory.journal import reflexion_memory
from dashboard.app import app

POSITION_SIZING = {
    "SPY": 10,   # ~$7,640 position size
    "QQQ": 10,   # ~$7,090 position size
    "NVDA": 25,  # ~$5,300 position size
    "AAPL": 20,  # ~$6,160 position size
    "TSLA": 20,  # ~$7,060 position size
    "AMD": 15    # ~$7,140 position size
}

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
            print(f"\n--- [SCAN CYCLE #{scan_cycle}] ---")
            
            # Fetch current open positions to enforce position capping
            open_positions = alpaca_client.get_positions()
            existing_symbols = [p.get("symbol") for p in open_positions]
            
            for symbol in config.TARGET_SYMBOLS:
                decision = committee.evaluate_opportunity(symbol, account)
                action = decision.get("action")
                reason = decision.get("reason")
                
                print(f"[{symbol}] Action: {action} | Reason: {reason}")
                
                # Only execute new trade if symbol is NOT already in open positions
                if action == "PROPOSE_TRADE" and symbol not in existing_symbols:
                    strat = decision.get("strategy_type")
                    conf = decision.get("confidence", 0.75)
                    audit = decision.get("audit_trail", {})
                    trade_qty = POSITION_SIZING.get(symbol, 10)
                    
                    # Record entry in Reflexion Memory
                    entry_id = reflexion_memory.record_entry(symbol, strat, conf, audit)
                    print(f"🧠 REFLEXION MEMORY LOGGED: {entry_id}")
                    
                    print(f"⚡ EXECUTING HIGH-CAPACITY PAPER ORDER: {trade_qty} shares of {symbol} ({strat})...")
                    exec_res = alpaca_client.submit_paper_trade(symbol, side="buy", qty=trade_qty)
                    print(f"    Result: {exec_res}")
                elif symbol in existing_symbols:
                    print(f"    [POSITION CAP] Active position exists for {symbol}. Holding current trade.")

            scan_cycle += 1
            print(f"\nSleeping 30 seconds before next scan cycle... (Press Ctrl+C to stop)")
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\nHalting OmniAlpha AI System... Goodbye!")

if __name__ == "__main__":
    main_loop()
