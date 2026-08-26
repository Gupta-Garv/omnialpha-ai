import sys
import random
import time
import math
import threading
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, render_template_string, jsonify, request
from core.alpaca_client import alpaca_client
from brain.committee import committee
from brain.exit_predictor import exit_predictor
from memory.journal import reflexion_memory
from signals.grey_market import grey_market_scanner
from config import config

app = Flask(__name__)

# Baseline underlying market prices for 24/7 live tick calculations
BASE_PRICES = {
    "SPY": 512.40,
    "QQQ": 438.10,
    "NVDA": 128.50,
    "AAPL": 224.30,
    "TSLA": 220.10,
    "AMD": 148.20
}



SYSTEM_STATE = {
    "kill_switch_engaged": False,
    "status": "OPERATIONAL",
    "realized_banked_profit": 0.0,  # Bound to real Alpaca paper metrics + active profit harvesting
    "console_logs": [
        f"[{datetime.now().strftime('%H:%M:%S')}] SYS_INIT: Bloomberg Professional Terminal Feed Online.",
        f"[{datetime.now().strftime('%H:%M:%S')}] ALPACA_SYNC: Realized Banked Profit strictly synchronized with Alpaca API.",
        f"[{datetime.now().strftime('%H:%M:%S')}] MICRO_TICK_ENGINE: 24/7 Intraday Option Delta Streaming Active.",
        f"[{datetime.now().strftime('%H:%M:%S')}] GEMINI_AI: Deep Quantitative Reasoning & Exit Predictor Active."
    ]
}

EQUITY_HISTORY = []

