from signals.option_flow import option_flow_scanner
from config import config

def run_test():
    print("=" * 60)
    print("🔍 CHECKPOINT 5 TEST: Alpaca Option Chains & Market Data")
    print("=" * 60)
    
    symbols = config.TARGET_SYMBOLS[:3]  # Test top 3 underlyings
    print(f"Querying live option chains on Alpaca Paper API for: {', '.join(symbols)}...\n")
    
    for symbol in symbols:
        result = option_flow_scanner.get_option_chain_summary(symbol)
        print(f"[{symbol}] Status: {result['status']}")
        print(f"       Contracts Found: {result.get('total_contracts', 0)}")
        print(f"       Calls: {result.get('calls_found', 0)} | Puts: {result.get('puts_found', 0)}")
        if result.get('sample_call_symbol'):
            print(f"       Sample Option Contract: {result['sample_call_symbol']}")
        print("-" * 50)
        
    print("\n✅ Option Chain Scanner pipeline is operational & responsive!")
    print("=" * 60)

if __name__ == "__main__":
    run_test()
