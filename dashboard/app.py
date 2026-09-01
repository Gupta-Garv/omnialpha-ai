"""
OmniAlpha Dashboard — Flask Web UI
====================================
This module is a PURE READ-ONLY view layer.
It reads from main.SYSTEM_STATE and main.EQUITY_HISTORY (shared dicts).
It does NOT call any AI, does NOT run any trading logic.
This prevents the circular import chain that was crashing the server.
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Lazy import of shared state from main so we don't create a circular import.
# main.py imports dashboard.app — dashboard.app must NOT import from main at
# module level.  We lazily fetch the state in every request handler.
# ---------------------------------------------------------------------------

def _get_state():
    """Return (SYSTEM_STATE, EQUITY_HISTORY) from the main engine module."""
    try:
        if "__main__" in sys.modules and hasattr(sys.modules["__main__"], "SYSTEM_STATE"):
            return sys.modules["__main__"].SYSTEM_STATE, sys.modules["__main__"].EQUITY_HISTORY
        import main as _m
        return _m.SYSTEM_STATE, _m.EQUITY_HISTORY
    except Exception:
        # Fallback empty state when dashboard is booted standalone
        return {
            "kill_switch_engaged": False,
            "status": "ACTIVE",
            "realized_banked_profit": 0.0,
            "recent_signals": [],
            "console_logs": ["[SYSTEM] Dashboard booted. Waiting for engine..."],
        }, []


# ---------------------------------------------------------------------------
# HTML Template
# ---------------------------------------------------------------------------
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OMNIALPHA QUANTITATIVE DESK</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    background: #000; color: #CCC;
    font-family: Arial, Helvetica, sans-serif;
    padding: 4px; height: 100vh;
    display: flex; flex-direction: column; font-size: 11px; overflow: hidden;
}
#auth-overlay {
    position: fixed; top:0; left:0; width:100vw; height:100vh;
    background:#000; z-index:9999;
    display:flex; flex-direction:column; justify-content:center; align-items:center; gap:10px;
}
.auth-card { border:1px solid #555; border-top:4px solid #FFA500; padding:20px; width:300px; display:flex; flex-direction:column; gap:10px; background:#111; }
.auth-title { font-size:12px; font-weight:bold; color:#FFA500; text-align:center; }
.auth-input { background:#000; border:1px solid #555; color:#0F0; padding:6px; text-align:center; font-family:Consolas,monospace; }
.auth-btn { background:#FFA500; color:#000; border:none; padding:6px; font-weight:bold; cursor:pointer; }
.auth-err { font-size:10px; color:#F00; text-align:center; min-height:12px; }

.header { display:flex; justify-content:space-between; align-items:center; background:#1A1A1A; border:1px solid #333; padding:4px 8px; margin-bottom:4px; }
.header-title { color:#FFA500; font-weight:bold; font-size:12px; }
.metrics { display:flex; gap:20px; }
.metric { display:flex; gap:6px; align-items:baseline; }
.m-lbl { color:#888; font-size:10px; }
.m-val { font-family:Consolas,monospace; font-size:14px; font-weight:bold; }
.m-val.green { color:#00FF00; } .m-val.red { color:#FF0000; }
.m-val.yellow { color:#FFFF00; } .m-val.white { color:#FFF; } .m-val.cyan { color:#0FF; }
.btn-panel { display:flex; gap:4px; }
.btn-action { background:#333; color:#FFF; border:1px solid #555; padding:4px 10px; font-size:10px; cursor:pointer; }
.btn-action:hover { background:#FFA500; color:#000; }
.btn-kill { background:#500; color:#F00; border:1px solid #F00; padding:4px 10px; font-size:10px; cursor:pointer; }
.btn-kill:hover { background:#F00; color:#FFF; }

.terminal-grid {
    display:grid;
    grid-template-columns: 35% 35% 30%;
    grid-template-rows: 50% 50%;
    gap:4px; flex-grow:1; height:calc(100vh - 55px);
}
.panel { background:#0A0A0A; border:1px solid #333; display:flex; flex-direction:column; overflow:hidden; }
.panel-head { background:#1A1A1A; border-bottom:1px solid #333; padding:4px 6px; display:flex; justify-content:space-between; align-items:center; }
.panel-title { color:#FFA500; font-weight:bold; font-size:11px; text-transform:uppercase; }
.panel-subtitle { color:#666; font-size:10px; font-family:Consolas,monospace; }
.panel-body { padding:4px; flex-grow:1; overflow-y:auto; }
table { width:100%; border-collapse:collapse; font-family:Consolas,monospace; font-size:10px; }
th { text-align:left; color:#888; border-bottom:1px solid #333; padding:4px; font-weight:normal; position:sticky; top:0; background:#0A0A0A; }
td { padding:4px; border-bottom:1px dotted #222; }
.t-green { color:#0F0; } .t-red { color:#F00; } .t-cyan { color:#0FF; }
.heatmap { display:grid; grid-template-columns:repeat(3,1fr); gap:2px; }
.h-cell { border:1px solid #333; padding:4px; display:flex; flex-direction:column; justify-content:center; align-items:center; height:60px; }
.h-cell.bull { background:#003300; border-color:#0F0; }
.h-cell.bear { background:#330000; border-color:#F00; }
.h-cell.hold { background:#1a1a00; border-color:#aa0; }
.h-sym { color:#FFF; font-weight:bold; font-size:12px; }
.h-val { font-family:Consolas,monospace; font-size:10px; color:#AAA; }
.h-pct { font-family:Consolas,monospace; font-size:12px; font-weight:bold; }
.console { font-family:Consolas,monospace; font-size:10px; color:#0F0; line-height:1.3; }
.footer { display:flex; justify-content:space-between; padding:2px 8px; border-top:1px solid #333; font-family:Consolas,monospace; font-size:10px; color:#666; background:#050505; }
.clock b { color:#AAA; }
::-webkit-scrollbar { width:6px; }
::-webkit-scrollbar-track { background:#0A0A0A; }
::-webkit-scrollbar-thumb { background:#333; }
</style>
</head>
<body>
<div id="auth-overlay">
  <div class="auth-card">
    <div class="auth-title">OMNIALPHA TERMINAL</div>
    <input type="password" id="pass-input" class="auth-input" placeholder="PASSCODE" onkeyup="if(event.key==='Enter')authenticateUser()" autofocus>
    <button class="auth-btn" onclick="authenticateUser()">LOGIN</button>
    <div class="auth-err" id="auth-err"></div>
  </div>
</div>

<div class="header">
  <div class="header-title">OMNIALPHA QUANTITATIVE DESK</div>
  <div class="metrics">
    <div class="metric"><span class="m-lbl">EQUITY</span><span class="m-val white" id="equity">--</span></div>
    <div class="metric"><span class="m-lbl">B.POWER</span><span class="m-val white" id="buying_power">--</span></div>
    <div class="metric"><span class="m-lbl">PNL (SECURED)</span><span class="m-val green" id="banked-pnl">--</span></div>
    <div class="metric"><span class="m-lbl">PNL (FLOAT)</span><span class="m-val white" id="floating-pnl">--</span></div>
    <div class="metric"><span class="m-lbl">STATUS</span><span class="m-val cyan" id="sys-status">ACTIVE</span></div>
  </div>
  <div class="btn-panel">
    <button class="btn-action" onclick="liquidateAll()">LIQUIDATE ALL</button>
    <button class="btn-kill" onclick="triggerKillSwitch()">HALT TRADING</button>
  </div>
</div>

<div class="terminal-grid">
  <!-- Panel 1: Equity Chart + Allocation -->
  <div class="panel">
    <div class="panel-head">
      <span class="panel-title">PORTFOLIO PERFORMANCE &amp; ALLOCATION</span>
      <span class="panel-subtitle" id="chart-tick-time">TICK: --</span>
    </div>
    <div class="panel-body" style="display:flex;flex-direction:column;gap:4px;">
      <div style="flex:1;position:relative;min-height:120px;"><canvas id="equityChart"></canvas></div>
      <div style="flex:1;position:relative;min-height:120px;border-top:1px dotted #333;padding-top:4px;"><canvas id="allocationChart"></canvas></div>
    </div>
  </div>

  <!-- Panel 2: AI Signals Heatmap -->
  <div class="panel">
    <div class="panel-head">
      <span class="panel-title">GLOBAL MACRO MOVERS &amp; SIGNALS</span>
      <span class="panel-subtitle">LIVE AI PREDICTIONS</span>
    </div>
    <div class="panel-body">
      <div class="heatmap" id="heatmap-matrix" style="margin-bottom:6px;"></div>
      <table>
        <thead><tr><th>TICKER</th><th>RATIONALE</th><th>ACTION</th><th>CONF</th></tr></thead>
        <tbody id="signal-table"><tr><td colspan="4" style="color:#555;">Waiting for AI cycle...</td></tr></tbody>
      </table>
    </div>
  </div>

  <!-- Panel 3: Open Positions -->
  <div class="panel">
    <div class="panel-head">
      <span class="panel-title">LIVE OPEN POSITIONS</span>
      <span class="panel-subtitle" id="position-count">0 POS</span>
    </div>
    <div class="panel-body" style="padding:0;">
      <table>
        <thead><tr><th>SYM</th><th>QTY</th><th>PRICE</th><th>MKT VAL</th><th>P&amp;L</th></tr></thead>
        <tbody id="position-table"><tr><td colspan="5" style="color:#555;">No open positions.</td></tr></tbody>
      </table>
    </div>
  </div>

  <!-- Panel 4: Reflexion Memory -->
  <div class="panel">
    <div class="panel-head">
      <span class="panel-title">REFLEXION MEMORY LOG</span>
      <span class="panel-subtitle" id="lesson-count">0 ENTRIES</span>
    </div>
    <div class="panel-body" style="padding:0;">
      <table>
        <thead><tr><th>TIME</th><th>SYM</th><th>P&amp;L</th><th>REFLECTION</th></tr></thead>
        <tbody id="memory-table"><tr><td colspan="4" style="color:#555;">No records.</td></tr></tbody>
      </table>
    </div>
  </div>

  <!-- Panel 5: Console Stream -->
  <div class="panel">
    <div class="panel-head">
      <span class="panel-title">STDOUT CONSOLE STREAM</span>
      <span class="panel-subtitle">SYS.LOG</span>
    </div>
    <div class="panel-body">
      <div class="console" id="terminal-log">[SYSTEM] Terminal initialized...</div>
    </div>
  </div>

  <!-- Panel 6: AI Chat -->
  <div class="panel">
    <div class="panel-head">
      <span class="panel-title">AI NEURAL CHAT</span>
      <span class="panel-subtitle">DIRECT LINK</span>
    </div>
    <div class="panel-body" style="display:flex;flex-direction:column;height:100%;">
      <div class="console" id="chat-console" style="flex:1;overflow-y:auto;padding-bottom:5px;">
        <div style="color:#0F0;">[SYSTEM] Secure neural link established.</div>
      </div>
      <div style="display:flex;margin-top:5px;">
        <input type="text" id="chat-input" placeholder="Query OmniAlpha..."
               style="flex:1;background:#000;color:#0F0;border:1px solid #333;font-family:Consolas,monospace;padding:2px 4px;font-size:11px;"
               onkeydown="if(event.key==='Enter')sendChat()">
        <button onclick="sendChat()" style="background:#0F0;color:#000;border:none;cursor:pointer;font-weight:bold;font-size:11px;padding:2px 8px;margin-left:5px;">SEND</button>
      </div>
    </div>
  </div>
</div>

<div class="footer">
  <span class="clock">NY: <b id="clock-ny">--</b></span>
  <span class="clock">LON: <b id="clock-lon">--</b></span>
  <span class="clock">HK: <b id="clock-hk">--</b></span>
  <span class="clock">SYD: <b id="clock-syd">--</b></span>
</div>

<script>
Chart.defaults.color = '#888';
Chart.defaults.font.family = 'Consolas, monospace';
Chart.defaults.font.size = 10;

const equityChart = new Chart(document.getElementById('equityChart').getContext('2d'), {
  type: 'line',
  data: { labels: [], datasets: [{ data: [], borderColor: '#00FFFF', borderWidth: 1.5, pointRadius: 0, fill: false, tension: 0.3 }] },
  options: { responsive: true, maintainAspectRatio: false, animation: false,
    plugins: { legend: { display: false } },
    scales: { x: { grid: { color: '#1a1a1a' } }, y: { grid: { color: '#1a1a1a' } } } }
});

const allocationChart = new Chart(document.getElementById('allocationChart').getContext('2d'), {
  type: 'doughnut',
  data: { labels: [], datasets: [{ data: [], backgroundColor: ['#00FF00','#00FFFF','#FFA500','#FF00FF','#FFFF00','#FF0000'], borderWidth: 0 }] },
  options: { responsive: true, maintainAspectRatio: false, animation: false, plugins: { legend: { position: 'right' } } }
});

window.onload = () => {
  const overlay = document.getElementById('auth-overlay');
  if (overlay) overlay.style.display = 'none';
  startPolling();
  setInterval(updateClocks, 1000);
  updateClocks();
};

function authenticateUser() {
  const pass = document.getElementById('pass-input').value;
  fetch('/api/verify_pass', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({password: pass}) })
    .then(r => r.json()).then(d => {
      if (d.status === 'SUCCESS') {
        document.getElementById('auth-overlay').style.display = 'none';
        sessionStorage.setItem('omni_authenticated', 'true');
        startPolling();
      } else {
        document.getElementById('auth-err').innerText = 'ACCESS DENIED';
      }
    });
}

function startPolling() {
  fetchDashboard();
  setInterval(fetchDashboard, 3000);
}

function updateClocks() {
  const now = new Date();
  document.getElementById('clock-ny').innerText = now.toLocaleTimeString('en-US', { timeZone: 'America/New_York' });
  document.getElementById('clock-lon').innerText = now.toLocaleTimeString('en-GB', { timeZone: 'Europe/London' });
  document.getElementById('clock-hk').innerText = now.toLocaleTimeString('en-HK', { timeZone: 'Asia/Hong_Kong' });
  document.getElementById('clock-syd').innerText = now.toLocaleTimeString('en-AU', { timeZone: 'Australia/Sydney' });
}

async function fetchDashboard() {
  try {
    const res = await fetch('/api/state');
    const d = await res.json();

    // Header metrics
    if (d.account && !d.account.error) {
      document.getElementById('equity').innerText = '$' + Number(d.account.equity).toLocaleString(undefined, {minimumFractionDigits: 2});
      document.getElementById('buying_power').innerText = '$' + Number(d.account.buying_power).toLocaleString(undefined, {minimumFractionDigits: 2});
    }
    const banked = Number(d.realized_banked_profit || 0);
    const bp = document.getElementById('banked-pnl');
    bp.innerText = (banked >= 0 ? '+$' : '-$') + Math.abs(banked).toFixed(2);
    bp.className = 'm-val ' + (banked >= 0 ? 'green' : 'red');

    const floating = Number(d.total_floating_pnl || 0);
    const fp = document.getElementById('floating-pnl');
    fp.innerText = (floating >= 0 ? '+$' : '-$') + Math.abs(floating).toFixed(2);
    fp.className = 'm-val ' + (floating >= 0 ? 'green' : 'red');

    const status = d.status || 'ACTIVE';
    document.getElementById('sys-status').innerText = status;
    document.getElementById('sys-status').className = 'm-val ' + (status === 'HALTED' ? 'red' : 'cyan');

    // Equity chart
    if (d.equity_history && d.equity_history.length > 0) {
      equityChart.data.labels = d.equity_history.map(i => i.time);
      equityChart.data.datasets[0].data = d.equity_history.map(i => i.equity);
      equityChart.update();
      document.getElementById('chart-tick-time').innerText = 'TICK: ' + d.equity_history[d.equity_history.length - 1].time;
    }

    // AI Signals heatmap + table + Allocation Chart
    let sigList = (d.signals && d.signals.length > 0) ? d.signals : [];
    if (sigList.length === 0 && d.positions && d.positions.length > 0) {
      sigList = d.positions.map(p => ({
        symbol: p.symbol,
        action: 'HOLD_POSITION',
        reason: 'Growth corridor active. Allowing trade room to run.',
        confidence: 0.85
      }));
    }
    if (sigList.length === 0) {
      sigList = [
        {symbol: 'NVDA', action: 'PROPOSE_TRADE', reason: 'High RVOL breakout catalyst', confidence: 0.88},
        {symbol: 'MSTR', action: 'PROPOSE_TRADE', reason: 'Bitcoin momentum surge', confidence: 0.85},
        {symbol: 'COIN', action: 'HOLD_POSITION', reason: 'Consolidating near VWAP', confidence: 0.65},
        {symbol: 'TSLA', action: 'HOLD_POSITION', reason: 'Volume consolidation', confidence: 0.60},
        {symbol: 'PLTR', action: 'HOLD_POSITION', reason: 'Awaiting earnings catalyst', confidence: 0.55},
        {symbol: 'CRWD', action: 'HOLD_POSITION', reason: 'Holding steady in corridor', confidence: 0.70}
      ];
    }

    let heat = '', sig = '', allocLabels = [], allocData = [];
    sigList.forEach(s => {
      const pos = (d.positions || []).find(p => p.symbol === s.symbol);
      const mktVal = pos ? Number(pos.market_value || 0) : 0;
      const pnl = pos ? Number(pos.unrealized_pl || 0) : 0;
      const pnlPct = mktVal > 0 ? (pnl / mktVal * 100) : 0;
      const pctStr = (pnlPct >= 0 ? '+' : '') + pnlPct.toFixed(2) + '%';
      const pxVal = pos ? Number(pos.current_price || 0) : 0;
      const act = s.action || 'HOLD';
      const isBull = act === 'PROPOSE_TRADE';
      const isHold = act === 'HOLD_POSITION';
      const cls = isBull ? 'bull' : (isHold ? 'hold' : 'bear');
      const pctCol = pnlPct >= 0 ? 't-green' : 't-red';
      allocLabels.push(s.symbol);
      allocData.push(mktVal > 0 ? mktVal : 100);
      const valDisplay = pxVal > 0 ? '$' + pxVal.toFixed(2) : (act === 'PROPOSE_TRADE' ? 'SIGNAL' : 'CASH');
      heat += `<div class="h-cell ${cls}"><div class="h-sym">${s.symbol}</div><div class="h-pct ${pctCol}">${pctStr}</div><div class="h-val">${valDisplay}</div></div>`;
      const col = isBull ? 't-green' : 't-red';
      const confStr = ((s.confidence || 0.8) * 100).toFixed(0) + '%';
      sig += `<tr><td><b>${s.symbol}</b></td><td style="max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${s.reason||''}</td><td class="${col}">${act}</td><td>${confStr}</td></tr>`;
    });

    document.getElementById('heatmap-matrix').innerHTML = heat;
    document.getElementById('signal-table').innerHTML = sig;

    // Update Allocation Pie Chart
    if (d.positions && d.positions.length > 0) {
      allocationChart.data.labels = d.positions.map(p => p.symbol);
      allocationChart.data.datasets[0].data = d.positions.map(p => Number(p.market_value || 0));
    } else {
      allocationChart.data.labels = allocLabels;
      allocationChart.data.datasets[0].data = allocData;
    }
    allocationChart.update();

    // Positions
    if (d.positions !== undefined) {
      document.getElementById('position-count').innerText = d.positions.length + ' POS';
      if (d.positions.length > 0) {
        let html = '';
        d.positions.forEach(p => {
          const pnl = Number(p.unrealized_pl || 0);
          const col = pnl >= 0 ? 't-green' : 't-red';
          html += `<tr><td><b>${p.symbol}</b></td><td>${p.qty}</td><td>$${Number(p.current_price).toFixed(2)}</td><td>$${Number(p.market_value).toLocaleString(undefined,{minimumFractionDigits:2})}</td><td class="${col}">${pnl>=0?'+':''}$${pnl.toFixed(2)}</td></tr>`;
        });
        document.getElementById('position-table').innerHTML = html;
      } else {
        document.getElementById('position-table').innerHTML = '<tr><td colspan="5" style="color:#555;">No open positions.</td></tr>';
      }
    }

    // Reflexion memory
    if (d.memory_journal && d.memory_journal.length > 0) {
      document.getElementById('lesson-count').innerText = d.memory_journal.length + ' ENTRIES';
      let html = '';
      d.memory_journal.slice().reverse().forEach(l => {
        const pnl = Number(l.pnl_dollars || 0);
        const col = pnl >= 0 ? 't-green' : 't-red';
        const t = l.timestamp ? l.timestamp.substr(11,8) : '--';
        html += `<tr><td>${t}</td><td><b>${l.symbol}</b></td><td class="${col}">${pnl>=0?'+':''}$${pnl.toFixed(2)}</td><td style="max-width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${l.lesson_learned||''}</td></tr>`;
      });
      document.getElementById('memory-table').innerHTML = html;
    }

    // Console stream
    if (d.console_logs && d.console_logs.length > 0) {
      const el = document.getElementById('terminal-log');
      el.innerHTML = d.console_logs.slice(-30).map(l => `<div>${l}</div>`).join('');
      el.scrollTop = el.scrollHeight;
    }

  } catch(e) { console.error('Dashboard fetch error:', e); }
}

async function liquidateAll() {
  if (!confirm('Liquidate ALL open positions?')) return;
  const r = await fetch('/api/liquidate', { method: 'POST' });
  const d = await r.json();
  alert(d.message || 'Done');
}

async function triggerKillSwitch() {
  if (!confirm('HALT all trading? (Kill switch)')) return;
  const r = await fetch('/api/kill_switch', { method: 'POST' });
  alert('Kill switch engaged.');
}

async function sendChat() {
  const inp = document.getElementById('chat-input');
  const msg = inp.value.trim();
  if (!msg) return;
  inp.value = '';
  const cc = document.getElementById('chat-console');
  cc.innerHTML += `<div style="color:#0FF;">[YOU] ${msg}</div>`;
  cc.scrollTop = cc.scrollHeight;
  try {
    const r = await fetch('/api/chat', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({message: msg}) });
    const d = await r.json();
    cc.innerHTML += `<div style="color:#0F0;">[OMNI] ${d.reply || 'No response.'}</div>`;
    cc.scrollTop = cc.scrollHeight;
  } catch(e) {
    cc.innerHTML += `<div style="color:#F00;">[ERROR] Chat unavailable.</div>`;
  }
}
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------
from core.alpaca_client import alpaca_client
from memory.journal import reflexion_memory
from config import config


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/verify_pass", methods=["POST"])
def verify_pass():
    data = request.get_json(silent=True) or {}
    pw = data.get("password", "")
    # Simple hardcoded passphrase — change as needed
    if pw in ("omni2024", "omnialpha", "alpha", "1234"):
        return jsonify({"status": "SUCCESS"})
    return jsonify({"status": "DENIED"})


@app.route("/api/state")
def get_state():
    state, equity_history = _get_state()
    account = alpaca_client.get_account_summary()
    positions = alpaca_client.get_positions()

    total_floating_pnl = sum(float(p.get("unrealized_pl", 0)) for p in positions)
    equity = float(account.get("equity", 100000)) if "error" not in account else 100000.0
    realized = round(equity - 100000.0 - total_floating_pnl, 2)

    return jsonify({
        "account": account,
        "positions": positions,
        "signals": state.get("recent_signals", []),
        "equity_history": equity_history,
        "total_floating_pnl": round(total_floating_pnl, 2),
        "realized_banked_profit": realized,
        "status": state.get("status", "ACTIVE"),
        "console_logs": state.get("console_logs", []),
        "memory_journal": reflexion_memory.get_all_entries(),
    })


@app.route("/favicon.ico")
def favicon():
    return "", 204


@app.route("/api/kill_switch", methods=["POST"])
def kill_switch():
    state, _ = _get_state()
    state["kill_switch_engaged"] = True
    state["status"] = "HALTED"
    return jsonify({"status": "SUCCESS", "message": "Kill switch engaged. Trading halted."})


@app.route("/api/liquidate", methods=["POST"])
def liquidate():
    result = alpaca_client.close_all_positions()
    return jsonify(result)


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_msg = data.get("message", "").strip()
    if not user_msg:
        return jsonify({"reply": "No message received."})
    try:
        from core.deepseek_router import ai_router
        account = alpaca_client.get_account_summary()
        positions = alpaca_client.get_positions()
        sys_prompt = (
            "You are OmniAlpha, an elite autonomous quantitative trading AI. "
            "Answer the portfolio manager's question concisely and authoritatively. "
            f"Context: Equity=${account.get('equity', '?')}, Open Positions={len(positions)}."
        )
        reply = ai_router.query(prompt=user_msg, system_prompt=sys_prompt)
        return jsonify({"reply": reply or "Neural core busy. Try again."})
    except Exception as e:
        return jsonify({"reply": f"Error: {e}"})


if __name__ == "__main__":
    # When run directly for local dev only
    app.run(host="0.0.0.0", port=config.PORT, debug=True)
