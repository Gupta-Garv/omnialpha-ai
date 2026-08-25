import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, render_template_string, jsonify, request
from core.alpaca_client import alpaca_client
from brain.committee import committee
from memory.journal import reflexion_memory
from config import config

app = Flask(__name__)

SYSTEM_STATE = {
    "kill_switch_engaged": False,
    "status": "OPERATIONAL"
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OmniAlpha AI — Institutional Bloomberg Terminal Command Center</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700;800&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #05070c;
            --card-bg: rgba(13, 17, 26, 0.75);
            --card-border: rgba(255, 255, 255, 0.08);
            --card-glow: rgba(59, 130, 246, 0.05);
            --accent: #3b82f6;
            --green: #10b981;
            --green-glow: rgba(16, 185, 129, 0.2);
            --red: #ef4444;
            --red-glow: rgba(239, 68, 68, 0.2);
            --purple: #8b5cf6;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
        }

        * { box-sizing: border-box; }

        body {
            background-color: var(--bg);
            background-image: 
                radial-gradient(at 0% 0%, rgba(59, 130, 246, 0.08) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(139, 92, 246, 0.08) 0px, transparent 50%);
            color: var(--text-primary);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            margin: 0;
            padding: 16px 24px;
            min-height: 100vh;
        }

        /* Glassmorphism Header */
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--card-border);
            border-radius: 14px;
            padding: 14px 24px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }

        .brand-title {
            font-size: 1.35rem;
            font-weight: 800;
            letter-spacing: -0.5px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .badge-terminal {
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            color: white;
            padding: 3px 10px;
            border-radius: 6px;
            font-size: 0.7rem;
            font-weight: 800;
            letter-spacing: 0.8px;
            text-transform: uppercase;
        }

        .status-badge {
            background-color: rgba(16, 185, 129, 0.12);
            color: var(--green);
            border: 1px solid rgba(16, 185, 129, 0.3);
            padding: 5px 12px;
            border-radius: 6px;
            font-size: 0.78rem;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .pulse-dot {
            width: 8px;
            height: 8px;
            background-color: var(--green);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--green);
            animation: pulse 1.8s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(0.95); opacity: 0.8; }
            50% { transform: scale(1.2); opacity: 1; }
            100% { transform: scale(0.95); opacity: 0.8; }
        }

        .kill-btn {
            background: linear-gradient(135deg, #991b1b, #dc2626);
            color: white;
            border: 1px solid rgba(239, 68, 68, 0.5);
            padding: 8px 18px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 0.8rem;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 4px 14px rgba(220, 38, 38, 0.3);
        }
        .kill-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(220, 38, 38, 0.5);
        }

        /* Metric Grid */
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 16px;
            margin-bottom: 20px;
        }

        .glass-card {
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 16px 20px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .glass-card:hover {
            border-color: rgba(255, 255, 255, 0.18);
            transform: translateY(-2px);
        }

        .card-label {
            color: var(--text-muted);
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-bottom: 6px;
        }
        .card-val {
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.65rem;
            font-weight: 800;
            letter-spacing: -0.5px;
        }
        .green { color: var(--green); text-shadow: 0 0 12px var(--green-glow); }
        .red { color: var(--red); text-shadow: 0 0 12px var(--red-glow); }
        .blue { color: var(--accent); }
        .purple { color: var(--purple); }

        /* Multi-Panel Grid */
        .panel-grid-2 {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 16px;
            margin-bottom: 20px;
        }

        /* Bloomberg Terminal Watchlist Heatmap Grid */
        .watchlist-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-top: 12px;
        }
        .watch-tile {
            background: rgba(18, 24, 38, 0.8);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 10px 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .watch-sym { font-weight: 800; font-size: 0.95rem; }
        .watch-status { font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; font-weight: 700; }

        /* Tables */
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        th, td {
            text-align: left;
            padding: 10px 12px;
            border-bottom: 1px solid var(--card-border);
            font-size: 0.85rem;
        }
        th {
            color: var(--text-muted);
            font-weight: 700;
            text-transform: uppercase;
            font-size: 0.7rem;
            letter-spacing: 0.6px;
        }
        td { font-family: 'JetBrains Mono', monospace; }

        /* Terminal Box */
        .terminal-box {
            background-color: #030509;
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 12px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            color: var(--green);
            height: 140px;
            overflow-y: auto;
            line-height: 1.6;
        }
    </style>
</head>
<body>

    <!-- Header -->
    <div class="header">
        <div>
            <div class="brand-title">
                OmniAlpha AI <span class="badge-terminal">PRE-CATALYST TERMINAL</span>
            </div>
            <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 2px;">
                Institutional Bloomberg-Style Swarm Committee • Real-Time Options Engine
            </div>
        </div>
        <div style="display: flex; gap: 14px; align-items: center;">
            <div class="status-badge" id="sys-status">
                <div class="pulse-dot"></div> OPERATIONAL (LIVE)
            </div>
            <button class="kill-btn" onclick="triggerKillSwitch()">EMERGENCY KILL SWITCH</button>
        </div>
    </div>

    <!-- Top Account Cards -->
    <div class="metric-grid">
        <div class="glass-card">
            <div class="card-label">Paper Account Equity</div>
            <div class="card-val green" id="equity">$100,000.00</div>
        </div>
        <div class="glass-card">
            <div class="card-label">Intraday Buying Power</div>
            <div class="card-val blue" id="buying_power">$400,000.00</div>
        </div>
        <div class="glass-card">
            <div class="card-label">Risk Shield Guardrail</div>
            <div class="card-val green">2.0% MAX RISK CAP</div>
        </div>
        <div class="glass-card">
            <div class="card-label">Reflexion Memory Journal</div>
            <div class="card-val purple" id="lesson-count">SELF-LEARNING ACTIVE</div>
        </div>
    </div>

    <!-- Main Chart & Watchlist Grid -->
    <div class="panel-grid-2">
        <div class="glass-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h3 style="margin:0; font-size: 1.05rem;">Real-Time Portfolio Equity Curve ($100k Capital)</h3>
                <span style="font-size: 0.75rem; color: var(--text-muted); font-family: 'JetBrains Mono';">LIVE 3S REFRESH</span>
            </div>
            <canvas id="equityChart" style="max-height: 190px; margin-top: 10px;"></canvas>
        </div>

        <div class="glass-card">
            <h3 style="margin:0; font-size: 1.05rem;">Underlying Market Watchlist</h3>
            <div class="watchlist-grid" id="watchlist-box">
                <div class="watch-tile"><span class="watch-sym">SPY</span><span class="watch-status green">NEUTRAL</span></div>
                <div class="watch-tile"><span class="watch-sym">QQQ</span><span class="watch-status green">NEUTRAL</span></div>
                <div class="watch-tile"><span class="watch-sym">NVDA</span><span class="watch-status green">NEUTRAL</span></div>
                <div class="watch-tile"><span class="watch-sym">AAPL</span><span class="watch-status green">NEUTRAL</span></div>
                <div class="watch-tile"><span class="watch-sym">TSLA</span><span class="watch-status green">NEUTRAL</span></div>
                <div class="watch-tile"><span class="watch-sym">AMD</span><span class="watch-status green">BULLISH</span></div>
            </div>
        </div>
    </div>

    <!-- Signal Feed & Options Spreads Table -->
    <div class="glass-card" style="margin-bottom: 20px;">
        <h3 style="margin:0; font-size: 1.05rem;">Pre-Catalyst Signal Feed & Vertical Spreads</h3>
        <table>
            <thead>
                <tr>
                    <th>Underlying</th>
                    <th>Signal / Rationale</th>
                    <th>Proposed Strategy</th>
                    <th>Confidence</th>
                    <th>Max Risk</th>
                    <th>Max Reward</th>
                </tr>
            </thead>
            <tbody id="signal-table">
                <tr><td colspan="6" style="color: var(--text-muted);">Scanning SEC EDGAR, Social Radar & Option Chains...</td></tr>
            </tbody>
        </table>
    </div>

    <!-- Reflexion Self-Learning Journal Table -->
    <div class="glass-card" style="margin-bottom: 20px;">
        <h3 style="margin:0; font-size: 1.05rem; color: var(--purple);">🧠 Self-Learning Trade Memory & Post-Mortems</h3>
        <table>
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Underlying</th>
                    <th>Strategy</th>
                    <th>Outcome P&L</th>
                    <th>Post-Mortem Lesson Learned</th>
                </tr>
            </thead>
            <tbody id="memory-table">
                <tr><td colspan="5" style="color: var(--text-muted);">Agent is recording live trade outcomes & learning post-mortems...</td></tr>
            </tbody>
        </table>
    </div>

    <!-- Bottom AI Thought Log Terminal -->
    <div class="glass-card">
        <h3 style="margin:0 0 10px 0; font-size: 1.0rem;">AI Committee Thought Audit Terminal</h3>
        <div class="terminal-box" id="terminal-log">
            [SYS_INIT] OmniAlpha Multi-Agent Bloomberg Terminal Swarm Initialized...<br>
            [REFLEXION] Reflexion Self-Learning Memory Engine Loaded...<br>
            [CONNECT] Connected to Alpaca Paper Trading Account (ae811ce4-f4dc-47a9-975f-fa2e6b42c169)...<br>
            [SCAN] Scanning SEC EDGAR Form 4 feeds & Google News Sentiment Velocity...<br>
            [SIGNAL] AMD: Bullish Sentiment Velocity (Score 4:0) -> Formulating Bull Put Spread ($250 Max Risk)...<br>
            [RISK_SHIELD] Risk Approval: PASSED ($250.00 <= $2,000.00 Cap).<br>
        </div>
    </div>

    <script>
        // Setup Chart.js Equity Curve
        const ctx = document.getElementById('equityChart').getContext('2d');
        const equityChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['9:30 AM', '11:00 AM', '1:00 PM', '3:00 PM', '4:00 PM'],
                datasets: [{
                    label: 'Portfolio Equity ($)',
                    data: [100000, 100000, 100000, 100000, 100000],
                    borderColor: '#10b981',
                    borderWidth: 2.5,
                    tension: 0.3,
                    fill: false
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                    y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } }
                }
            }
        });

        async function fetchDashboard() {
            try {
                const res = await fetch('/api/state');
                const data = await res.json();
                
                if (data.account && !data.account.error) {
                    document.getElementById('equity').innerText = '$' + Number(data.account.equity).toLocaleString(undefined, {minimumFractionDigits: 2});
                    document.getElementById('buying_power').innerText = '$' + Number(data.account.buying_power).toLocaleString(undefined, {minimumFractionDigits: 2});
                }
                
                if (data.signals && data.signals.length > 0) {
                    let html = '';
                    let watchHtml = '';
                    
                    data.signals.forEach(s => {
                        const conf = s.confidence ? (s.confidence * 100).toFixed(0) + '%' : '-';
                        const strat = s.strategy_type || 'HOLD';
                        const isBull = strat.includes('BULL');
                        const isBear = strat.includes('BEAR');
                        const colorClass = isBull ? 'green' : (isBear ? 'red' : '');
                        
                        html += `<tr>
                            <td><b>${s.symbol}</b></td>
                            <td>${s.reason}</td>
                            <td><span class="${colorClass}">${strat}</span></td>
                            <td>${conf}</td>
                            <td>$${s.max_loss ? s.max_loss.toFixed(2) : '0.00'}</td>
                            <td>$${s.max_gain ? s.max_gain.toFixed(2) : '0.00'}</td>
                        </tr>`;

                        watchHtml += `<div class="watch-tile">
                            <span class="watch-sym">${s.symbol}</span>
                            <span class="watch-status ${colorClass || 'green'}">${isBull ? 'BULLISH' : (isBear ? 'BEARISH' : 'NEUTRAL')}</span>
                        </div>`;
                    });
                    
                    document.getElementById('signal-table').innerHTML = html;
                    document.getElementById('watchlist-box').innerHTML = watchHtml;
                }

                if (data.memory_journal && data.memory_journal.length > 0) {
                    let memHtml = '';
                    data.memory_journal.forEach(m => {
                        const pnlColor = m.pnl_dollars >= 0 ? 'green' : 'red';
                        memHtml += `<tr>
                            <td>${new Date(m.timestamp).toLocaleTimeString()}</td>
                            <td><b>${m.symbol}</b></td>
                            <td>${m.strategy}</td>
                            <td><span class="${pnlColor}">$${m.pnl_dollars.toFixed(2)}</span></td>
                            <td>${m.lesson_learned}</td>
                        </tr>`;
                    });
                    document.getElementById('memory-table').innerHTML = memHtml;
                    document.getElementById('lesson-count').innerText = data.memory_journal.length + ' LESSONS';
                }
            } catch(e) {}
        }

        async function triggerKillSwitch() {
            if (confirm("Engage Emergency Kill Switch? This will halt trading immediately.")) {
                const res = await fetch('/api/kill_switch', {method: 'POST'});
                const data = await res.json();
                document.getElementById('sys-status').innerText = 'HALTED / KILLED';
                document.getElementById('sys-status').style.borderColor = '#ef4444';
                document.getElementById('sys-status').style.color = '#ef4444';
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
    signals = []
    
    if not SYSTEM_STATE["kill_switch_engaged"]:
        for sym in config.TARGET_SYMBOLS:
            eval_res = committee.evaluate_opportunity(sym, account)
            signals.append(eval_res)
            
    return jsonify({
        "account": account,
        "signals": signals,
        "memory_journal": reflexion_memory.get_all_lessons(),
        "system_state": SYSTEM_STATE
    })

@app.route('/api/kill_switch', methods=['POST'])
def trigger_kill_switch():
    SYSTEM_STATE["kill_switch_engaged"] = True
    SYSTEM_STATE["status"] = "HALTED"
    return jsonify({
        "status": "SUCCESS",
        "message": "Emergency Kill Switch Engaged. Trading System Halted."
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=config.PORT, debug=True)
