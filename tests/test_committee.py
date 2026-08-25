from brain.committee import committee
from config import config

def run_test():
    print("=" * 60)
    print("🧠 CHECKPOINT 7 TEST: Multi-Agent Decision Committee")
    print("=" * 60)
    
    mock_account = {"equity": 100000.0, "buying_power": 400000.0}
    symbols = config.TARGET_SYMBOLS
    
    print(f"Evaluating multi-agent signal matrix for underlyings: {', '.join(symbols)}...\n")
    
    for symbol in symbols:
        decision = committee.evaluate_opportunity(symbol, mock_account)
        print(f"[{symbol}] Action: {decision['action']}")
        print(f"       Reason: {decision['reason']}")
        if decision.get("action") == "PROPOSE_TRADE":
            print(f"       Strategy: {decision['strategy_type']} | Confidence: {decision['confidence'] * 100:.0f}%")
            print(f"       Max Risk: ${decision['max_loss']:.2f} | Max Reward: ${decision['max_gain']:.2f}")
            print(f"       Audit Rationale: {decision['audit_trail']['rationale']}")
        print("-" * 50)
        
    print("\n✅ Multi-Agent Committee Decision pipeline is operational & responsive!")
    print("=" * 60)

if __name__ == "__main__":
    run_test()
