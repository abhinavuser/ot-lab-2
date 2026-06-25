#!/usr/bin/env python3
"""
Railroad North - Master PLC
Coordinates track segments and enforces safety interlocks
"""

import asyncio
import json
import logging
import os
import socket
import threading
import time
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict, field

# Configure logging
logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO'),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATA STRUCTURES
# ============================================================================

class TrackState(Enum):
    IDLE = 0
    SWITCHING = 1
    OCCUPIED = 2
    FAULT = 3
    EMERGENCY_STOP = 4

class RouteType(Enum):
    ROUTE_A = 1  # Express mainline
    ROUTE_B = 2  # Local siding
    ROUTE_C = 3  # Maintenance track

@dataclass
class SegmentStatus:
    segment_id: int
    name: str
    state: TrackState
    current_route: Optional[RouteType]
    last_switch_time: str
    sensor_occupied: bool
    barrier_engaged: bool
    signal_state: str
    fault_code: int

@dataclass
class SafetyInterlock:
    rule_id: int
    description: str
    condition: str
    action: str
    active: bool

# ============================================================================
# MASTER PLC CLASS
# ============================================================================

class MasterPLC:
    """
    Railroad North Master PLC Controller
    Manages distributed track segments with safety interlocks
    """
    
    def __init__(self):
        self.listen_ip = os.environ.get('LISTEN_IP', '0.0.0.0')
        self.listen_port = int(os.environ.get('LISTEN_PORT', 502))
        self.slave_configs = self._load_slave_configs()
        
        # Segment status tracking
        self.segments: Dict[int, SegmentStatus] = {}
        self.initialize_segments()
        
        # Safety interlocks
        self.safety_interlocks = self._load_safety_interlocks()
        
        # Communication history
        self.command_history: List[Dict] = []
        self.max_history = 1000
        
        # Slave health tracking
        self.slave_health: Dict[int, dict] = {}
        for slave in self.slave_configs['slaves']:
            self.slave_health[slave['id']] = {
                'last_heartbeat': datetime.now().isoformat(),
                'status': 'ONLINE',
                'missed_heartbeats': 0
            }
        
        logger.info("Master PLC initialized")
    
    def _load_slave_configs(self) -> Dict:
        config_path = os.environ.get('SLAVE_CONFIGS', '/app/slave_config.json')
        try:
            with open(config_path) as f:
                return json.load(f)
        except Exception:
            logger.warning("Slave config not found, using defaults")
            return {
                'slaves': [
                    {'id': 1, 'name': 'North (Entrance)', 'ip': '172.25.1.10', 'port': 502, 'heartbeat_interval': 5},
                    {'id': 2, 'name': 'Central (Junction)', 'ip': '172.25.2.10', 'port': 502, 'heartbeat_interval': 5},
                    {'id': 3, 'name': 'South (Yard)', 'ip': '172.25.3.10', 'port': 502, 'heartbeat_interval': 5}
                ]
            }
    
    def initialize_segments(self):
        for slave in self.slave_configs['slaves']:
            segment_id = slave['id']
            self.segments[segment_id] = SegmentStatus(
                segment_id=segment_id,
                name=slave['name'],
                state=TrackState.IDLE,
                current_route=None,
                last_switch_time=datetime.now().isoformat(),
                sensor_occupied=False,
                barrier_engaged=True,  # Start with barriers engaged (safe)
                signal_state='RED',
                fault_code=0
            )
    
    def _load_safety_interlocks(self) -> List[SafetyInterlock]:
        return [
            SafetyInterlock(
                rule_id=1,
                description="No conflicting routes at junction",
                condition="segment_2_route == A AND segment_1_route == A",
                action="REJECT_COMMAND",
                active=True
            ),
            SafetyInterlock(
                rule_id=2,
                description="Barrier must be lowered before routing",
                condition="barrier_not_engaged",
                action="REJECT_COMMAND",
                active=True
            ),
            SafetyInterlock(
                rule_id=3,
                description="No track switching when occupied",
                condition="track_occupied AND switch_command",
                action="ACTIVATE_EMERGENCY_STOP",
                active=True
            ),
            SafetyInterlock(
                rule_id=4,
                description="Heartbeat failure triggers E-stop",
                condition="slave_heartbeat_timeout > 5s",
                action="ACTIVATE_EMERGENCY_STOP",
                active=True
            ),
        ]
    
    def validate_route_command(self, segment_id: int, route: RouteType) -> tuple:
        if segment_id not in self.segments:
            return False, f"Invalid segment ID: {segment_id}"
        
        segment = self.segments[segment_id]
        
        if segment.state == TrackState.FAULT:
            return False, f"Segment {segment.name} is in FAULT state"
        
        if segment.state == TrackState.EMERGENCY_STOP:
            return False, f"Segment {segment.name} is under EMERGENCY STOP"
        
        if not segment.barrier_engaged:
            return False, f"Barrier not engaged for segment {segment.name}"
        
        if segment.sensor_occupied and segment.state == TrackState.SWITCHING:
            return False, f"Cannot switch: track {segment.name} is occupied"
        
        # Check for route conflicts at junction
        if segment_id == 2:
            if route == RouteType.ROUTE_A and self.segments[1].current_route == RouteType.ROUTE_A:
                return False, "Conflicting routes at junction"
        
        # Send audit log
        self._send_syslog(f"VALIDATED: Segment {segment_id} route {route.name}")
        
        return True, "Valid"
    
    def execute_route_command(self, segment_id: int, route: RouteType) -> bool:
        is_valid, reason = self.validate_route_command(segment_id, route)
        
        command_log = {
            'timestamp': datetime.now().isoformat(),
            'segment_id': segment_id,
            'requested_route': route.name,
            'valid': is_valid,
            'reason': reason
        }
        
        if not is_valid:
            logger.warning(f"REJECTED: Segment {segment_id} route {route.name} - {reason}")
            self._send_syslog(f"REJECTED: Segment {segment_id} route {route.name} - {reason}")
            command_log['executed'] = False
            self.command_history.append(command_log)
            return False
        
        segment = self.segments[segment_id]
        segment.state = TrackState.SWITCHING
        segment.current_route = route
        segment.last_switch_time = datetime.now().isoformat()
        
        # Simulate switch delay then go back to IDLE
        segment.state = TrackState.IDLE
        segment.signal_state = 'GREEN'
        
        logger.info(f"APPROVED: Segment {segment.name} route changed to {route.name}")
        self._send_syslog(f"APPROVED: Segment {segment.name} route changed to {route.name}")
        
        command_log['executed'] = True
        self.command_history.append(command_log)
        
        if len(self.command_history) > self.max_history:
            self.command_history.pop(0)
        
        return True
    
    def emergency_stop(self, reason: str):
        logger.critical(f"EMERGENCY STOP: {reason}")
        self._send_syslog(f"EMERGENCY_STOP: {reason}")
        for seg in self.segments.values():
            seg.state = TrackState.EMERGENCY_STOP
            seg.signal_state = 'RED'
    
    def clear_emergency(self):
        logger.info("Emergency cleared - resetting segments to IDLE")
        self._send_syslog("EMERGENCY_CLEARED: All segments reset")
        for seg in self.segments.values():
            if seg.state == TrackState.EMERGENCY_STOP:
                seg.state = TrackState.IDLE
                seg.signal_state = 'RED'
    
    def get_system_status(self) -> Dict:
        segments_data = []
        for seg in self.segments.values():
            segments_data.append({
                'segment_id': seg.segment_id,
                'name': seg.name,
                'state': seg.state.name,
                'current_route': seg.current_route.name if seg.current_route else None,
                'last_switch_time': seg.last_switch_time,
                'sensor_occupied': seg.sensor_occupied,
                'barrier_engaged': seg.barrier_engaged,
                'signal_state': seg.signal_state,
                'fault_code': seg.fault_code
            })
        
        return {
            'timestamp': datetime.now().isoformat(),
            'status': 'operational',
            'segments': segments_data,
            'safety_interlocks': [
                {
                    'rule_id': si.rule_id,
                    'description': si.description,
                    'active': si.active
                }
                for si in self.safety_interlocks
            ],
            'slave_health': self.slave_health,
            'total_commands': len(self.command_history),
            'recent_commands': self.command_history[-10:]
        }
    
    def _send_syslog(self, message: str):
        timestamp = datetime.now().isoformat()
        log_message = f"{timestamp} [MASTER] {message}"
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(log_message.encode(), ('172.25.0.40', 514))
            sock.close()
        except Exception as e:
            logger.debug(f"Syslog send failed (collector may not be up): {e}")
    
    def monitor_slaves_sync(self):
        while True:
            try:
                for slave in self.slave_configs['slaves']:
                    slave_id = slave['id']
                    try:
                        import urllib.request
                        resp = urllib.request.urlopen(
                            f"http://{slave['ip']}:8080/health", timeout=2
                        )
                        if resp.status == 200:
                            self.slave_health[slave_id]['last_heartbeat'] = datetime.now().isoformat()
                            self.slave_health[slave_id]['status'] = 'ONLINE'
                            self.slave_health[slave_id]['missed_heartbeats'] = 0
                    except Exception:
                        self.slave_health[slave_id]['missed_heartbeats'] += 1
                        if self.slave_health[slave_id]['missed_heartbeats'] > 3:
                            self.slave_health[slave_id]['status'] = 'OFFLINE'
                            logger.warning(f"Slave {slave_id} ({slave['name']}) OFFLINE - missed heartbeats")
                            self._send_syslog(f"HEARTBEAT_FAILURE: Slave {slave_id} ({slave['name']})")
                            if self.segments[slave_id].state != TrackState.EMERGENCY_STOP:
                                self.segments[slave_id].state = TrackState.FAULT
                                self.segments[slave_id].signal_state = 'RED'
                
                time.sleep(slave.get('heartbeat_interval', 5))
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(5)

