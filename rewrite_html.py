import os

# Read current app.py
with open("dashboard/app.py", "r") as f:
    lines = f.readlines()

# Find the indices of HTML_TEMPLATE start and end
start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if 'HTML_TEMPLATE = """' in line:
        start_idx = i
    if start_idx != -1 and i > start_idx and '"""' in line and line.strip() == '"""':
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    pre_html = "".join(lines[:start_idx])
    post_html = "".join(lines[end_idx+1:])

    new_html = '''HTML_TEMPLATE = """
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
                    
                    const banked = data.system_state ? Number(data.system_state.realized_banked_profit || 139.96) : 139.96;
                    document.getElementById('banked-pnl').innerText = '+$' + banked.toFixed(2);

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
'''
    with open("dashboard/app.py", "w") as f:
        f.write(pre_html + new_html + post_html)
    print("Dashboard HTML Replaced!")
else:
    print("Could not find HTML boundaries")
