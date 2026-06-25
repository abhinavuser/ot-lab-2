#!/usr/bin/env python3
"""
Railroad North - Slave PLC
Local track segment controller
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
from dataclasses import dataclass
from typing import Dict

logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO'),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATA STRUCTURES
# ============================================================================

class DeviceType(Enum):
    TRACK_SWITCH = 1
    SIGNAL = 2
    BARRIER = 3
    OCCUPANCY_SENSOR = 4

class SignalState(Enum):
    RED = 0
    YELLOW = 1
    GREEN = 2

@dataclass
class LocalDevice:
    device_id: int
    device_type: DeviceType
    name: str
    state: object
    last_update: str

# ============================================================================
# SLAVE PLC CLASS
# ============================================================================

class SlavePLC:
    """Slave PLC for track segment control"""
    
    def __init__(self):
        self.slave_id = int(os.environ.get('SLAVE_ID', 1))
        self.segment_name = os.environ.get('SEGMENT_NAME', 'Unknown')
        self.master_ip = os.environ.get('MASTER_IP', '172.25.0.10')
        self.master_port = int(os.environ.get('MASTER_PORT', 502))
        self.listen_port = int(os.environ.get('LISTEN_PORT', 502))
        
        self.config = self._load_config()
        self.devices: Dict[int, LocalDevice] = {}
        self.initialize_devices()
        
        self.last_master_contact = datetime.now().isoformat()
        self.heartbeat_interval = 5
        self.command_log: list = []
        
        logger.info(f"Slave PLC {self.slave_id} ({self.segment_name}) initialized")
    
    def _load_config(self) -> Dict:
        try:
            with open('/app/config/segment.json') as f:
                return json.load(f)
        except Exception:
            logger.warning("Segment config not found, using defaults")
            return {
                'segment_id': self.slave_id,
                'name': self.segment_name,
                'devices': [
                    {'id': 1, 'type': 'TRACK_SWITCH', 'name': f'Switch {self.segment_name}-A'},
                    {'id': 2, 'type': 'TRACK_SWITCH', 'name': f'Switch {self.segment_name}-B'},
                    {'id': 3, 'type': 'SIGNAL', 'name': f'Signal {self.segment_name}'},
                    {'id': 4, 'type': 'BARRIER', 'name': f'Barrier {self.segment_name}'},
                    {'id': 5, 'type': 'OCCUPANCY_SENSOR', 'name': f'Occupancy {self.segment_name}'},
                ]
            }
    
    def initialize_devices(self):
        for dev_config in self.config.get('devices', []):
            dev_id = dev_config['id']
            dev_type = DeviceType[dev_config['type']]
            
            if dev_type == DeviceType.TRACK_SWITCH:
                initial_state = 'INACTIVE'
            elif dev_type == DeviceType.SIGNAL:
                initial_state = 'RED'
            elif dev_type == DeviceType.BARRIER:
                initial_state = 'LOWERED'
            elif dev_type == DeviceType.OCCUPANCY_SENSOR:
                initial_state = False
            else:
                initial_state = None
            
            self.devices[dev_id] = LocalDevice(
                device_id=dev_id,
                device_type=dev_type,
                name=dev_config['name'],
                state=initial_state,
                last_update=datetime.now().isoformat()
            )
    
    def control_track_switch(self, switch_id: int, command: str) -> dict:
        if switch_id not in self.devices:
            return {'success': False, 'error': f'Unknown switch {switch_id}'}
        
        device = self.devices[switch_id]
        if device.device_type != DeviceType.TRACK_SWITCH:
            return {'success': False, 'error': f'Device {switch_id} is not a track switch'}
        
        if command not in ['ACTIVATE', 'DEACTIVATE']:
            return {'success': False, 'error': f'Invalid command: {command}'}
        
        # Safety checks
        if command == 'ACTIVATE':
            occupancy_sensor = next(
                (d for d in self.devices.values() if d.device_type == DeviceType.OCCUPANCY_SENSOR), None
            )
            if occupancy_sensor and occupancy_sensor.state:
                msg = f"Cannot activate switch {switch_id}: track occupied"
                logger.warning(msg)
                self._send_syslog(f"REJECTED: {msg}")
                return {'success': False, 'error': msg}
            
            barrier = next(
                (d for d in self.devices.values() if d.device_type == DeviceType.BARRIER), None
            )
            if barrier and barrier.state != 'LOWERED':
                msg = f"Cannot activate switch {switch_id}: barrier not lowered"
                logger.warning(msg)
                self._send_syslog(f"REJECTED: {msg}")
                return {'success': False, 'error': msg}
        
        device.state = 'ACTIVE' if command == 'ACTIVATE' else 'INACTIVE'
        device.last_update = datetime.now().isoformat()
        
        logger.info(f"Switch {switch_id} ({device.name}) {command}")
        self._send_syslog(f"DEVICE_CONTROL: {device.name} {command}")
        
        self.command_log.append({
            'timestamp': datetime.now().isoformat(),
            'device': device.name,
            'action': command,
            'result': 'SUCCESS'
        })
        
        return {'success': True, 'device': device.name, 'new_state': device.state}
    
    def control_signal(self, signal_state: str) -> dict:
        signal = next(
            (d for d in self.devices.values() if d.device_type == DeviceType.SIGNAL), None
        )
        if not signal:
            return {'success': False, 'error': 'No signal device found'}
        
        if signal_state not in ['RED', 'YELLOW', 'GREEN']:
            return {'success': False, 'error': f'Invalid signal state: {signal_state}'}
        
        signal.state = signal_state
        signal.last_update = datetime.now().isoformat()
        
        logger.info(f"Signal {signal.name} set to {signal_state}")
        self._send_syslog(f"SIGNAL_CHANGE: {signal.name} -> {signal_state}")
        
        return {'success': True, 'device': signal.name, 'new_state': signal_state}
    
    def set_device_state(self, device_name: str, value) -> dict:
        device = next(
            (d for d in self.devices.values() if d.name.lower() == device_name.lower() or
             d.device_type.name.lower() == device_name.lower()), None
        )
        if not device:
            return {'success': False, 'error': f'Device not found: {device_name}'}
        
        device.state = value
        device.last_update = datetime.now().isoformat()
        logger.info(f"Device {device.name} state set to {value}")
        self._send_syslog(f"DEVICE_SET: {device.name} -> {value}")
        
        return {'success': True, 'device': device.name, 'new_state': str(value)}
    
    def get_status(self) -> Dict:
        return {
            'slave_id': self.slave_id,
            'segment_name': self.segment_name,
            'timestamp': datetime.now().isoformat(),
            'devices': {
                dev_id: {
                    'id': dev.device_id,
                    'name': dev.name,
                    'type': dev.device_type.name,
                    'state': str(dev.state),
                    'last_update': dev.last_update
                }
                for dev_id, dev in self.devices.items()
            },
            'recent_commands': self.command_log[-10:]
        }
    
    def _send_syslog(self, message: str):
        timestamp = datetime.now().isoformat()
        log_message = f"{timestamp} [SLAVE-{self.slave_id}] {message}"
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(log_message.encode(), ('172.25.0.40', 514))
            sock.close()
        except Exception as e:
            logger.debug(f"Syslog send failed: {e}")
    
    def heartbeat_loop(self):
        while True:
            try:
                self._send_syslog(f"HEARTBEAT: Slave {self.slave_id} ({self.segment_name}) alive")
                logger.debug(f"Heartbeat: Slave {self.slave_id}")
                time.sleep(self.heartbeat_interval)
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                time.sleep(5)

# ============================================================================
# REST API
# ============================================================================

from flask import Flask, jsonify, request as flask_request

app = Flask(__name__)
slave_plc = SlavePLC()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'role': 'slave',
        'slave_id': slave_plc.slave_id,
        'segment': slave_plc.segment_name,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(slave_plc.get_status())

@app.route('/api/device/switch', methods=['POST'])
def control_switch():
    data = flask_request.json
    switch_id = data.get('switch_id')
    command = data.get('command')
    result = slave_plc.control_track_switch(switch_id, command)
    return jsonify(result)

@app.route('/api/device/signal', methods=['POST'])
def control_signal():
    data = flask_request.json
    state = data.get('state', 'RED')
    result = slave_plc.control_signal(state)
    return jsonify(result)

@app.route('/api/device/set', methods=['POST'])
def set_device():
    data = flask_request.json
    device = data.get('device', '')
    value = data.get('value')
    result = slave_plc.set_device_state(device, value)
    return jsonify(result)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    # Start heartbeat in background
    heartbeat_thread = threading.Thread(
        target=slave_plc.heartbeat_loop,
        daemon=True
    )
    heartbeat_thread.start()
    
    # Start REST API
    logger.info(f"Starting Slave {slave_plc.slave_id} ({slave_plc.segment_name}) API on 0.0.0.0:8080")
    app.run(host='0.0.0.0', port=8080, debug=False)
