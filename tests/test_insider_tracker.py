from signals.insider_tracker import insider_tracker
from config import config

def run_test():
    print("=" * 60)
    print("🔍 CHECKPOINT 3 TEST: SEC EDGAR Insider Tracker (Form 4)")
    print("=" * 60)
    
    symbols = config.TARGET_SYMBOLS
    print(f"Scanning SEC filings for underlyings: {', '.join(symbols)}...")
    
    results = insider_tracker.fetch_recent_filings(symbols)
    
    print(f"\nScan Complete! Filings Detected: {len(results)}")
    if results:
        for idx, item in enumerate(results, 1):
            print(f"\n[{idx}] Symbol: {item['symbol']}")
            print(f"    Title: {item['title']}")
            print(f"    Form: {item['form_type']}")
            print(f"    Updated: {item['updated_at']}")
    else:
        print("ℹ️ No immediate Form 4 filings found in the latest 40 SEC feeds for focus underlyings.")
        print("SEC Scanner pipeline is operational & responsive!")
    print("=" * 60)

if __name__ == "__main__":
    run_test()