# ============================================================================
# REST API
# ============================================================================

from flask import Flask, jsonify, request as flask_request

app = Flask(__name__)
master_plc = MasterPLC()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'role': 'master', 'timestamp': datetime.now().isoformat()})

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(master_plc.get_system_status())

@app.route('/api/command', methods=['POST'])
def send_command():
    data = flask_request.json
    segment_id = data.get('segment_id')
    route_name = data.get('route', 'ROUTE_A')
    
    try:
        route = RouteType[route_name]
    except KeyError:
        return jsonify({'success': False, 'error': f'Invalid route: {route_name}'}), 400
    
    result = master_plc.execute_route_command(segment_id, route)
    return jsonify({'success': result, 'segment_id': segment_id, 'requested_route': route_name})

@app.route('/api/segments', methods=['GET'])
def get_segments():
    segments = {}
    for seg_id, seg in master_plc.segments.items():
        segments[seg_id] = {
            'segment_id': seg.segment_id,
            'name': seg.name,
            'state': seg.state.name,
            'current_route': seg.current_route.name if seg.current_route else None,
            'sensor_occupied': seg.sensor_occupied,
            'barrier_engaged': seg.barrier_engaged,
            'signal_state': seg.signal_state
        }
    return jsonify(segments)

@app.route('/api/emergency', methods=['POST'])
def trigger_emergency():
    data = flask_request.json or {}
    reason = data.get('reason', 'Manual emergency stop')
    master_plc.emergency_stop(reason)
    return jsonify({'success': True, 'action': 'emergency_stop', 'reason': reason})

@app.route('/api/emergency/clear', methods=['POST'])
def clear_emergency():
    master_plc.clear_emergency()
    return jsonify({'success': True, 'action': 'emergency_cleared'})

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    # Start slave monitor in background
    monitor_thread = threading.Thread(
        target=master_plc.monitor_slaves_sync,
        daemon=True
    )
    monitor_thread.start()
    
    # Start REST API
    logger.info("Starting Master PLC API on 0.0.0.0:8080")
    app.run(host='0.0.0.0', port=8080, debug=False)
