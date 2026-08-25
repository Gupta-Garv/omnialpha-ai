import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dashboard.app import app

def run_test():
    print("=" * 60)
    print("🖥️ CHECKPOINT 8 TEST: Visual Web Dashboard & Kill Switch")
    print("=" * 60)
    
    client = app.test_client()
    
    # 1. Test Web UI homepage render
    res_home = client.get('/')
    print(f"[TEST 1 - Homepage Render]: Status Code {res_home.status_code}")
    assert res_home.status_code == 200, "Homepage failed to render"
    assert b"OmniAlpha AI" in res_home.data, "Title badge missing in UI"

    # 2. Test Real-Time State API Endpoint
    res_api = client.get('/api/state')
    print(f"[TEST 2 - API State Endpoint]: Status Code {res_api.status_code}")
    assert res_api.status_code == 200, "State API failed"
    data = res_api.get_json()
    assert "account" in data, "Account field missing in API state"
    assert "signals" in data, "Signals field missing in API state"
    print(f"       Account Equity in API: ${data['account'].get('equity', 0):,.2f}")
    print(f"       Signals Evaluated in API: {len(data['signals'])}")

    # 3. Test Emergency Kill Switch Endpoint
    res_kill = client.post('/api/kill_switch')
    print(f"[TEST 3 - Emergency Kill Switch API]: Status Code {res_kill.status_code}")
    assert res_kill.status_code == 200, "Kill switch endpoint failed"
    kill_data = res_kill.get_json()
    assert kill_data["status"] == "SUCCESS", "Kill switch activation failed"
    print(f"       Kill Switch Message: {kill_data['message']}")

    print("\n✅ Web Dashboard & Emergency Kill Switch passed 100%!")
    print("=" * 60)

if __name__ == "__main__":
    run_test()
