#!/usr/bin/env python3
"""
Railroad North - Central SCADA Server
Operator interface for railroad control
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import requests as http_requests

logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO'),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


class SCADAServer:
    """Central SCADA server for railroad control"""
    
    def __init__(self):
        self.master_plc_ip = os.environ.get('MASTER_PLC_IP', '172.25.0.10')
        self.master_plc_port = int(os.environ.get('MASTER_PLC_PORT', 502))
        self.segments = {
            1: {'name': 'North (Entrance)', 'ip': '172.25.1.10'},
            2: {'name': 'Central (Junction)', 'ip': '172.25.2.10'},
            3: {'name': 'South (Yard)', 'ip': '172.25.3.10'}
        }
        self.command_history: List[Dict] = []
        logger.info("SCADA Server initialized")
    
    def get_master_status(self) -> Dict:
        try:
            resp = http_requests.get(f'http://{self.master_plc_ip}:8080/api/status', timeout=2)
            return resp.json()
        except Exception as e:
            logger.error(f"Cannot reach Master PLC: {e}")
            return {'error': 'Master PLC unreachable'}
    
    def send_route_command(self, segment_id: int, route: str) -> Dict:
        try:
            command_data = {
                'segment_id': segment_id,
                'route': route,
                'timestamp': datetime.now().isoformat(),
                'operator': 'SCADA'
            }
            resp = http_requests.post(
                f'http://{self.master_plc_ip}:8080/api/command',
                json=command_data, timeout=2
            )
            result = resp.json()
            self.command_history.append({**command_data, 'result': result})
            logger.info(f"Command sent: Segment {segment_id} -> Route {route}")
            return result
        except Exception as e:
            logger.error(f"Command failed: {e}")
            return {'error': str(e), 'success': False}
    
    def get_system_overview(self) -> Dict:
        master_status = self.get_master_status()
        return {
            'timestamp': datetime.now().isoformat(),
            'master_plc': master_status,
            'segments': self.segments,
            'recent_commands': self.command_history[-5:]
        }


app = Flask(__name__)
CORS(app)
scada = SCADAServer()

# ============================================================================
# WEB INTERFACE
# ============================================================================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Railroad North - SCADA Control Center</title>
    <style>
        :root {
            --bg-dark: #0f172a;
            --bg-panel: #1e293b;
            --accent: #38bdf8;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-main);
            padding: 25px;
            min-height: 100vh;
        }
        .header {
            background-color: var(--bg-panel);
            border-top: 4px solid var(--accent);
            padding: 20px 30px;
            margin-bottom: 25px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 { font-size: 24px; font-weight: 600; color: var(--text-main); }
        .header p { color: var(--text-muted); font-size: 14px; margin-top: 4px; }
        .status-bar {
            background-color: var(--bg-panel);
            padding: 15px 25px;
            margin-bottom: 25px;
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 14px;
            font-weight: 500;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        }
        .status-bar .indicator { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 8px; }
        .indicator.online { background: var(--success); box-shadow: 0 0 8px var(--success); }
        .indicator.offline { background: var(--danger); box-shadow: 0 0 8px var(--danger); }
        
        .container { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
        
        .segment {
            background-color: var(--bg-panel);
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            border: 1px solid rgba(255,255,255,0.05);
        }
        .segment h3 { margin-bottom: 20px; color: var(--accent); font-size: 18px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px; }
        .segment-status {
            background: rgba(0,0,0,0.2);
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
            font-size: 14px;
            line-height: 2.0;
            color: var(--text-muted);
        }
        .control-buttons { display: flex; flex-direction: column; gap: 10px; }
        
        button {
            background-color: #2563eb;
            color: #ffffff;
            border: none;
            padding: 10px 15px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            transition: background-color 0.2s;
        }
        button:hover { background-color: #1d4ed8; }
        button:active { transform: translateY(1px); }
        
        button.emergency { background-color: var(--danger); }
        button.emergency:hover { background-color: #dc2626; }
        button.clear { background-color: #475569; }
        button.clear:hover { background-color: #334155; }
        
        .panel-bottom { grid-column: 1 / -1; display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 5px; }
        .panel { background-color: var(--bg-panel); padding: 25px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
        .panel h3 { color: var(--text-main); font-size: 16px; margin-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px; }
        
        .log-panel { max-height: 250px; overflow-y: auto; font-family: monospace; font-size: 13px; }
        .log-entry { margin: 6px 0; padding: 8px 12px; background: rgba(0,0,0,0.2); border-radius: 4px; border-left: 3px solid var(--accent); }
        
        .success { color: var(--success); font-weight: 600;}
        .error { color: var(--danger); font-weight: 600;}
        .warning { color: var(--warning); font-weight: 600;}
        .info { color: var(--accent); font-weight: 600;}
        
        .interlock { padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 14px; color: var(--text-muted); }
        .interlock:last-child { border: none; }
        .active-badge { color: var(--success); font-weight: bold; background: rgba(16,185,129,0.1); padding: 2px 8px; border-radius: 12px; font-size: 12px; }
        
        @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }
        .pulse { animation: pulse 2s infinite; }
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>RAILROAD NORTH</h1>
            <p>Central SCADA Control Center | Master-Slave PLC Architecture</p>
        </div>
        <div style="text-align: right;">
            <button class="emergency" onclick="emergencyStop()">E-STOP / HALT ALL</button>
            <button class="clear" onclick="clearEmergency()">CLEAR FAULTS</button>
        </div>
    </div>
    
    <div class="status-bar">
        <span><span class="indicator" id="master-indicator"></span>Master PLC: <span id="master-status">Connecting...</span></span>
        <span>System Time: <span id="system-time">--:--:--</span></span>
        <span>Commands Issued: <span id="command-count">0</span></span>
    </div>
    
    <div class="container">
        <div class="segment" id="segment-1">
            <h3>Segment 1: North (Entrance)</h3>
            <div class="segment-status"><div id="seg1-status">Loading...</div></div>
            <div class="control-buttons">
                <button onclick="sendCommand(1, 'ROUTE_A')">Route A (Express)</button>
                <button onclick="sendCommand(1, 'ROUTE_B')">Route B (Local)</button>
                <button onclick="sendCommand(1, 'ROUTE_C')">Route C (Maintenance)</button>
            </div>
        </div>
        
        <div class="segment" id="segment-2">
            <h3>Segment 2: Central (Junction)</h3>
            <div class="segment-status"><div id="seg2-status">Loading...</div></div>
            <div class="control-buttons">
                <button onclick="sendCommand(2, 'ROUTE_A')">Route A (Express)</button>
                <button onclick="sendCommand(2, 'ROUTE_B')">Route B (Local)</button>
                <button onclick="sendCommand(2, 'ROUTE_C')">Route C (Maintenance)</button>
            </div>
        </div>
        
        <div class="segment" id="segment-3">
            <h3>Segment 3: South (Yard)</h3>
            <div class="segment-status"><div id="seg3-status">Loading...</div></div>
            <div class="control-buttons">
                <button onclick="sendCommand(3, 'ROUTE_A')">Route A (Express)</button>
                <button onclick="sendCommand(3, 'ROUTE_B')">Route B (Local)</button>
                <button onclick="sendCommand(3, 'ROUTE_C')">Route C (Maintenance)</button>
            </div>
        </div>
        
        <div class="panel-bottom">
            <div class="panel">
                <h3>Safety Interlocks</h3>
                <div id="safety-content" style="color: var(--text-muted); font-size: 14px;">Loading...</div>
            </div>
            
            <div class="panel log-panel">
                <h3>Command Audit Log</h3>
                <div id="log-content"></div>
            </div>
        </div>
    </div>
    
    <script>
        let allLogs = [];
        
        async function updateStatus() {
            try {
                const resp = await fetch('/api/overview');
                const data = await resp.json();
                
                const ind = document.getElementById('master-indicator');
                const ms = document.getElementById('master-status');
                if (data.master_plc.error) {
                    ind.className = 'indicator offline';
                    ms.innerHTML = '<span class="error">OFFLINE</span>';
                } else {
                    ind.className = 'indicator online';
                    ms.innerHTML = '<span class="success">ONLINE</span>';
                }
                
                if (data.master_plc.segments) {
                    data.master_plc.segments.forEach(seg => {
                        const el = document.getElementById('seg' + seg.segment_id + '-status');
                        if (!el) return;
                        const stateClass = seg.state === 'EMERGENCY_STOP' ? 'error' : seg.state === 'FAULT' ? 'warning' : 'info';
                        const occClass = seg.sensor_occupied ? 'error' : 'success';
                        el.innerHTML =
                            'State: <span class="' + stateClass + '">' + seg.state + '</span><br>' +
                            'Route: <span class="warning">' + (seg.current_route || 'NONE') + '</span><br>' +
                            'Signal: <span class="info">' + seg.signal_state + '</span><br>' +
                            'Barrier: <span class="success">' + (seg.barrier_engaged ? 'ENGAGED' : 'RAISED') + '</span><br>' +
                            'Occupied: <span class="' + occClass + '">' + (seg.sensor_occupied ? 'YES' : 'NO') + '</span>';
                    });
                }
                
                if (data.master_plc.safety_interlocks) {
                    const sc = document.getElementById('safety-content');
                    sc.innerHTML = data.master_plc.safety_interlocks.map(si =>
                        '<div class="interlock">[Rule ' + si.rule_id + '] ' + si.description +
                        ' - <span class="active-badge">' + (si.active ? 'ACTIVE' : 'INACTIVE') + '</span></div>'
                    ).join('');
                }
                
                document.getElementById('command-count').textContent = data.master_plc.total_commands || 0;
                
                if (data.recent_commands && data.recent_commands.length > 0) {
                    const logDiv = document.getElementById('log-content');
                    const cmds = data.recent_commands.slice().reverse();
                    logDiv.innerHTML = cmds.map(cmd => {
                        const ok = cmd.result && cmd.result.success;
                        return '<div class="log-entry ' + (ok ? 'success' : 'error') + '">' +
                            '[' + (cmd.timestamp || '').substring(11, 19) + '] Seg ' + cmd.segment_id +
                            ': ' + cmd.route + ' - ' + (ok ? 'SUCCESS' : 'REJECTED') + '</div>';
                    }).join('');
                }
            } catch (e) {
                document.getElementById('master-indicator').className = 'indicator offline';
                document.getElementById('master-status').innerHTML = '<span class="error pulse">CONNECTING...</span>';
            }
        }
        
        async function sendCommand(segId, route) {
            try {
                const resp = await fetch('/api/command', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ segment_id: segId, route: route })
                });
                await resp.json();
                updateStatus();
            } catch (e) { alert('Command failed: ' + e); }
        }
        
        async function emergencyStop() {
            if (!confirm('TRIGGER EMERGENCY STOP?')) return;
            await fetch('/api/emergency', { method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ reason: 'Manual SCADA E-Stop' })
            });
            updateStatus();
        }
        
        async function clearEmergency() {
            await fetch('/api/emergency/clear', { method: 'POST' });
            updateStatus();
        }
        
        setInterval(() => {
            document.getElementById('system-time').textContent = new Date().toLocaleTimeString();
        }, 1000);
        
        updateStatus();
        setInterval(updateStatus, 2000);
    </script>
</body>
</html>
'''

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'role': 'scada'})

@app.route('/api/status', methods=['GET'])
def api_status():
    return jsonify(scada.get_system_overview())

@app.route('/api/overview', methods=['GET'])
def api_overview():
    return jsonify(scada.get_system_overview())

@app.route('/api/command', methods=['POST'])
def api_command():
    data = request.json
    segment_id = data.get('segment_id')
    route = data.get('route')
    result = scada.send_route_command(segment_id, route)
    return jsonify(result)

@app.route('/api/segments', methods=['GET'])
def api_segments():
    return jsonify(scada.segments)

@app.route('/api/emergency', methods=['POST'])
def api_emergency():
    data = request.json or {}
    reason = data.get('reason', 'SCADA emergency')
    try:
        resp = http_requests.post(
            f'http://{scada.master_plc_ip}:8080/api/emergency',
            json={'reason': reason}, timeout=2
        )
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/emergency/clear', methods=['POST'])
def api_emergency_clear():
    try:
        resp = http_requests.post(
            f'http://{scada.master_plc_ip}:8080/api/emergency/clear', timeout=2
        )
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    logger.info("Starting SCADA Server on 0.0.0.0:8080")
    app.run(host='0.0.0.0', port=8080, debug=False)
