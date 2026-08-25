from core.risk_shield import RiskShield

def run_test():
    print("=" * 60)
    print("🛡️ CHECKPOINT 6 TEST: Unbreakable Quantitative Risk Shield")
    print("=" * 60)
    
    shield = RiskShield(account_equity=100000.0, buying_power=400000.0)
    print(f"Testing Risk Shield on Account Equity: ${shield.account_equity:,.2f} | Buying Power: ${shield.buying_power:,.2f}\n")

    # Test Case 1: Compliant defined-risk trade ($300 risk on $100k account)
    res1 = shield.validate_trade("NVDA", "BULL_PUT_SPREAD", 1, max_possible_loss=300.0, max_possible_gain=600.0)
    print(f"[TEST 1 - Compliant Trade ($300 Risk)]")
    print(f"       Approved: {res1.approved} | Reason: {res1.reason}\n")

    # Test Case 2: Over-leveraged trade ($5,000 risk > 2% cap)
    res2 = shield.validate_trade("TSLA", "CALL_BUY", 10, max_possible_loss=5000.0, max_possible_gain=15000.0)
    print(f"[TEST 2 - Over-leveraged Trade ($5,000 Risk)]")
    print(f"       Approved: {res2.approved} | Reason: {res2.reason}\n")

    # Test Case 3: Undefined risk trade ($0 or negative risk spec)
    res3 = shield.validate_trade("SPY", "NAKED_OPTION", 1, max_possible_loss=0.0, max_possible_gain=1000.0)
    print(f"[TEST 3 - Undefined Risk Trade ($0 Risk Spec)]")
    print(f"       Approved: {res3.approved} | Reason: {res3.reason}\n")

    assert res1.approved == True, "Test 1 failed: Should approve compliant trade"
    assert res2.approved == False, "Test 2 failed: Should block over-leveraged trade"
    assert res3.approved == False, "Test 3 failed: Should block undefined risk trade"

    print("✅ Risk Shield guardrail assertions passed 100%!")
    print("=" * 60)

if __name__ == "__main__":
    run_test()