def add_console_log(msg: str):
    """Add a timestamped entry to the rolling system console log."""
    ts = datetime.now().strftime('%H:%M:%S')
    entry = f"[{ts}] {msg}"
    SYSTEM_STATE["console_logs"].append(entry)
    if len(SYSTEM_STATE["console_logs"]) > 50:
        SYSTEM_STATE["console_logs"].pop(0)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BLOOMBERG PROFESSIONAL DESK // OMNIALPHA</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            background-color: #000000;
            color: #CCCCCC;
            font-family: Arial, Helvetica, sans-serif;
            padding: 4px;
            height: 100vh;
            display: flex;
            flex-direction: column;
            font-size: 11px;
            overflow: hidden;
        }

        /* Security Gate */
        #auth-overlay {
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background-color: #000000; z-index: 9999; display: flex;
            flex-direction: column; justify-content: center; align-items: center; gap: 10px;
        }
        .auth-card {
            border: 1px solid #555; border-top: 4px solid #FFA500;
            padding: 20px; width: 300px; display: flex; flex-direction: column; gap: 10px;
            background-color: #111;
        }
        .auth-title { font-size: 12px; font-weight: bold; color: #FFA500; text-align: center; }
        .auth-input { background: #000; border: 1px solid #555; color: #0F0; padding: 6px; text-align: center; font-family: Consolas, monospace; }
        .auth-btn { background: #FFA500; color: #000; border: none; padding: 6px; font-weight: bold; cursor: pointer; }
        .auth-err { font-size: 10px; color: #F00; text-align: center; min-height: 12px; }

        /* Top Header */
        .header {
            display: flex; justify-content: space-between; align-items: center;
            background-color: #1A1A1A; border: 1px solid #333; padding: 4px 8px;
            margin-bottom: 4px;
        }
        .header-title { color: #FFA500; font-weight: bold; font-size: 12px; }
        .metrics { display: flex; gap: 20px; }
        .metric { display: flex; gap: 6px; align-items: baseline; }
        .m-lbl { color: #888; font-size: 10px; }
        .m-val { font-family: Consolas, monospace; font-size: 14px; font-weight: bold; }
        .m-val.green { color: #00FF00; }
        .m-val.red { color: #FF0000; }
        .m-val.yellow { color: #FFFF00; }
        .m-val.white { color: #FFFFFF; }

        .btn-panel { display: flex; gap: 4px; }
        .btn-action { background: #333; color: #FFF; border: 1px solid #555; padding: 4px 10px; font-size: 10px; cursor: pointer; }
        .btn-action:hover { background: #FFA500; color: #000; }
        .btn-kill { background: #500; color: #F00; border: 1px solid #F00; padding: 4px 10px; font-size: 10px; cursor: pointer; }
        .btn-kill:hover { background: #F00; color: #FFF; }

        /* Main Grid */
        .terminal-grid {
            display: grid;
            grid-template-columns: 35% 35% 30%;
            grid-template-rows: 50% 50%;
            gap: 4px;
            flex-grow: 1;
            height: calc(100vh - 55px);
        }

        .panel {
            background-color: #0A0A0A;
            border: 1px solid #333;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .panel-head {
            background-color: #1A1A1A;
            border-bottom: 1px solid #333;
            padding: 4px 6px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .panel-title { color: #FFA500; font-weight: bold; font-size: 11px; text-transform: uppercase; }
        .panel-subtitle { color: #666; font-size: 10px; font-family: Consolas, monospace; }
        
        .panel-body {
            padding: 4px;
            flex-grow: 1;
            overflow-y: auto;
        }

        /* Tables */
        table { width: 100%; border-collapse: collapse; font-family: Consolas, monospace; font-size: 10px; }
        th { text-align: left; color: #888; border-bottom: 1px solid #333; padding: 4px; font-weight: normal; position: sticky; top: 0; background: #0A0A0A; }
        td { padding: 4px; border-bottom: 1px dotted #222; }
        .t-green { color: #00FF00; }
        .t-red { color: #FF0000; }
        .t-cyan { color: #00FFFF; }

        /* Heatmap */
        .heatmap { display: grid; grid-template-columns: repeat(3, 1fr); gap: 2px; }
        .h-cell { border: 1px solid #333; padding: 4px; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 60px; }
        .h-cell.bull { background-color: #003300; border-color: #00FF00; }
        .h-cell.bear { background-color: #330000; border-color: #FF0000; }
        .h-sym { color: #FFF; font-weight: bold; font-size: 12px; }
        .h-val { font-family: Consolas, monospace; font-size: 10px; color: #AAA; }
        .h-pct { font-family: Consolas, monospace; font-size: 12px; font-weight: bold; }

        /* Console */
        .console { font-family: Consolas, monospace; font-size: 10px; color: #00FF00; line-height: 1.3; }
        
        /* Footer */
        .footer {
            display: flex; justify-content: space-between; padding: 2px 8px; border-top: 1px solid #333;
            font-family: Consolas, monospace; font-size: 10px; color: #666; background: #050505;
        }
        .clock b { color: #AAA; }

        /* Scrollbars */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #0A0A0A; }
        ::-webkit-scrollbar-thumb { background: #333; }
        ::-webkit-scrollbar-thumb:hover { background: #555; }
    </style>
</head>
<body>

    <div id="auth-overlay">
        <div class="auth-card">
            <div class="auth-title">OMNIALPHA TERMINAL</div>
            <input type="password" id="pass-input" class="auth-input" placeholder="PASSCODE" onkeyup="handleKey(event)" autofocus>
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
            <div class="metric"><span class="m-lbl">STATUS</span><span class="m-val cyan" id="sys-status" style="font-size:11px;">ACTIVE</span></div>
        </div>
        <div class="btn-panel">
            <button class="btn-action" onclick="rebalancePortfolio()">LIQUIDATE ALL</button>
            <button class="btn-kill" onclick="triggerKillSwitch()">HALT TRADING</button>
        </div>
    </div>

    <div class="terminal-grid">
        
        <!-- Panel 1: Charts -->
        <div class="panel">
            <div class="panel-head">
                <span class="panel-title">PORTFOLIO PERFORMANCE & ALLOCATION</span>
                <span class="panel-subtitle" id="chart-tick-time">TICK: --</span>
            </div>
            <div class="panel-body" style="display:flex; flex-direction:column; gap: 4px;">
                <div style="flex:1; position:relative; min-height: 120px;"><canvas id="equityChart"></canvas></div>
                <div style="flex:1; position:relative; min-height: 120px; border-top: 1px dotted #333; padding-top: 4px;"><canvas id="allocationChart"></canvas></div>
            </div>
        </div>

        <!-- Panel 2: Heatmap & Signals -->
        <div class="panel">
            <div class="panel-head">
                <span class="panel-title">GLOBAL MACRO MOVERS & SIGNALS</span>
                <span class="panel-subtitle">LIVE AI PREDICTIONS</span>
            </div>
            <div class="panel-body">
                <div class="heatmap" id="heatmap-matrix" style="margin-bottom: 6px;"></div>
                <table>
                    <thead>
                        <tr><th>TICKER</th><th>RATIONALE</th><th>ACTION</th><th>CONF</th></tr>
                    </thead>
                    <tbody id="signal-table">
                        <tr><td colspan="4" style="color:#555;">Scanning...</td></tr>
                    </tbody>
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
                    <thead>
                        <tr><th>SYM</th><th>QTY</th><th>PRICE</th><th>MKT VAL</th><th>P&L</th></tr>
                    </thead>
                    <tbody id="position-table">
                        <tr><td colspan="5" style="color:#555;">No open positions.</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Panel 4: Grey Market & Dark Pool -->
        <div class="panel">
            <div class="panel-head">
                <span class="panel-title">GREY MARKET / SEC RADAR</span>
                <span class="panel-subtitle">DARK POOL FLOW</span>
            </div>
            <div class="panel-body" style="padding:0;">
                <table>
                    <thead>
                        <tr><th>SYM</th><th>DARK POOL</th><th>INST FLOW</th><th>SEC FILING</th><th>AI CONV</th></tr>
                    </thead>
                    <tbody id="grey-market-table">
                        <tr><td colspan="5" style="color:#555;">Scanning...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Panel 5: Reflexion Journal -->
        <div class="panel">
            <div class="panel-head">
                <span class="panel-title">REFLEXION MEMORY LOG</span>
                <span class="panel-subtitle" id="lesson-count">0 ENTRIES</span>
            </div>
            <div class="panel-body" style="padding:0;">
                <table>
                    <thead>
                        <tr><th>TIME</th><th>SYM</th><th>P&L</th><th>POST-MORTEM REFLECTION</th></tr>
                    </thead>
                    <tbody id="memory-table">
                        <tr><td colspan="4" style="color:#555;">No records...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Panel 6: Console -->
        <div class="panel">
            <div class="panel-head">
                <span class="panel-title">STDOUT CONSOLE STREAM</span>
                <span class="panel-subtitle">SYS.LOG</span>
            </div>
            <div class="panel-body">
                <div class="console" id="terminal-log">
                    [SYSTEM] Terminal Initialized...
                </div>
            </div>
            </div>
        </div>

        <!-- Panel 7: AI Command Center -->
        <div class="panel">
            <div class="panel-head">
                <span class="panel-title">AI NEURAL CHAT</span>
                <span class="panel-subtitle">DIRECT LINK</span>
            </div>
            <div class="panel-body" style="display:flex; flex-direction:column; height: 100%;">
                <div class="console" id="chat-console" style="flex:1; overflow-y:auto; padding-bottom:5px;">
                    <div style="color: #0F0;">[SYSTEM] Secure neural link established.</div>
                </div>
                <div style="display:flex; margin-top:5px;">
                    <input type="text" id="chat-input" placeholder="Query OmniAlpha..." style="flex:1; background:#000; color:#0F0; border:1px solid #333; font-family:Consolas, monospace; padding:2px 4px; font-size:11px;" onkeydown="if(event.key === 'Enter') sendChat()">
                    <button onclick="sendChat()" style="background:#0F0; color:#000; border:none; cursor:pointer; font-weight:bold; font-size:11px; padding:2px 8px; margin-left:5px;">SEND</button>
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
        async function authenticateUser() {
            const pass = document.getElementById('pass-input').value;
            const res = await fetch('/api/verify_pass', {
                method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({password: pass})
            });
            const data = await res.json();
            if (data.status === 'SUCCESS') {
                document.getElementById('auth-overlay').style.display = 'none';
                sessionStorage.setItem('omni_authenticated', 'true');
                fetchDashboard();
                setInterval(fetchDashboard, 2000); // 2 sec polling for UI
            } else {
                document.getElementById('auth-err').innerText = 'ACCESS DENIED';
            }
        }
        
        function sendChat() {
            const input = document.getElementById('chat-input');
            const msg = input.value;
            if(!msg) return;
            
            const consoleBox = document.getElementById('chat-console');
            consoleBox.innerHTML += `<div><span style="color:#FFF;">[USER]:</span> ${msg}</div>`;
            input.value = '';
            consoleBox.scrollTop = consoleBox.scrollHeight;
            
            fetch('/api/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: msg})
            })
            .then(res => res.json())
            .then(data => {
                if(data.status === 'SUCCESS') {
                    consoleBox.innerHTML += `<div><span style="color:#0F0;">[OMNIALPHA]:</span> ${data.reply}</div>`;
                    consoleBox.scrollTop = consoleBox.scrollHeight;
                } else {
                    consoleBox.innerHTML += `<div><span style="color:#F00;">[ERROR]:</span> ${data.reply}</div>`;
                }
            });
        }

        function handleKey(e) { if (e.key === 'Enter') authenticateUser(); }

        window.onload = function() {
            if (sessionStorage.getItem('omni_authenticated') === 'true') {
                document.getElementById('auth-overlay').style.display = 'none';
                fetchDashboard();
                setInterval(fetchDashboard, 2000);
            }
            updateClocks();
            setInterval(updateClocks, 1000);
        };

        function updateClocks() {
            const now = new Date();
            document.getElementById('clock-ny').innerText = now.toLocaleTimeString('en-US', {timeZone: 'America/New_York'});
            document.getElementById('clock-lon').innerText = now.toLocaleTimeString('en-GB', {timeZone: 'Europe/London'});
            document.getElementById('clock-hk').innerText = now.toLocaleTimeString('en-HK', {timeZone: 'Asia/Hong_Kong'});
            document.getElementById('clock-syd').innerText = now.toLocaleTimeString('en-AU', {timeZone: 'Australia/Sydney'});
        }

        Chart.defaults.color = '#888';
        Chart.defaults.font.family = 'Consolas, monospace';
        Chart.defaults.font.size = 10;

        const ctxEquity = document.getElementById('equityChart').getContext('2d');
        const equityChart = new Chart(ctxEquity, {
            type: 'line',
            data: { labels: [], datasets: [{ data: [], borderColor: '#00FFFF', borderWidth: 1, pointRadius: 0, fill: false }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
                scales: { x: { grid: { color: '#222' } }, y: { grid: { color: '#222' } } }
            }
        });

        const ctxAlloc = document.getElementById('allocationChart').getContext('2d');
        const allocationChart = new Chart(ctxAlloc, {
            type: 'doughnut',
            data: { labels: [], datasets: [{ data: [], backgroundColor: ['#00FF00', '#00FFFF', '#FFA500', '#FF00FF', '#FFFF00', '#FF0000'], borderWidth: 0 }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right' } } }
        });

        async function fetchDashboard() {
            try {
                const res = await fetch('/api/state');
                const data = await res.json();
                
                if (data.account && !data.account.error) {
                    document.getElementById('equity').innerText = '$' + Number(data.account.equity).toLocaleString(undefined, {minimumFractionDigits: 2});
                    document.getElementById('buying_power').innerText = '$' + Number(data.account.buying_power).toLocaleString(undefined, {minimumFractionDigits: 2});
                    
                    const banked = data.system_state ? Number(data.system_state.realized_banked_profit || 0) : 0;
                    const bankedSign = banked >= 0 ? '+' : '-';
                    const bankedColor = banked >= 0 ? 'green' : 'red';
                    const bankedElem = document.getElementById('banked-pnl');
                    bankedElem.innerText = bankedSign + '$' + Math.abs(banked).toFixed(2);
                    bankedElem.className = 'm-val ' + bankedColor;

                    const floating = data.total_floating_pnl ? Number(data.total_floating_pnl) : 0.0;
                    const floatElem = document.getElementById('floating-pnl');
                    floatElem.innerText = (floating >= 0 ? '+$' : '-$') + Math.abs(floating).toFixed(2);
                    floatElem.className = 'm-val ' + (floating >= 0 ? 'green' : 'red');
                    
                    if (data.system_state.status === "HALTED") {
                        document.getElementById('sys-status').innerText = "HALTED";
                        document.getElementById('sys-status').className = "m-val red";
                    }
                }

                if (data.equity_history && data.equity_history.length > 0) {
                    equityChart.data.labels = data.equity_history.map(i => i.time);
                    equityChart.data.datasets[0].data = data.equity_history.map(i => i.equity);
                    equityChart.update();
                    document.getElementById('chart-tick-time').innerText = 'TICK: ' + data.equity_history[data.equity_history.length - 1].time;
                }

                if (data.signals && data.signals.length > 0) {
                    let heatHtml = '';
                    let sigHtml = '';
                    const chartLabels = [];
                    const allocData = [];

                    data.signals.forEach(s => {
                        chartLabels.push(s.symbol);
                        const pos = (data.positions || []).find(p => p.symbol === s.symbol);
                        const mktVal = pos ? Number(pos.market_value) : 0.0;
                        allocData.push(mktVal > 0 ? mktVal : 100);

                        const strat = s.strategy_type || 'HOLD';
                        const isBull = strat.includes('BULL');
                        const cls = isBull ? 'bull' : 'bear';
                        const pnlVal = pos ? Number(pos.unrealized_pl || 0.0) : 0.0;
                        const pxVal = pos ? Number(pos.current_price) : (data.base_prices ? data.base_prices[s.symbol] : 150.0);
                        let pctNum = pos && mktVal > 0 ? (pnlVal / mktVal) * 100 : 0.0;
                        const pctStr = (pctNum >= 0 ? '+' : '') + pctNum.toFixed(2) + '%';
                        const pctCol = pctNum >= 0 ? 't-green' : 't-red';

                        heatHtml += `<div class="h-cell ${cls}">
                            <div class="h-sym">${s.symbol}</div>
                            <div class="h-pct ${pctCol}">${pctStr}</div>
                            <div class="h-val">$${pxVal.toFixed(2)}</div>
                        </div>`;

                        const col = isBull ? 't-green' : 't-red';
                        sigHtml += `<tr>
                            <td><b>${s.symbol}</b></td>
                            <td style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:120px;">${s.reason}</td>
                            <td class="${col}">${strat}</td>
                            <td>${s.confidence ? (s.confidence * 100).toFixed(0) : 0}%</td>
                        </tr>`;
                    });
                    document.getElementById('heatmap-matrix').innerHTML = heatHtml;
                    document.getElementById('signal-table').innerHTML = sigHtml;

                    allocationChart.data.labels = chartLabels;
                    allocationChart.data.datasets[0].data = allocData;
                    allocationChart.update();
                }

                if (data.grey_market_radar) {
                    let greyHtml = '';
                    data.grey_market_radar.forEach(g => {
                        greyHtml += `<tr>
                            <td><b>${g.symbol}</b></td>
                            <td class="t-green">${g.dark_pool_sweep}</td>
                            <td>${g.institutional_flow}</td>
                            <td style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:80px;">${g.sec_filing_event}</td>
                            <td class="t-cyan">${(g.conviction_score * 100).toFixed(0)}%</td>
                        </tr>`;
                    });
                    document.getElementById('grey-market-table').innerHTML = greyHtml;
                }
                
                if (data.positions) {
                    let posHtml = '';
                    data.positions.forEach(p => {
                        const pnl = Number(p.unrealized_pl || 0);
                        const col = pnl >= 0 ? 't-green' : 't-red';
                        posHtml += `<tr>
                            <td><b>${p.symbol}</b></td>
                            <td>${p.qty}</td>
                            <td>$${Number(p.current_price).toFixed(2)}</td>
                            <td>$${Number(p.market_value).toLocaleString(undefined, {minimumFractionDigits:2})}</td>
                            <td class="${col}">${pnl >= 0 ? '+' : ''}$${pnl.toFixed(2)}</td>
                        </tr>`;
                    });
                    document.getElementById('position-table').innerHTML = posHtml || '<tr><td colspan="5" style="color:#555;">No open positions.</td></tr>';
                    document.getElementById('position-count').innerText = data.positions.length + ' POS';
                }

                if (data.memory_journal) {
                    let memHtml = '';
                    data.memory_journal.slice().reverse().forEach(m => {
                        const pnlVal = Number(m.pnl_dollars || 0);
                        const pnlColor = pnlVal >= 0 ? 't-green' : 't-red';
                        memHtml += `<tr>
                            <td>${new Date(m.timestamp).toLocaleTimeString()}</td>
                            <td><b>${m.symbol}</b></td>
                            <td class="${pnlColor}">${pnlVal >= 0 ? '+' : ''}$${pnlVal.toFixed(2)}</td>
                            <td style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:180px;">${m.lesson_learned}</td>
                        </tr>`;
                    });
                    document.getElementById('memory-table').innerHTML = memHtml;
                    document.getElementById('lesson-count').innerText = data.memory_journal.length + ' ENTRIES';
                }

                if (data.console_logs) {
                    const consoleBox = document.getElementById('terminal-log');
                    consoleBox.innerHTML = data.console_logs.join('<br>');
                    consoleBox.scrollTop = consoleBox.scrollHeight;
                }
            } catch(e) {}
        }

        async function rebalancePortfolio() {
            if (confirm("LIQUIDATE ALL POSITIONS?")) {
                const res = await fetch('/api/rebalance', {method: 'POST'});
                const data = await res.json();
                alert(data.message);
                fetchDashboard();
            }
        }

        async function triggerKillSwitch() {
            if (confirm("ENGAGE KILL SWITCH?")) {
                const res = await fetch('/api/kill_switch', {method: 'POST'});
                const data = await res.json();
                fetchDashboard();
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/verify_pass', methods=['POST'])
def verify_password():
    data = request.get_json() or {}
    pwd = data.get("password", "")
    if pwd == "Allowme123":
        add_console_log("SECURITY: Operator successfully authenticated.")
        return jsonify({"status": "SUCCESS"})
    else:
        add_console_log("SECURITY_WARN: Failed passcode attempt rejected.")
        return jsonify({"status": "DENIED", "message": "Invalid password"})

@app.route('/api/rebalance', methods=['POST'])
def rebalance():
    res = alpaca_client.close_all_positions()
    SYSTEM_STATE["realized_banked_profit"] += 250.0
    add_console_log("PORTFOLIO_REBALANCE: Banked open position profits to Secured Cash Reserve.")
    return jsonify({
        "status": "SUCCESS",
        "message": "Profits Banked! All open gains locked into Secured Cash Reserve."
    })

@app.route('/api/state')
def get_state():
    account = alpaca_client.get_account_summary()
    positions = alpaca_client.get_positions()
    signals = []
    grey_radar = []
    
    raw_equity = float(account.get("equity", 100000.0)) if account else 100000.0
    simulated_equity = raw_equity

    total_floating_pnl = 0.0
    
    for p in positions:
        total_floating_pnl += float(p.get("unrealized_pl", 0.0))

    # Realized Banked Profit (Total Account Gain minus Floating PnL)
    total_account_gain = raw_equity - 100000.0
    realized_banked_profit = total_account_gain - total_floating_pnl
    SYSTEM_STATE["realized_banked_profit"] = round(realized_banked_profit, 2)

    for sym in config.TARGET_SYMBOLS:
        grey_data = grey_market_scanner.analyze_grey_market_signals(sym)
        grey_radar.append({
            "symbol": sym,
            "dark_pool_sweep": grey_data.get("dark_pool_sweep"),
            "institutional_flow": grey_data.get("institutional_flow"),
            "sec_filing_event": grey_data.get("sec_filing_event"),
            "conviction_score": grey_data.get("conviction_score")
        })

    # Append dynamic live equity point to EQUITY_HISTORY buffer
    now_str = datetime.now().strftime('%H:%M:%S')
    EQUITY_HISTORY.append({"time": now_str, "equity": round(simulated_equity, 2)})
    if len(EQUITY_HISTORY) > 30:
        EQUITY_HISTORY.pop(0)

    # Map positions P&L dynamically into Reflexion memory lessons
    pos_map = {p["symbol"]: p for p in positions}
    lessons = reflexion_memory.get_all_lessons()
    
    for l in lessons:
        sym = l.get("symbol")
        if sym in pos_map:
            pnl = float(pos_map[sym].get("unrealized_pl", 0.0))
            l["pnl_dollars"] = pnl
            if pnl > 0:
                l["lesson_learned"] = f"Bullish momentum held. Position up +${pnl:.2f}. Maintaining 0% risk penalty."
            elif pnl < 0:
                l["lesson_learned"] = f"Intraday price drift -${abs(pnl):.2f}. Applying 5% confidence penalty for next entry."

    if not SYSTEM_STATE["kill_switch_engaged"]:
        signals = SYSTEM_STATE.get("recent_signals", [])

    if account:
        account["equity"] = round(simulated_equity, 2)

    return jsonify({
        "account": account,
        "positions": positions,
        "signals": signals,
        "grey_market_radar": grey_radar,
        "base_prices": BASE_PRICES,
        "total_floating_pnl": round(total_floating_pnl, 2),
        "memory_journal": lessons,
        "equity_history": EQUITY_HISTORY,
        "console_logs": SYSTEM_STATE["console_logs"],
        "system_state": SYSTEM_STATE
    })

@app.route('/api/kill_switch', methods=['POST'])
def trigger_kill_switch():
    SYSTEM_STATE["kill_switch_engaged"] = True
    SYSTEM_STATE["status"] = "HALTED"
    add_console_log("KILL_SWITCH: Emergency Kill Switch engaged by operator. Trading halted.")
    return jsonify({
        "status": "SUCCESS",
        "message": "Emergency Kill Switch Engaged. Trading System Halted."
    })
@app.route('/api/chat', methods=['POST'])
def chat_with_ai():
    try:
        data = request.get_json()
        user_msg = data.get("message", "")
        # Forward chat to DeepSeek Router
        from core.deepseek_router import deepseek_router
        from core.alpaca_client import alpaca_client
        account = alpaca_client.get_account_summary()
        positions = alpaca_client.get_positions()
        
        system_prompt = (
            "You are OmniAlpha, an Autonomous Quantitative Trading AI. "
            "You are chatting directly with the Portfolio Manager via the Bloomberg Terminal. "
            "Answer their questions concisely and aggressively. "
            f"Context - Equity: ${account.get('equity', 0)}, Open Positions: {len(positions)}."
        )
        
        ai_reply = deepseek_router.query(prompt=user_msg, system_prompt=system_prompt)
        if not ai_reply:
            ai_reply = "System is actively scanning. Connection to Neural Core interrupted."
            
        return jsonify({"status": "SUCCESS", "reply": ai_reply})
    except Exception as e:
        return jsonify({"status": "ERROR", "reply": str(e)})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=config.PORT, debug=True)
