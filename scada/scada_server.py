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
            --bg-dark: #000000;
            --bg-panel: #0a0a0a;
            --border: #222222;
            --border-hover: #555555;
            --text-main: #e5e5e5;
            --text-muted: #888888;
            --success: #22c55e;
            --danger: #ef4444;
            --warning: #eab308;
            --accent: #ffffff;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-main);
            padding: 40px;
            min-height: 100vh;
            line-height: 1.5;
        }
        
        .header {
            margin-bottom: 40px;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border);
        }
        .header h1 { font-size: 24px; font-weight: 400; letter-spacing: 1px; }
        .header p { color: var(--text-muted); font-size: 13px; margin-top: 5px; text-transform: uppercase; letter-spacing: 1px; }
        
        .status-bar {
            display: flex;
            gap: 40px;
            margin-bottom: 40px;
            font-size: 13px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .status-bar span span { color: var(--text-main); margin-left: 5px; }
        .indicator { display: inline-block; width: 6px; height: 6px; border-radius: 50%; margin-right: 6px; vertical-align: middle; }
        .indicator.online { background: var(--success); }
        .indicator.offline { background: var(--danger); }
        
        .container { display: grid; grid-template-columns: repeat(3, 1fr); gap: 30px; }
        
        .segment {
            background-color: var(--bg-dark);
            padding: 30px;
            border: 1px solid var(--border);
        }
        .segment h3 { margin-bottom: 25px; font-size: 14px; font-weight: 500; text-transform: uppercase; letter-spacing: 1px; color: var(--text-muted); }
        
        .segment-status {
            margin-bottom: 30px;
            font-size: 13px;
            font-family: 'JetBrains Mono', 'Courier New', monospace;
        }
        .segment-status div { line-height: 2.2; }
        
        .control-buttons { display: flex; flex-direction: column; gap: 8px; }
        
        button {
            background-color: transparent;
            color: var(--text-muted);
            border: 1px solid var(--border);
            padding: 12px 15px;
            cursor: pointer;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: all 0.2s ease;
            text-align: left;
        }
        button:hover { 
            border-color: var(--text-main); 
            color: var(--text-main);
            padding-left: 20px;
        }
        button.active-route {
            border-color: var(--warning);
            color: var(--warning);
            padding-left: 20px;
            background-color: rgba(234, 179, 8, 0.05);
        }
        
        .header-actions { display: flex; gap: 10px; }
        button.emergency { color: #ff6b6b; border-color: #4a1d1d; }
        button.emergency:hover { background-color: #ff6b6b; color: #000; border-color: #ff6b6b; padding-left: 15px; }
        button.clear { border-color: var(--border); }
        button.clear:hover { background-color: var(--text-main); color: var(--bg-dark); padding-left: 15px; }
        
        .panel-bottom { grid-column: 1 / -1; display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-top: 10px; }
        .panel { padding: 30px; border: 1px solid var(--border); }
        .panel h3 { font-size: 14px; font-weight: 500; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 25px; color: var(--text-muted); }
        
        .log-panel { max-height: 250px; overflow-y: auto; }
        .log-entry { margin: 8px 0; font-family: 'JetBrains Mono', 'Courier New', monospace; font-size: 12px; color: var(--text-muted); }
        
        .success { color: var(--success); }
        .error { color: var(--danger); }
        .warning { color: var(--warning); }
        .info { color: var(--text-main); }
        
        .interlock { padding: 12px 0; border-bottom: 1px solid var(--border); font-size: 13px; color: var(--text-main); }
        .interlock:last-child { border: none; }
        .active-badge { float: right; color: var(--success); font-family: 'JetBrains Mono', monospace; font-size: 11px; }
        
        @keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0; } }
        .pulse { animation: blink 1s infinite; }
        
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: var(--bg-dark); }
        ::-webkit-scrollbar-thumb { background: var(--border); }
        ::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>RAILROAD NORTH</h1>
            <p>Master-Slave PLC Architecture &mdash; System Control</p>
        </div>
        <div class="header-actions">
            <button class="emergency" onclick="emergencyStop()">E-Stop</button>
            <button class="clear" onclick="clearEmergency()">Clear Faults</button>
        </div>
    </div>
    
    <div class="status-bar">
        <div>Status <span id="master-status">Connecting...</span></div>
        <div>System Time <span id="system-time">--:--:--</span></div>
        <div>Commands Issued <span id="command-count">0</span></div>
    </div>
    
    <div class="container">
        <div class="segment" id="segment-1">
            <h3>01 &mdash; North Entrance</h3>
            <div class="segment-status"><div id="seg1-status">Loading...</div></div>
            <div class="control-buttons">
                <button onclick="sendCommand(1, 'ROUTE_A')">Route A (Express)</button>
                <button onclick="sendCommand(1, 'ROUTE_B')">Route B (Local)</button>
                <button onclick="sendCommand(1, 'ROUTE_C')">Route C (Maintenance)</button>
            </div>
        </div>
        
        <div class="segment" id="segment-2">
            <h3>02 &mdash; Central Junction</h3>
            <div class="segment-status"><div id="seg2-status">Loading...</div></div>
            <div class="control-buttons">
                <button onclick="sendCommand(2, 'ROUTE_A')">Route A (Express)</button>
                <button onclick="sendCommand(2, 'ROUTE_B')">Route B (Local)</button>
                <button onclick="sendCommand(2, 'ROUTE_C')">Route C (Maintenance)</button>
            </div>
        </div>
        
        <div class="segment" id="segment-3">
            <h3>03 &mdash; South Yard</h3>
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
                <div id="safety-content" style="color: var(--text-muted); font-size: 13px;">Loading...</div>
            </div>
            
            <div class="panel log-panel">
                <h3>System Audit Log</h3>
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
                
                const ms = document.getElementById('master-status');
                if (data.master_plc.error) {
                    ms.innerHTML = '<span class="error">OFFLINE</span>';
                } else {
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
                            
                        const segmentDiv = document.getElementById('segment-' + seg.segment_id);
                        if (segmentDiv) {
                            const buttons = segmentDiv.querySelectorAll('button');
                            buttons.forEach(btn => {
                                if (seg.current_route && btn.getAttribute('onclick').includes(seg.current_route)) {
                                    btn.classList.add('active-route');
                                } else {
                                    btn.classList.remove('active-route');
                                }
                            });
                        }
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
                
                const scadaCmds = data.recent_commands || [];
                const allCmds = data.master_plc.recent_commands || [];
                if (allCmds.length > 0) {
                    const logDiv = document.getElementById('log-content');
                    const cmds = allCmds.slice().reverse();
                    logDiv.innerHTML = cmds.map(cmd => {
                        const ok = cmd.valid;
                        const route = cmd.requested_route || cmd.route;
                        
                        // Correlate: Is this command in the SCADA dashboard's local history?
                        const isScada = scadaCmds.some(sc => 
                            sc.segment_id === cmd.segment_id && 
                            sc.route === route && 
                            Math.abs(new Date(sc.timestamp) - new Date(cmd.timestamp)) < 5000
                        );
                        
                        let statusText = 'REJECTED: ' + (cmd.reason || 'Safety Interlock');
                        let cssClass = 'error';
                        
                        if (ok) {
                            if (isScada) {
                                statusText = 'COMMAND ACCEPTED';
                                cssClass = 'success';
                            } else {
                                statusText = 'UNAUTHORIZED API CALL';
                                cssClass = 'warning';
                            }
                        }
                        
                        return '<div class="log-entry ' + cssClass + '">' +
                            '[' + (cmd.timestamp || '').substring(11, 19) + '] Seg ' + cmd.segment_id +
                            ': ' + route + ' - ' + statusText + '</div>';
                    }).join('');
                }
            } catch (e) {
                const ms = document.getElementById('master-status');
                if (ms) ms.innerHTML = '<span class="error pulse">CONNECTING...</span>';
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
            const el = document.getElementById('system-time');
            if (el) el.textContent = new Date().toLocaleTimeString();
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
