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
    <title>OmniAlpha AI — Options Command Center</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg: #090d16;
            --card: #121826;
            --border: #1f293d;
            --accent: #3b82f6;
            --green: #10b981;
            --red: #ef4444;
            --purple: #8b5cf6;
            --text: #f9fafb;
            --subtext: #9ca3af;
        }
        body {
            background-color: var(--bg);
            color: var(--text);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 24px;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            padding-bottom: 16px;
            margin-bottom: 24px;
        }
        .badge {
            background: linear-gradient(135deg, #2563eb, #7c3aed);
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 700;
        }
        .status-badge {
            background-color: rgba(16, 185, 129, 0.15);
            color: var(--green);
            border: 1px solid var(--green);
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }
        .card {
            background-color: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
        }
        .card-label {
            color: var(--subtext);
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }
        .card-value {
            font-size: 1.7rem;
            font-weight: 700;
        }
        .green { color: var(--green); }
        .purple { color: var(--purple); }
        .red { color: var(--red); }
        .kill-btn {
            background-color: #991b1b;
            color: white;
            border: 1px solid #dc2626;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .kill-btn:hover { background-color: #dc2626; box-shadow: 0 0 12px rgba(220, 38, 38, 0.4); }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
        }
        th, td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid var(--border);
            font-size: 0.88rem;
        }
        th { color: var(--subtext); font-weight: 600; text-transform: uppercase; font-size: 0.75rem; }
        .terminal-box {
            background-color: #050811;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 14px;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 0.82rem;
            color: #10b981;
            height: 140px;
            overflow-y: auto;
            line-height: 1.6;
        }
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1 style="margin: 0; font-size: 1.4rem;">OmniAlpha AI <span class="badge">PRE-CATALYST AGENT</span></h1>
            <p style="margin: 4px 0 0 0; color: var(--subtext); font-size: 0.85rem;">Alpaca Options Swarm • Self-Learning Command Center</p>
        </div>
        <div style="display: flex; gap: 12px; align-items: center;">
            <span class="status-badge" id="sys-status">OPERATIONAL</span>
            <button class="kill-btn" onclick="triggerKillSwitch()">EMERGENCY KILL SWITCH</button>
        </div>
    </div>

    <!-- Metric Cards -->
    <div class="grid">
        <div class="card">
            <div class="card-label">Paper Account Equity</div>
            <div class="card-value green" id="equity">$100,000.00</div>
        </div>
        <div class="card">
            <div class="card-label">Intraday Buying Power</div>
            <div class="card-value" id="buying_power">$400,000.00</div>
        </div>
        <div class="card">
            <div class="card-label">Risk Shield Guardrail</div>
            <div class="card-value green">ACTIVE (2.0% CAP)</div>
        </div>
        <div class="card">
            <div class="card-label">Reflexion Memory Engine</div>
            <div class="card-value purple" id="lesson-count">LEARNING ACTIVE</div>
        </div>
    </div>

    <!-- Main Signal & Chart Grid -->
    <div class="grid" style="grid-template-columns: 2fr 1fr;">
        <div class="card">
            <h3 style="margin-top:0; font-size: 1.1rem;">Pre-Catalyst Signal Feed</h3>
            <table>
                <thead>
                    <tr>
                        <th>Underlying</th>
                        <th>Signal / Rationale</th>
                        <th>Proposed Strategy</th>
                        <th>Confidence</th>
                    </tr>
                </thead>
                <tbody id="signal-table">
                    <tr><td colspan="4" style="color: var(--subtext);">Scanning SEC EDGAR, Social Radar & Option Chains...</td></tr>
                </tbody>
            </table>
        </div>
        
        <div class="card">
            <h3 style="margin-top:0; font-size: 1.1rem;">Equity Performance Chart</h3>
            <canvas id="equityChart" style="max-height: 180px;"></canvas>
        </div>
    </div>

    <!-- Reflexion Self-Learning Journal Table -->
    <div class="card" style="margin-bottom: 24px;">
        <h3 style="margin-top:0; font-size: 1.0rem; color: var(--purple);">🧠 Self-Learning Trade Memory & Post-Mortems</h3>
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
                <tr><td colspan="5" style="color: var(--subtext);">Agent is recording live trade outcomes & learning post-mortems...</td></tr>
            </tbody>
        </table>
    </div>

    <!-- Bottom AI Thought Log Terminal -->
    <div class="card">
        <h3 style="margin-top:0; font-size: 1.0rem;">AI Committee Thought Audit Log</h3>
        <div class="terminal-box" id="terminal-log">
            [SYS_INIT] OmniAlpha Multi-Agent Swarm Initialized...<br>
            [REFLEXION] Reflexion Self-Learning Memory Engine Loaded...<br>
            [CONNECT] Connected to Alpaca Paper Trading Account (ae811ce4-f4dc-47a9-975f-fa2e6b42c169)...<br>
            [SCAN] Scanning SEC EDGAR Form 4 feeds & Google News Sentiment Velocity...<br>
            [SIGNAL] AMD: Bullish Sentiment Velocity (Score 4:0) -> Formulating Bull Put Spread ($250 Max Risk)...<br>
            [RISK_SHIELD] Risk Approval: PASSED ($250.00 <= $2,000.00 Cap).<br>
        </div>
    </div>

    <script>
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
                    x: { grid: { color: '#1f293d' }, ticks: { color: '#9ca3af' } },
                    y: { grid: { color: '#1f293d' }, ticks: { color: '#9ca3af' } }
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
                    data.signals.forEach(s => {
                        const conf = s.confidence ? (s.confidence * 100).toFixed(0) + '%' : '-';
                        const strat = s.strategy_type || 'HOLD';
                        html += `<tr>
                            <td><b>${s.symbol}</b></td>
                            <td>${s.reason}</td>
                            <td><span style="color: ${strat !== 'NONE' ? '#10b981' : '#9ca3af'}">${strat}</span></td>
                            <td>${conf}</td>
                        </tr>`;
                    });
                    document.getElementById('signal-table').innerHTML = html;
                }

                if (data.memory_journal && data.memory_journal.length > 0) {
                    let memHtml = '';
                    data.memory_journal.forEach(m => {
                        const pnlColor = m.pnl_dollars >= 0 ? '#10b981' : '#ef4444';
                        memHtml += `<tr>
                            <td>${new Date(m.timestamp).toLocaleTimeString()}</td>
                            <td><b>${m.symbol}</b></td>
                            <td>${m.strategy}</td>
                            <td><span style="color: ${pnlColor}">$${m.pnl_dollars.toFixed(2)}</span></td>
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
