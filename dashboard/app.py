import sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, render_template_string, jsonify
from core.alpaca_client import alpaca_client
from brain.committee import committee
from memory.journal import reflexion_memory
from config import config

app = Flask(__name__)

SYSTEM_STATE = {
    "kill_switch_engaged": False,
    "status": "OPERATIONAL",
    "console_logs": [
        f"[{datetime.now().strftime('%H:%M:%S')}] SYS_INIT: OmniAlpha Quantitative Options Engine Online.",
        f"[{datetime.now().strftime('%H:%M:%S')}] REFLEXION: Self-Learning Memory Store initialized from disk.",
        f"[{datetime.now().strftime('%H:%M:%S')}] ALPACA_API: Connected to paper account ae811ce4-f4dc-47a9-975f-fa2e6b42c169.",
        f"[{datetime.now().strftime('%H:%M:%S')}] SCANNER: Monitoring SEC EDGAR filings & market sentiment velocity."
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
    <title>OmniAlpha AI // QUANTITATIVE OPTIONS DESK</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            background-color: #000000;
            color: #E2E8F0;
            font-family: 'Space Mono', monospace;
            padding: 16px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .top-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: #090D14;
            border: 1px solid #1E2638;
            border-left: 3px solid #00FF66;
            padding: 12px 20px;
        }

        .bar-title {
            font-size: 1.1rem;
            font-weight: 700;
            letter-spacing: 1.5px;
            color: #FFFFFF;
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .bar-title span {
            font-size: 0.75rem;
            color: #64748B;
            font-weight: 400;
        }

        .metrics-row {
            display: flex;
            gap: 20px;
            align-items: center;
        }

        .metric-item {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
        }

        .metric-label {
            font-size: 0.65rem;
            color: #64748B;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        .metric-val {
            font-size: 1.05rem;
            font-weight: 700;
            letter-spacing: 0.5px;
        }

        .txt-green { color: #00FF66; }
        .txt-red { color: #FF3344; }
        .txt-white { color: #FFFFFF; }
        .txt-muted { color: #64748B; }

        .btn-kill {
            background: #1A0507;
            border: 1px solid #FF3344;
            color: #FF3344;
            padding: 6px 14px;
            font-family: 'Space Mono', monospace;
            font-size: 0.75rem;
            font-weight: 700;
            cursor: pointer;
            letter-spacing: 1px;
            transition: all 0.15s ease;
        }
        .btn-kill:hover {
            background: #FF3344;
            color: #000000;
        }

        .grid-main {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 16px;
        }

        .panel {
            background-color: #090D14;
            border: 1px solid #1E2638;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .panel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #1E2638;
            padding-bottom: 8px;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 1.2px;
            color: #94A3B8;
            text-transform: uppercase;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th {
            text-align: left;
            font-size: 0.65rem;
            color: #64748B;
            letter-spacing: 1px;
            text-transform: uppercase;
            padding: 8px 6px;
            border-bottom: 1px solid #1E2638;
        }

        td {
            font-size: 0.8rem;
            padding: 10px 6px;
            border-bottom: 1px solid #121824;
            white-space: nowrap;
        }

        .watch-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
        }

        .watch-card {
            background: #0D131F;
            border: 1px solid #1E2638;
            padding: 10px;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .watch-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .watch-sym { font-weight: 700; font-size: 0.9rem; color: #FFFFFF; }
        .watch-sig { font-size: 0.7rem; font-weight: 700; letter-spacing: 0.5px; }

        .watch-details {
            display: flex;
            justify-content: space-between;
            font-size: 0.7rem;
            color: #64748B;
        }

        .console-box {
            background-color: #04060A;
            border: 1px solid #121824;
            padding: 12px;
            font-size: 0.75rem;
            color: #00FF66;
            height: 140px;
            overflow-y: auto;
            line-height: 1.6;
            font-family: 'Space Mono', monospace;
        }
    </style>
</head>
<body>

    <!-- Header Bar -->
    <div class="top-bar">
        <div class="bar-title">
            OmniAlpha AI // OPTIONS EXECUTION CORE
            <span>ALPACA API • MARKET SCANNER</span>
        </div>
        <div class="metrics-row">
            <div class="metric-item">
                <div class="metric-label">PAPER EQUITY</div>
                <div class="metric-val txt-white" id="equity">$100,000.00</div>
            </div>
            <div class="metric-item">
                <div class="metric-label">NET PROFIT / LOSS</div>
                <div class="metric-val txt-green" id="net-pnl">$0.00 (+0.00%)</div>
            </div>
            <div class="metric-item">
                <div class="metric-label">BUYING POWER</div>
                <div class="metric-val txt-white" id="buying_power">$400,000.00</div>
            </div>
            <div class="metric-item">
                <div class="metric-label">STATUS</div>
                <div class="metric-val txt-green" id="sys-status" style="font-size:0.85rem; padding-top:3px;">[ONLINE]</div>
            </div>
            <button class="btn-kill" onclick="triggerKillSwitch()">KILL SWITCH</button>
        </div>
    </div>

    <!-- Main Grid: Chart & Watchlist -->
    <div class="grid-main">
        <div class="panel">
            <div class="panel-header">
                <div>PORTFOLIO PERFORMANCE CURVE (REAL-TIME EQUITY)</div>
                <div class="txt-muted" id="chart-tick-time">TICK: REALTIME</div>
            </div>
            <canvas id="equityChart" style="max-height: 180px;"></canvas>
        </div>

        <div class="panel">
            <div class="panel-header">
                <div>MARKET WATCHLIST & SENTIMENT EDGE</div>
                <div class="txt-muted">6 TARGETS</div>
            </div>
            <div class="watch-grid" id="watchlist-box">
                <div class="watch-card"><span class="watch-sym">SPY</span><span class="watch-sig txt-green">BULLISH</span></div>
            </div>
        </div>
    </div>

    <!-- Active Open Positions Table -->
    <div class="panel">
        <div class="panel-header">
            <div>LIVE OPEN POSITIONS & UNREALIZED P&L</div>
            <div class="txt-muted" id="position-count">0 ACTIVE POSITIONS</div>
        </div>
        <table>
            <thead>
                <tr>
                    <th>ASSET</th>
                    <th>QTY</th>
                    <th>CURRENT PRICE</th>
                    <th>MARKET VALUE</th>
                    <th>UNREALIZED P&L ($)</th>
                </tr>
            </thead>
            <tbody id="position-table">
                <tr><td colspan="5" class="txt-muted">Fetching live Alpaca positions...</td></tr>
            </tbody>
        </table>
    </div>

    <!-- Signal Feed Table -->
    <div class="panel">
        <div class="panel-header">
            <div>PRE-CATALYST SIGNALS & ORDER FLOW</div>
            <div class="txt-muted">SWARM COMMITTEE</div>
        </div>
        <table>
            <thead>
                <tr>
                    <th>TICKER</th>
                    <th>SIGNAL RATIONALE</th>
                    <th>STRATEGY</th>
                    <th>CONF</th>
                    <th>MAX RISK</th>
                    <th>MAX REWARD</th>
                </tr>
            </thead>
            <tbody id="signal-table">
                <tr><td colspan="6" class="txt-muted">Scanning live order flow...</td></tr>
            </tbody>
        </table>
    </div>

    <!-- Reflexion Memory Table -->
    <div class="panel">
        <div class="panel-header">
            <div>TRADE JOURNAL & DYNAMIC REFLEXION MEMORY</div>
            <div class="txt-muted" id="lesson-count">0 LESSONS</div>
        </div>
        <table>
            <thead>
                <tr>
                    <th>TIME</th>
                    <th>TICKER</th>
                    <th>STRATEGY</th>
                    <th>P&L</th>
                    <th>POST-MORTEM REFLECTION</th>
                </tr>
            </thead>
            <tbody id="memory-table">
                <tr><td colspan="5" class="txt-muted">Recording execution logs...</td></tr>
            </tbody>
        </table>
    </div>

    <!-- System Console -->
    <div class="panel">
        <div class="panel-header">SYSTEM CONSOLE STDOUT STREAM</div>
        <div class="console-box" id="terminal-log">
            [00:00:01] SYS_INIT: OmniAlpha Quantitative Options Engine Online.<br>
        </div>
    </div>

    <script>
        const ctx = document.getElementById('equityChart').getContext('2d');
        const equityChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Portfolio Equity ($)',
                    data: [],
                    borderColor: '#00FF66',
                    borderWidth: 1.8,
                    tension: 0.2,
                    pointRadius: 3,
                    pointBackgroundColor: '#00FF66',
                    fill: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { color: '#121824' }, ticks: { color: '#64748B', font: { family: 'Space Mono' } } },
                    y: { grid: { color: '#121824' }, ticks: { color: '#64748B', font: { family: 'Space Mono' } } }
                }
            }
        });

        async function fetchDashboard() {
            try {
                const res = await fetch('/api/state');
                const data = await res.json();
                
                if (data.account && !data.account.error) {
                    const eq = Number(data.account.equity);
                    document.getElementById('equity').innerText = '$' + eq.toLocaleString(undefined, {minimumFractionDigits: 2});
                    document.getElementById('buying_power').innerText = '$' + Number(data.account.buying_power).toLocaleString(undefined, {minimumFractionDigits: 2});
                    
                    const diff = eq - 100000.0;
                    const pct = (diff / 100000.0) * 100;
                    const pnlElem = document.getElementById('net-pnl');
                    const sign = diff >= 0 ? '+' : '';
                    pnlElem.innerText = `${sign}$${diff.toFixed(2)} (${sign}${pct.toFixed(2)}%)`;
                    pnlElem.className = 'metric-val ' + (diff >= 0 ? 'txt-green' : 'txt-red');
                }

                if (data.equity_history && data.equity_history.length > 0) {
                    const labels = data.equity_history.map(item => item.time);
                    const values = data.equity_history.map(item => item.equity);
                    
                    equityChart.data.labels = labels;
                    equityChart.data.datasets[0].data = values;
                    
                    // Color code chart line green if profit, red if drawdown
                    const currentEquity = values[values.length - 1];
                    const chartColor = currentEquity >= 100000 ? '#00FF66' : '#FF3344';
                    equityChart.data.datasets[0].borderColor = chartColor;
                    equityChart.data.datasets[0].pointBackgroundColor = chartColor;
                    
                    equityChart.update();
                    document.getElementById('chart-tick-time').innerText = 'LAST TICK: ' + labels[labels.length - 1];
                }
                
                if (data.positions && data.positions.length > 0) {
                    let posHtml = '';
                    data.positions.forEach(p => {
                        const pnl = Number(p.unrealized_pl || 0);
                        const col = pnl >= 0 ? 'txt-green' : 'txt-red';
                        const sign = pnl >= 0 ? '+' : '';
                        posHtml += `<tr>
                            <td><b>${p.symbol}</b></td>
                            <td>${p.qty}</td>
                            <td>$${Number(p.current_price).toFixed(2)}</td>
                            <td>$${Number(p.market_value).toFixed(2)}</td>
                            <td class="${col}">${sign}$${pnl.toFixed(2)}</td>
                        </tr>`;
                    });
                    document.getElementById('position-table').innerHTML = posHtml;
                    document.getElementById('position-count').innerText = data.positions.length + ' ACTIVE POSITIONS';
                }

                if (data.signals && data.signals.length > 0) {
                    let html = '';
                    let watchHtml = '';
                    
                    data.signals.forEach(s => {
                        const conf = s.confidence ? (s.confidence * 100).toFixed(0) + '%' : '-';
                        const strat = s.strategy_type || 'HOLD';
                        const isBull = strat.includes('BULL');
                        const isBear = strat.includes('BEAR');
                        const col = isBull ? 'txt-green' : (isBear ? 'txt-red' : 'txt-muted');
                        
                        // Find matching live price if available
                        const pos = (data.positions || []).find(p => p.symbol === s.symbol);
                        const pxStr = pos ? `$${Number(pos.current_price).toFixed(2)}` : 'LIVE';

                        html += `<tr>
                            <td><b>${s.symbol}</b></td>
                            <td>${s.reason}</td>
                            <td class="${col}">${strat}</td>
                            <td>${conf}</td>
                            <td>$${s.max_loss ? s.max_loss.toFixed(2) : '0.00'}</td>
                            <td>$${s.max_gain ? s.max_gain.toFixed(2) : '0.00'}</td>
                        </tr>`;

                        watchHtml += `<div class="watch-card">
                            <div class="watch-top">
                                <span class="watch-sym">${s.symbol}</span>
                                <span class="watch-sig ${col}">${isBull ? 'BULLISH' : (isBear ? 'BEARISH' : 'HOLD')}</span>
                            </div>
                            <div class="watch-details">
                                <span>PRICE: ${pxStr}</span>
                                <span>CONF: ${conf}</span>
                            </div>
                        </div>`;
                    });
                    
                    document.getElementById('signal-table').innerHTML = html;
                    document.getElementById('watchlist-box').innerHTML = watchHtml;
                }

                if (data.memory_journal && data.memory_journal.length > 0) {
                    let memHtml = '';
                    data.memory_journal.forEach(m => {
                        const pnlVal = Number(m.pnl_dollars || 0);
                        const pnlColor = pnlVal >= 0 ? 'txt-green' : 'txt-red';
                        const sign = pnlVal >= 0 ? '+' : '';
                        memHtml += `<tr>
                            <td>${new Date(m.timestamp).toLocaleTimeString()}</td>
                            <td><b>${m.symbol}</b></td>
                            <td>${m.strategy}</td>
                            <td class="${pnlColor}">${sign}$${pnlVal.toFixed(2)}</td>
                            <td>${m.lesson_learned}</td>
                        </tr>`;
                    });
                    document.getElementById('memory-table').innerHTML = memHtml;
                    document.getElementById('lesson-count').innerText = data.memory_journal.length + ' LESSONS';
                }

                if (data.console_logs && data.console_logs.length > 0) {
                    const consoleBox = document.getElementById('terminal-log');
                    consoleBox.innerHTML = data.console_logs.join('<br>');
                    consoleBox.scrollTop = consoleBox.scrollHeight;
                }
            } catch(e) {}
        }

        async function triggerKillSwitch() {
            if (confirm("Engage Emergency Kill Switch?")) {
                const res = await fetch('/api/kill_switch', {method: 'POST'});
                const data = await res.json();
                document.getElementById('sys-status').innerText = '[HALTED]';
                document.getElementById('sys-status').className = 'metric-val txt-red';
                alert(data.message);
            }
        }

        setInterval(fetchDashboard, 3000);
        fetchDashboard();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/state')
def get_state():
    account = alpaca_client.get_account_summary()
    positions = alpaca_client.get_positions()
    signals = []
    
    # Record equity point in EQUITY_HISTORY buffer
    if account and "equity" in account:
        now_str = datetime.now().strftime('%H:%M:%S')
        eq_val = float(account["equity"])
        EQUITY_HISTORY.append({"time": now_str, "equity": eq_val})
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
                l["lesson_learned"] = f"Intraday price drift -$abs({pnl:.2f}). Applying 5% confidence penalty for next entry."

    if not SYSTEM_STATE["kill_switch_engaged"]:
        for sym in config.TARGET_SYMBOLS:
            eval_res = committee.evaluate_opportunity(sym, account)
            signals.append(eval_res)
            
    # Add heartbeat console log entry
    add_console_log(f"PORTFOLIO: Active equity ${account.get('equity', 100000.0):,.2f} | {len(positions)} live positions synced.")

    return jsonify({
        "account": account,
        "positions": positions,
        "signals": signals,
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

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=config.PORT, debug=True)
