# Railroad North Lab - Complete Implementation Guide
## Master-Slave Distributed PLC Architecture for Freight Control

**Lab Type:** Distributed Railway Control System  
**Architecture:** Master-Slave PLC Topology  
**Protocols:** Modbus TCP, Syslog  
**Complexity:** Advanced  
**Deployment Time:** 30-45 minutes  

---

## 📋 Table of Contents
1. [System Architecture](#system-architecture)
2. [Component Overview](#component-overview)
3. [Docker Infrastructure](#docker-infrastructure)
4. [PLC Implementation](#plc-implementation)
5. [SCADA Simulation](#scada-simulation)
6. [Network Configuration](#network-configuration)
7. [Monitoring & Logging](#monitoring--logging)
8. [Training Scenarios](#training-scenarios)

---

## System Architecture

### Railroad North Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                     Railroad Network Control System               │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CONTROL CENTER (DMZ Layer)                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ EWS (Engineering Workstation)                           │   │
│  │ SCADA Server (Central Control)                          │   │
│  │ Master PLC Controller                                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          │                                       │
│                    ┌─────┴─────┐                                │
│                    │  Modbus   │                                │
│                    │   Router  │                                │
│                    └─────┬─────┘                                │
│                          │                                       │
│        ┌─────────────────┼─────────────────┐                   │
│        │                 │                 │                   │
│        ▼                 ▼                 ▼                   │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐             │
│  │ SEGMENT 1│      │ SEGMENT 2│      │ SEGMENT 3│             │
│  │Slave PLC │      │Slave PLC │      │Slave PLC │             │
│  ├──────────┤      ├──────────┤      ├──────────┤             │
│  │Track SW. │      │Track SW. │      │Track SW. │             │
│  │Signals   │      │Signals   │      │Signals   │             │
│  │Barriers  │      │Barriers  │      │Barriers  │             │
│  └──────────┘      └──────────┘      └──────────┘             │
│                                                                  │
│  MONITORING LAYER (OT Network)                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ IDS (Zeek/Suricata) - Network Monitoring               │   │
│  │ Collector - Log Aggregation                            │   │
│  │ ELK Stack - Centralized Logging & Analysis             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  DMZ TRANSFER LAYER                                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ DMZ Router - IT/OT Boundary                             │   │
│  │ DMZ Collector - Syslog Aggregation                      │   │
│  │ DMZ Transfer - Secure File Movement                     │   │
│  │ DMZ Pentest - Controlled Testing                        │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

### Network Zones

```
Network Layout:
═════════════════════════════════════════════════════════════════

IT Network (172.26.0.0/16)
├─ EWS (Engineering Workstation)
├─ DMZ Pentest
└─ Management Interface

DMZ Layer (172.27.0.0/16)
├─ DMZ Router (Gateway)
├─ DMZ Collector (Syslog aggregator)
├─ DMZ Transfer (File transfer)
└─ DMZ Pentest (Controlled access)

OT Network (172.25.0.0/16)
├─ Master PLC (172.25.0.10)
├─ Slave PLC 1 (172.25.1.10)
├─ Slave PLC 2 (172.25.2.10)
├─ Slave PLC 3 (172.25.3.10)
├─ SCADA Server (172.25.0.20)
├─ Router (172.25.0.1)
├─ IDS (172.25.0.30)
├─ Collector (172.25.0.40)
└─ ELK Stack (172.25.0.50)

Management Network (172.28.0.0/16)
└─ Central Monitoring & Analytics
```

### Communication Flows

```
Normal Operation Flow:
1. SCADA → Master PLC: "Switch track segment 1 to route A"
2. Master PLC → Slave PLC 1: "Activate switch A1"
3. Slave PLC 1 → Sensors: Read switch position
4. Slave PLC 1 → Actuators: Activate barrier
5. Slave PLC 1 → Master PLC: "Switch A1 activated, position confirmed"
6. Master PLC → SCADA: "Segment 1 route changed to A"
7. All devices → Collector: Syslog events
8. Collector → ELK: Processed logs

Safety-Critical Flow:
1. Slave PLC 1: Detects unauthorized switch command
2. Slave PLC 1 → Emergency System: Trigger safety interlock
3. Emergency System → All Slaves: Stop all operations
4. All devices → Syslog: Emergency event
5. Collector → Alert System: CRITICAL - Unauthorized command
```

---

## Component Overview

### 1. Master PLC
**Role:** Central coordinator for all track segments  
**Responsibilities:**
- Receive track routing commands from SCADA
- Coordinate multiple slave PLCs
- Maintain system state and safety
- Enforce interlocking rules
- Collect status from all segments

**Key Features:**
- Modbus TCP master (polls slaves)
- State machine for track routing
- Safety override capabilities
- Heartbeat monitoring
- Event logging

### 2. Slave PLCs (Segment Controllers)
**Role:** Local control for each track segment  
**Responsibilities:**
- Execute switch commands from master
- Monitor sensor inputs (position, occupancy)
- Control actuators (switches, barriers, signals)
- Local safety interlocking
- Report status to master

**Configuration:**
- Slave PLC 1: Segment North (Entrance)
- Slave PLC 2: Segment Central (Junction)
- Slave PLC 3: Segment South (Yard)

### 3. SCADA Server
**Role:** Operator interface and system control  
**Capabilities:**
- Display railroad network map
- Send routing commands
- Monitor system status
- Historical data viewing
- Alarm management

### 4. Engineering Workstation (EWS)
**Role:** Configuration and development  
**Capabilities:**
- PLC programming
- System diagnostics
- Parameter adjustment
- Firmware updates

### 5. Network Infrastructure
- **Master Router:** Route Modbus traffic between zones
- **DMZ Router:** IT/OT boundary enforcement
- **Network Switches:** Segment isolation

### 6. Monitoring Stack
- **IDS:** Network intrusion detection
- **Collector:** Syslog aggregation
- **ELK:** Log analysis and visualization

---

## Docker Infrastructure

### Directory Structure

```
railroad-north/
├── docker-compose.yml
├── master-plc/
│   ├── Dockerfile
│   ├── master_plc.py
│   ├── ladder_logic.st
│   └── config.json
├── slave-plc/
│   ├── Dockerfile
│   ├── slave_plc.py
│   ├── segment_config.json
│   └── safety_interlocks.conf
├── scada/
│   ├── Dockerfile
│   ├── scada_server.py
│   └── web_ui/
├── network-config/
│   ├── router-rules.conf
│   ├── firewall-rules.conf
│   └── vlan-config.conf
├── monitoring/
│   ├── logstash.conf
│   ├── elasticsearch.yml
│   ├── kibana-dashboards.json
│   └── zeek-rules.sig
├── scripts/
│   ├── deploy.sh
│   ├── health-check.sh
│   ├── traffic-generator.py
│   └── reset-lab.sh
└── training-materials/
    ├── scenarios/
    ├── lab-manual.md
    └── instructor-guide.md
```

### Create Directory Structure

```bash
mkdir -p railroad-north/{master-plc,slave-plc,scada,network-config,monitoring,scripts,training-materials/scenarios}
cd railroad-north
```

---

## Docker Compose Configuration

### FILE: docker-compose.yml

```yaml
version: '3.8'

services:
  # ============================================================================
  # CONTROL CENTER - DMZ LAYER
  # ============================================================================
  
  ews:
    image: ubuntu:22.04
    container_name: railroad-ews
    hostname: ews
    networks:
      it-network:
        ipv4_address: 172.26.0.10
      dmz-network:
        ipv4_address: 172.27.0.10
    ports:
      - "5901:5901"    # VNC
      - "3389:3389"    # RDP
      - "8082:8080"    # OpenPLC Editor
    volumes:
      - ./master-plc:/home/ot/master-plc
      - ./slave-plc:/home/ot/slave-plc
      - ews-data:/data
    environment:
      - DISPLAY=:1
    restart: unless-stopped
    labels:
      - "zone=dmz"
      - "component=ews"

  scada:
    image: python:3.11-slim
    container_name: railroad-scada
    hostname: scada
    networks:
      dmz-network:
        ipv4_address: 172.27.0.20
      ot-network:
        ipv4_address: 172.25.0.20
    ports:
      - "8080:8080"    # SCADA Web UI
      - "502:502"      # Modbus TCP
    volumes:
      - ./scada:/app
      - scada-data:/data
    environment:
      - PYTHONUNBUFFERED=1
      - SCADA_ROLE=central_control
      - MASTER_PLC_IP=172.25.0.10
      - MASTER_PLC_PORT=502
    command: python /app/scada_server.py
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    labels:
      - "zone=dmz"
      - "component=scada"
    depends_on:
      - master-plc

  # ============================================================================
  # OT NETWORK - CONTROL LAYER
  # ============================================================================
  
  master-plc:
    image: python:3.11-slim
    container_name: railroad-master-plc
    hostname: master-plc
    networks:
      ot-network:
        ipv4_address: 172.25.0.10
    ports:
      - "5020:502"     # Modbus TCP
    volumes:
      - ./master-plc:/app
      - master-plc-data:/data
    environment:
      - PYTHONUNBUFFERED=1
      - PLC_ROLE=master
      - LISTEN_IP=0.0.0.0
      - LISTEN_PORT=502
      - SLAVE_CONFIGS=/app/slave_config.json
      - LOG_LEVEL=INFO
    command: python /app/master_plc.py
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import socket; socket.create_connection(('localhost', 502), timeout=2)"]
      interval: 30s
      timeout: 10s
      retries: 3
    labels:
      - "zone=ot"
      - "component=master-plc"
      - "criticality=critical"

  slave-plc-1:
    image: python:3.11-slim
    container_name: railroad-slave-plc-1
    hostname: slave-plc-1
    networks:
      ot-network:
        ipv4_address: 172.25.1.10
    ports:
      - "5021:502"     # Modbus TCP
    volumes:
      - ./slave-plc:/app
      - ./slave-plc/segment_1.json:/app/config/segment.json
      - slave-plc-1-data:/data
    environment:
      - PYTHONUNBUFFERED=1
      - PLC_ROLE=slave
      - SLAVE_ID=1
      - SEGMENT_NAME=North
      - LISTEN_PORT=502
      - MASTER_IP=172.25.0.10
      - MASTER_PORT=502
      - LOG_LEVEL=INFO
    command: python /app/slave_plc.py
    restart: unless-stopped
    labels:
      - "zone=ot"
      - "component=slave-plc"
      - "segment=north"
    depends_on:
      - master-plc

  slave-plc-2:
    image: python:3.11-slim
    container_name: railroad-slave-plc-2
    hostname: slave-plc-2
    networks:
      ot-network:
        ipv4_address: 172.25.2.10
    ports:
      - "5022:502"     # Modbus TCP
    volumes:
      - ./slave-plc:/app
      - ./slave-plc/segment_2.json:/app/config/segment.json
      - slave-plc-2-data:/data
    environment:
      - PYTHONUNBUFFERED=1
      - PLC_ROLE=slave
      - SLAVE_ID=2
      - SEGMENT_NAME=Central
      - LISTEN_PORT=502
      - MASTER_IP=172.25.0.10
      - MASTER_PORT=502
      - LOG_LEVEL=INFO
    command: python /app/slave_plc.py
    restart: unless-stopped
    labels:
      - "zone=ot"
      - "component=slave-plc"
      - "segment=central"
    depends_on:
      - master-plc

  slave-plc-3:
    image: python:3.11-slim
    container_name: railroad-slave-plc-3
    hostname: slave-plc-3
    networks:
      ot-network:
        ipv4_address: 172.25.3.10
    ports:
      - "5023:502"     # Modbus TCP
    volumes:
      - ./slave-plc:/app
      - ./slave-plc/segment_3.json:/app/config/segment.json
      - slave-plc-3-data:/data
    environment:
      - PYTHONUNBUFFERED=1
      - PLC_ROLE=slave
      - SLAVE_ID=3
      - SEGMENT_NAME=South
      - LISTEN_PORT=502
      - MASTER_IP=172.25.0.10
      - MASTER_PORT=502
      - LOG_LEVEL=INFO
    command: python /app/slave_plc.py
    restart: unless-stopped
    labels:
      - "zone=ot"
      - "component=slave-plc"
      - "segment=south"
    depends_on:
      - master-plc

  # ============================================================================
  # NETWORK COMPONENTS
  # ============================================================================
  
  router:
    image: alpine:latest
    container_name: railroad-router
    hostname: router
    networks:
      ot-network:
        ipv4_address: 172.25.0.1
      dmz-network:
        ipv4_address: 172.27.0.1
    ports:
      - "22:22"
    volumes:
      - ./network-config:/etc/network
    command: /bin/sh -c "while true; do sleep 3600; done"
    restart: unless-stopped
    labels:
      - "zone=ot"
      - "component=router"

  dmz-router:
    image: alpine:latest
    container_name: railroad-dmz-router
    hostname: dmz-router
    networks:
      it-network:
        ipv4_address: 172.26.0.1
      dmz-network:
        ipv4_address: 172.27.0.1
    volumes:
      - ./network-config:/etc/network
    restart: unless-stopped
    labels:
      - "zone=dmz"
      - "component=dmz-router"

  # ============================================================================
  # MONITORING LAYER
  # ============================================================================
  
  ids:
    image: zeek/zeek:latest
    container_name: railroad-ids
    hostname: ids
    networks:
      ot-network:
        ipv4_address: 172.25.0.30
    ports:
      - "5901:5901"    # VNC
    volumes:
      - ./monitoring/zeek-rules.sig:/opt/zeek/etc/site.sig
      - zeek-logs:/zeek/logs
    environment:
      - ZEEK_INSTALL_DIR=/opt/zeek
    restart: unless-stopped
    labels:
      - "zone=ot"
      - "component=ids"

  collector:
    image: python:3.11-slim
    container_name: railroad-collector
    hostname: collector
    networks:
      ot-network:
        ipv4_address: 172.25.0.40
    ports:
      - "514:514/udp"   # Syslog
      - "5000:5000/tcp" # TCP Syslog
    volumes:
      - ./monitoring:/app
      - collector-logs:/logs
    environment:
      - PYTHONUNBUFFERED=1
      - SYSLOG_PORT=514
      - LISTEN_IP=0.0.0.0
    command: python /app/syslog_collector.py
    restart: unless-stopped
    labels:
      - "zone=ot"
      - "component=collector"

  dmz-collector:
    image: python:3.11-slim
    container_name: railroad-dmz-collector
    hostname: dmz-collector
    networks:
      dmz-network:
        ipv4_address: 172.27.0.40
    ports:
      - "514:514/udp"   # Syslog
      - "5000:5000/tcp" # TCP Syslog
    volumes:
      - ./monitoring:/app
      - dmz-collector-logs:/logs
    environment:
      - PYTHONUNBUFFERED=1
      - SYSLOG_PORT=514
      - LISTEN_IP=0.0.0.0
    restart: unless-stopped
    labels:
      - "zone=dmz"
      - "component=dmz-collector"

  dmz-transfer:
    image: python:3.11-slim
    container_name: railroad-dmz-transfer
    hostname: dmz-transfer
    networks:
      it-network:
        ipv4_address: 172.26.0.30
      dmz-network:
        ipv4_address: 172.27.0.30
    ports:
      - "8081:8081"    # HTTPS
      - "22:22"        # SFTP
    volumes:
      - ./monitoring:/app
      - dmz-transfer-data:/data
    environment:
      - PYTHONUNBUFFERED=1
      - LISTEN_PORT=8081
    restart: unless-stopped
    labels:
      - "zone=dmz"
      - "component=dmz-transfer"

  dmz-pentest:
    image: ubuntu:22.04
    container_name: railroad-dmz-pentest
    hostname: dmz-pentest
    networks:
      it-network:
        ipv4_address: 172.26.0.20
      dmz-network:
        ipv4_address: 172.27.0.20
    ports:
      - "8083:8080"    # Web interface
    volumes:
      - ./scripts:/app
    environment:
      - PYTHONUNBUFFERED=1
    command: /bin/bash -c "apt-get update && apt-get install -y python3 python3-pip curl telnet && python3 /app/pentest-fury.py"
    restart: unless-stopped
    labels:
      - "zone=dmz"
      - "component=pentest"

  pentest:
    image: ubuntu:22.04
    container_name: railroad-pentest
    hostname: pentest
    networks:
      ot-network:
        ipv4_address: 172.25.0.60
    ports:
      - "8084:8080"
    volumes:
      - ./scripts:/app
      - pentest-data:/data
    environment:
      - PYTHONUNBUFFERED=1
    command: /bin/bash -c "apt-get update && apt-get install -y python3 python3-pip curl telnet nmap && python3 /app/pentest-fury.py"
    restart: unless-stopped
    labels:
      - "zone=ot"
      - "component=pentest"

  # ============================================================================
  # ELASTICSEARCH & KIBANA
  # ============================================================================
  
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    container_name: railroad-elasticsearch
    hostname: elasticsearch
    networks:
      ot-network:
        ipv4_address: 172.25.0.50
    ports:
      - "9200:9200"
      - "9300:9300"
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data
      - ./monitoring/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml
    restart: unless-stopped
    healthcheck:
      test: curl -s http://localhost:9200 >/dev/null || exit 1
      interval: 30s
      timeout: 10s
      retries: 5
    labels:
      - "zone=ot"
      - "component=elasticsearch"

  kibana:
    image: docker.elastic.co/kibana/kibana:8.0.0
    container_name: railroad-kibana
    hostname: kibana
    networks:
      ot-network:
        ipv4_address: 172.25.0.51
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
      - ELASTICSEARCH_USERNAME=elastic
      - ELASTICSEARCH_PASSWORD=changeme
    volumes:
      - ./monitoring/kibana-dashboards.json:/usr/share/kibana/dashboards.json
    depends_on:
      - elasticsearch
    restart: unless-stopped
    healthcheck:
      test: curl -s http://localhost:5601/api/status >/dev/null || exit 1
      interval: 30s
      timeout: 10s
      retries: 5
    labels:
      - "zone=ot"
      - "component=kibana"

  # ============================================================================
  # LOGSTASH (Log Processing)
  # ============================================================================
  
  logstash:
    image: docker.elastic.co/logstash/logstash:8.0.0
    container_name: railroad-logstash
    hostname: logstash
    networks:
      ot-network:
        ipv4_address: 172.25.0.52
    ports:
      - "5000:5000/tcp"
      - "5001:5001/udp"
      - "9600:9600"
    volumes:
      - ./monitoring/logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    environment:
      - ELASTICSEARCH_HOSTS=elasticsearch:9200
    depends_on:
      - elasticsearch
    restart: unless-stopped
    labels:
      - "zone=ot"
      - "component=logstash"

volumes:
  ews-data:
  scada-data:
  master-plc-data:
  slave-plc-1-data:
  slave-plc-2-data:
  slave-plc-3-data:
  zeek-logs:
  collector-logs:
  dmz-collector-logs:
  dmz-transfer-data:
  pentest-data:
  elasticsearch-data:

networks:
  it-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.26.0.0/16
  
  dmz-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.27.0.0/16
  
  ot-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.25.0.0/16
```

---

## PLC Implementation

### FILE: master-plc/master_plc.py

```python
#!/usr/bin/env python3
"""
Railroad North - Master PLC
Coordinates track segments and enforces safety interlocks
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pymodbus.server.asynchronous import StartAsyncTCPServer
from pymodbus.datastore import ModbusSequentialDataStore, ModbusSlaveContext, ModbusServerContext

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
    """Track segment states"""
    IDLE = 0
    SWITCHING = 1
    OCCUPIED = 2
    FAULT = 3
    EMERGENCY_STOP = 4

class RouteType(Enum):
    """Route types in the network"""
    ROUTE_A = 1  # Express mainline
    ROUTE_B = 2  # Local siding
    ROUTE_C = 3  # Maintenance track

@dataclass
class SegmentStatus:
    """Status of a track segment"""
    segment_id: int
    name: str
    state: TrackState
    current_route: Optional[RouteType]
    last_switch_time: datetime
    sensor_occupied: bool
    barrier_engaged: bool
    signal_state: str
    fault_code: int

@dataclass
class SafetyInterlock:
    """Safety rule enforcement"""
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
        
        # Modbus datastore
        self.setup_modbus_datastore()
        
        logger.info("Master PLC initialized")
    
    def _load_slave_configs(self) -> Dict:
        """Load slave PLC configurations"""
        try:
            with open('/app/slave_config.json') as f:
                return json.load(f)
        except:
            logger.warning("Slave config not found, using defaults")
            return {
                'slaves': [
                    {'id': 1, 'name': 'North', 'ip': '172.25.1.10', 'port': 502},
                    {'id': 2, 'name': 'Central', 'ip': '172.25.2.10', 'port': 502},
                    {'id': 3, 'name': 'South', 'ip': '172.25.3.10', 'port': 502}
                ]
            }
    
    def initialize_segments(self):
        """Initialize track segments"""
        for slave in self.slave_configs['slaves']:
            segment_id = slave['id']
            self.segments[segment_id] = SegmentStatus(
                segment_id=segment_id,
                name=slave['name'],
                state=TrackState.IDLE,
                current_route=None,
                last_switch_time=datetime.now(),
                sensor_occupied=False,
                barrier_engaged=False,
                signal_state='RED',
                fault_code=0
            )
    
    def _load_safety_interlocks(self) -> List[SafetyInterlock]:
        """Define safety rules"""
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
    
    def setup_modbus_datastore(self):
        """Setup Modbus datastore"""
        # Initialize datastore
        store = ModbusSequentialDataStore()
        self.context = ModbusServerContext(slaves={0x00: ModbusSlaveContext()}, single=False)
    
    def validate_route_command(self, segment_id: int, route: RouteType) -> tuple:
        """
        Validate route command against safety interlocks
        Returns: (is_valid: bool, reason: str)
        """
        
        # Check segment exists
        if segment_id not in self.segments:
            return False, f"Invalid segment ID: {segment_id}"
        
        segment = self.segments[segment_id]
        
        # Check if segment is in fault state
        if segment.state == TrackState.FAULT:
            return False, f"Segment {segment.name} is in FAULT state"
        
        # Check emergency stop
        if segment.state == TrackState.EMERGENCY_STOP:
            return False, f"Segment {segment.name} is under EMERGENCY STOP"
        
        # Check barrier engagement
        if not segment.barrier_engaged:
            return False, f"Barrier not engaged for segment {segment.name}"
        
        # Check track occupancy
        if segment.sensor_occupied and segment.state == TrackState.SWITCHING:
            return False, f"Cannot switch: track {segment.name} is occupied"
        
        # Check for route conflicts (simplified)
        if segment_id == 2:  # Central junction
            if segment.current_route == RouteType.ROUTE_A and route == RouteType.ROUTE_A:
                if self.segments[1].current_route == RouteType.ROUTE_A:
                    return False, "Conflicting routes at junction"
        
        return True, "Valid"
    
    async def execute_route_command(self, segment_id: int, route: RouteType) -> bool:
        """Execute a route change command"""
        
        # Validate
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
            self.command_history.append(command_log)
            return False
        
        # Update segment
        segment = self.segments[segment_id]
        segment.state = TrackState.SWITCHING
        segment.current_route = route
        segment.last_switch_time = datetime.now()
        
        logger.info(f"APPROVED: Segment {segment.name} route changed to {route.name}")
        
        # Simulate switching delay
        await asyncio.sleep(0.5)
        
        segment.state = TrackState.IDLE
        command_log['executed'] = True
        self.command_history.append(command_log)
        
        # Trim history
        if len(self.command_history) > self.max_history:
            self.command_history.pop(0)
        
        return True
    
    def get_system_status(self) -> Dict:
        """Get complete system status"""
        return {
            'timestamp': datetime.now().isoformat(),
            'segments': [asdict(seg) for seg in self.segments.values()],
            'safety_interlocks': [
                {
                    'rule_id': si.rule_id,
                    'description': si.description,
                    'active': si.active
                }
                for si in self.safety_interlocks
            ],
            'total_commands': len(self.command_history),
            'recent_commands': self.command_history[-10:]
        }
    
    async def start_modbus_server(self):
        """Start Modbus TCP server"""
        logger.info(f"Starting Modbus TCP server on {self.listen_ip}:{self.listen_port}")
        
        try:
            await StartAsyncTCPServer(
                context=self.context,
                address=(self.listen_ip, self.listen_port)
            )
        except Exception as e:
            logger.error(f"Modbus server error: {e}")
    
    async def monitor_slaves(self):
        """Monitor slave PLC heartbeats"""
        while True:
            try:
                for slave in self.slave_configs['slaves']:
                    slave_id = slave['id']
                    # TODO: Implement heartbeat check
                    # For now, just log
                    logger.debug(f"Heartbeat check: Slave {slave_id} ({slave['name']})")
                
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Monitor error: {e}")
    
    async def run(self):
        """Run master PLC"""
        logger.info("Master PLC running")
        
        # Run tasks
        await asyncio.gather(
            self.start_modbus_server(),
            self.monitor_slaves()
        )

# ============================================================================
# REST API FOR TESTING
# ============================================================================

from flask import Flask, jsonify, request

app = Flask(__name__)
master_plc = MasterPLC()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'role': 'master'})

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(master_plc.get_system_status())

@app.route('/api/command', methods=['POST'])
def send_command():
    data = request.json
    segment_id = data.get('segment_id')
    route = RouteType[data.get('route')]
    
    # Execute synchronously for API
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(
        master_plc.execute_route_command(segment_id, route)
    )
    
    return jsonify({'success': result})

@app.route('/api/segments', methods=['GET'])
def get_segments():
    segments = {
        seg_id: asdict(seg)
        for seg_id, seg in master_plc.segments.items()
    }
    return jsonify(segments)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    import threading
    
    # Start Modbus server in background
    async_thread = threading.Thread(
        target=lambda: asyncio.run(master_plc.run()),
        daemon=True
    )
    async_thread.start()
    
    # Start REST API
    logger.info("Starting Flask API on 0.0.0.0:8080")
    app.run(host='0.0.0.0', port=8080, debug=False)
```

### FILE: slave-plc/slave_plc.py

```python
#!/usr/bin/env python3
"""
Railroad North - Slave PLC
Local track segment controller
"""

import asyncio
import json
import logging
import os
import time
import random
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
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
    state: any
    last_update: datetime

# ============================================================================
# SLAVE PLC CLASS
# ============================================================================

class SlavePLC:
    """
    Slave PLC for track segment control
    """
    
    def __init__(self):
        self.slave_id = int(os.environ.get('SLAVE_ID', 1))
        self.segment_name = os.environ.get('SEGMENT_NAME', 'Unknown')
        self.master_ip = os.environ.get('MASTER_IP', '172.25.0.10')
        self.master_port = int(os.environ.get('MASTER_PORT', 502))
        self.listen_port = int(os.environ.get('LISTEN_PORT', 502))
        
        # Load segment configuration
        self.config = self._load_config()
        
        # Initialize devices
        self.devices: Dict[int, LocalDevice] = {}
        self.initialize_devices()
        
        # Operational state
        self.last_master_contact = datetime.now()
        self.heartbeat_interval = 5
        
        logger.info(f"Slave PLC {self.slave_id} ({self.segment_name}) initialized")
    
    def _load_config(self) -> Dict:
        """Load segment configuration"""
        try:
            with open('/app/config/segment.json') as f:
                return json.load(f)
        except:
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
        """Initialize local devices"""
        for dev_config in self.config.get('devices', []):
            dev_id = dev_config['id']
            dev_type = DeviceType[dev_config['type']]
            
            # Initialize with default state
            if dev_type == DeviceType.TRACK_SWITCH:
                initial_state = 'INACTIVE'
            elif dev_type == DeviceType.SIGNAL:
                initial_state = SignalState.RED
            elif dev_type == DeviceType.BARRIER:
                initial_state = 'LOWERED'
            elif dev_type == DeviceType.OCCUPANCY_SENSOR:
                initial_state = False  # Not occupied
            else:
                initial_state = None
            
            self.devices[dev_id] = LocalDevice(
                device_id=dev_id,
                device_type=dev_type,
                name=dev_config['name'],
                state=initial_state,
                last_update=datetime.now()
            )
    
    async def control_track_switch(self, switch_id: int, command: str) -> bool:
        """Control track switch"""
        if switch_id not in self.devices:
            logger.error(f"Unknown switch {switch_id}")
            return False
        
        device = self.devices[switch_id]
        
        if device.device_type != DeviceType.TRACK_SWITCH:
            logger.error(f"Device {switch_id} is not a track switch")
            return False
        
        # Validate command
        if command not in ['ACTIVATE', 'DEACTIVATE']:
            logger.error(f"Invalid command: {command}")
            return False
        
        # Check safety conditions
        if command == 'ACTIVATE':
            # Check if track is occupied
            occupancy_sensor = next(
                (d for d in self.devices.values() 
                 if d.device_type == DeviceType.OCCUPANCY_SENSOR),
                None
            )
            
            if occupancy_sensor and occupancy_sensor.state:
                logger.warning(f"Cannot activate switch {switch_id}: track occupied")
                return False
            
            # Check barrier status
            barrier = next(
                (d for d in self.devices.values() 
                 if d.device_type == DeviceType.BARRIER),
                None
            )
            
            if barrier and barrier.state != 'LOWERED':
                logger.warning(f"Cannot activate switch {switch_id}: barrier not lowered")
                return False
        
        # Execute command
        device.state = 'ACTIVE' if command == 'ACTIVATE' else 'INACTIVE'
        device.last_update = datetime.now()
        
        logger.info(f"Switch {switch_id} ({device.name}) {command}")
        
        # Send audit log
        await self.send_audit_log(
            f"DEVICE_CONTROL: {device.name} {command}"
        )
        
        return True
    
    async def control_signal(self, signal_state: SignalState) -> bool:
        """Control signal light"""
        signal = next(
            (d for d in self.devices.values() 
             if d.device_type == DeviceType.SIGNAL),
            None
        )
        
        if not signal:
            return False
        
        signal.state = signal_state
        signal.last_update = datetime.now()
        
        logger.info(f"Signal {signal.name} set to {signal_state.name}")
        
        await self.send_audit_log(f"SIGNAL_CHANGE: {signal.name} -> {signal_state.name}")
        
        return True
    
    async def send_audit_log(self, message: str):
        """Send audit log to collector"""
        timestamp = datetime.now().isoformat()
        log_message = f"{timestamp} [SLAVE-{self.slave_id}] {message}"
        
        try:
            # Send via syslog to collector
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(log_message.encode(), ('172.25.0.40', 514))
            sock.close()
        except Exception as e:
            logger.error(f"Failed to send audit log: {e}")
    
    async def heartbeat_loop(self):
        """Send heartbeats to master"""
        while True:
            try:
                # TODO: Send heartbeat to master PLC
                logger.debug(f"Heartbeat: Slave {self.slave_id}")
                await asyncio.sleep(self.heartbeat_interval)
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
    
    def get_status(self) -> Dict:
        """Get segment status"""
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
                    'last_update': dev.last_update.isoformat()
                }
                for dev_id, dev in self.devices.items()
            }
        }
    
    async def run(self):
        """Run slave PLC"""
        logger.info(f"Slave PLC {self.slave_id} ({self.segment_name}) running")
        
        await asyncio.gather(
            self.heartbeat_loop()
        )

# ============================================================================
# REST API
# ============================================================================

from flask import Flask, jsonify, request

app = Flask(__name__)
slave_plc = SlavePLC()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'role': 'slave', 'slave_id': slave_plc.slave_id})

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(slave_plc.get_status())

@app.route('/api/device/switch', methods=['POST'])
def control_switch():
    data = request.json
    switch_id = data.get('switch_id')
    command = data.get('command')
    
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(slave_plc.control_track_switch(switch_id, command))
    
    return jsonify({'success': result})

@app.route('/api/device/signal', methods=['POST'])
def control_signal():
    data = request.json
    state = SignalState[data.get('state')]
    
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(slave_plc.control_signal(state))
    
    return jsonify({'success': result})

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    import threading
    
    # Start async operations
    async_thread = threading.Thread(
        target=lambda: asyncio.run(slave_plc.run()),
        daemon=True
    )
    async_thread.start()
    
    # Start REST API
    logger.info(f"Starting Slave {slave_plc.slave_id} API on 0.0.0.0:8080")
    app.run(host='0.0.0.0', port=8080, debug=False)
```

---

## SCADA Implementation

### FILE: scada/scada_server.py

```python
#!/usr/bin/env python3
"""
Railroad North - Central SCADA Server
Operator interface for railroad control
"""

import json
import logging
import os
from datetime import datetime
from enum import Enum
from typing import Dict, List
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import requests

logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO'),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATA STRUCTURES
# ============================================================================

class RouteOption(Enum):
    ROUTE_A = 1  # Express
    ROUTE_B = 2  # Local
    ROUTE_C = 3  # Maintenance

# ============================================================================
# SCADA SERVER CLASS
# ============================================================================

class SCADAServer:
    """Central SCADA server for railroad control"""
    
    def __init__(self):
        self.master_plc_ip = os.environ.get('MASTER_PLC_IP', '172.25.0.10')
        self.master_plc_port = int(os.environ.get('MASTER_PLC_PORT', 502))
        
        # Segment configuration
        self.segments = {
            1: {'name': 'North (Entrance)', 'ip': '172.25.1.10'},
            2: {'name': 'Central (Junction)', 'ip': '172.25.2.10'},
            3: {'name': 'South (Yard)', 'ip': '172.25.3.10'}
        }
        
        # Command history
        self.command_history: List[Dict] = []
        
        logger.info("SCADA Server initialized")
    
    def get_master_status(self) -> Dict:
        """Get master PLC status"""
        try:
            response = requests.get(
                f'http://{self.master_plc_ip}:8080/api/status',
                timeout=2
            )
            return response.json()
        except Exception as e:
            logger.error(f"Cannot reach Master PLC: {e}")
            return {'error': 'Master PLC unreachable'}
    
    def send_route_command(self, segment_id: int, route: str) -> Dict:
        """Send route change command to master PLC"""
        try:
            command_data = {
                'segment_id': segment_id,
                'route': route,
                'timestamp': datetime.now().isoformat(),
                'operator': 'SCADA'
            }
            
            response = requests.post(
                f'http://{self.master_plc_ip}:8080/api/command',
                json=command_data,
                timeout=2
            )
            
            result = response.json()
            
            # Log command
            self.command_history.append({
                **command_data,
                'result': result
            })
            
            logger.info(f"Command sent: Segment {segment_id} -> Route {route}")
            
            return result
        except Exception as e:
            logger.error(f"Command failed: {e}")
            return {'error': str(e), 'success': False}
    
    def get_system_overview(self) -> Dict:
        """Get complete system overview"""
        master_status = self.get_master_status()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'master_plc': master_status,
            'segments': self.segments,
            'recent_commands': self.command_history[-5:]
        }

# ============================================================================
# FLASK APP
# ============================================================================

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
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Courier New', monospace;
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            color: #00ff00;
            padding: 20px;
            min-height: 100vh;
        }
        .header {
            background: #000;
            border: 2px solid #00ff00;
            padding: 20px;
            margin-bottom: 20px;
            text-align: center;
        }
        .header h1 {
            font-size: 28px;
            letter-spacing: 2px;
            margin-bottom: 5px;
        }
        .status-bar {
            background: #111;
            border: 1px solid #00ff00;
            padding: 10px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
        }
        .container {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }
        .segment {
            background: #1a1a1a;
            border: 2px solid #00ff00;
            padding: 20px;
            border-radius: 5px;
        }
        .segment h3 {
            margin-bottom: 15px;
            color: #ffff00;
        }
        .segment-status {
            background: #0a0a0a;
            padding: 10px;
            margin-bottom: 10px;
            border-left: 3px solid #00ff00;
        }
        .control-buttons {
            display: flex;
            gap: 10px;
            margin-top: 15px;
            flex-wrap: wrap;
        }
        button {
            background: #1a1a1a;
            color: #00ff00;
            border: 1px solid #00ff00;
            padding: 8px 15px;
            cursor: pointer;
            font-family: monospace;
            font-size: 12px;
            transition: all 0.3s;
        }
        button:hover {
            background: #00ff00;
            color: #000;
        }
        button:active {
            transform: scale(0.95);
        }
        .log-panel {
            grid-column: 1 / -1;
            background: #0a0a0a;
            border: 2px solid #00ff00;
            padding: 20px;
            max-height: 300px;
            overflow-y: auto;
            font-size: 12px;
        }
        .log-entry {
            margin: 5px 0;
            padding: 5px;
            border-left: 2px solid #00ff00;
            padding-left: 10px;
        }
        .success { color: #00ff00; }
        .error { color: #ff0000; }
        .warning { color: #ffff00; }
        .info { color: #00ffff; }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="header">
        <h1>RAILROAD NORTH</h1>
        <p>Central SCADA Control Center - Master-Slave PLC Architecture</p>
    </div>
    
    <div class="status-bar">
        <span>Master PLC: <span id="master-status">Connecting...</span></span>
        <span>System Time: <span id="system-time">--:--:--</span></span>
        <span>Total Commands: <span id="command-count">0</span></span>
    </div>
    
    <div class="container">
        <div class="segment">
            <h3>🚂 Segment 1: North (Entrance)</h3>
            <div class="segment-status">
                <div id="seg1-status">Loading...</div>
            </div>
            <div class="control-buttons">
                <button onclick="sendCommand(1, 'ROUTE_A')">Route A (Express)</button>
                <button onclick="sendCommand(1, 'ROUTE_B')">Route B (Local)</button>
                <button onclick="sendCommand(1, 'ROUTE_C')">Route C (Maint)</button>
            </div>
        </div>
        
        <div class="segment">
            <h3>🚄 Segment 2: Central (Junction)</h3>
            <div class="segment-status">
                <div id="seg2-status">Loading...</div>
            </div>
            <div class="control-buttons">
                <button onclick="sendCommand(2, 'ROUTE_A')">Route A (Express)</button>
                <button onclick="sendCommand(2, 'ROUTE_B')">Route B (Local)</button>
                <button onclick="sendCommand(2, 'ROUTE_C')">Route C (Maint)</button>
            </div>
        </div>
        
        <div class="segment">
            <h3>🚃 Segment 3: South (Yard)</h3>
            <div class="segment-status">
                <div id="seg3-status">Loading...</div>
            </div>
            <div class="control-buttons">
                <button onclick="sendCommand(3, 'ROUTE_A')">Route A (Express)</button>
                <button onclick="sendCommand(3, 'ROUTE_B')">Route B (Local)</button>
                <button onclick="sendCommand(3, 'ROUTE_C')">Route C (Maint)</button>
            </div>
        </div>
        
        <div class="log-panel">
            <h3>📋 Command Log</h3>
            <div id="log-content"></div>
        </div>
    </div>
    
    <script>
        async function updateStatus() {
            try {
                const resp = await fetch('/api/overview');
                const data = await resp.json();
                
                // Update master status
                const masterStatus = data.master_plc.error ? 
                    '<span class="error">OFFLINE</span>' : 
                    '<span class="success">ONLINE</span>';
                document.getElementById('master-status').innerHTML = masterStatus;
                
                // Update segments
                if (data.master_plc.segments) {
                    data.master_plc.segments.forEach(seg => {
                        const segDiv = document.getElementById(`seg${seg.segment_id}-status`);
                        segDiv.innerHTML = `
                            State: <span class="info">${seg.state}</span><br>
                            Route: <span class="warning">${seg.current_route || 'NONE'}</span><br>
                            Occupied: <span class="${seg.sensor_occupied ? 'error' : 'success'}">${seg.sensor_occupied ? 'YES' : 'NO'}</span>
                        `;
                    });
                }
                
                // Update command log
                const logDiv = document.getElementById('log-content');
                const commands = data.recent_commands || [];
                logDiv.innerHTML = commands.reverse().map(cmd => `
                    <div class="log-entry ${cmd.result.success ? 'success' : 'error'}">
                        [${cmd.timestamp}] Segment ${cmd.segment_id}: ${cmd.route} - ${cmd.result.success ? 'SUCCESS' : 'REJECTED'}
                    </div>
                `).join('');
                
                document.getElementById('command-count').textContent = commands.length;
                
            } catch (e) {
                console.error('Update failed:', e);
            }
        }
        
        async function sendCommand(segment_id, route) {
            try {
                const resp = await fetch('/api/command', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ segment_id, route })
                });
                const data = await resp.json();
                updateStatus();
            } catch (e) {
                alert('Command failed: ' + e);
            }
        }
        
        // Update clock
        setInterval(() => {
            const now = new Date();
            document.getElementById('system-time').textContent = 
                now.toLocaleTimeString();
        }, 1000);
        
        // Initial update and refresh every 2 seconds
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

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    logger.info("Starting SCADA Server on 0.0.0.0:8080")
    app.run(host='0.0.0.0', port=8080, debug=False)
```

---

## Configuration Files

### FILE: slave-plc/segment_1.json

```json
{
  "segment_id": 1,
  "name": "North (Entrance)",
  "devices": [
    {
      "id": 1,
      "type": "TRACK_SWITCH",
      "name": "Switch North-A",
      "modbus_register": 100
    },
    {
      "id": 2,
      "type": "TRACK_SWITCH",
      "name": "Switch North-B",
      "modbus_register": 101
    },
    {
      "id": 3,
      "type": "SIGNAL",
      "name": "Signal North",
      "modbus_register": 110
    },
    {
      "id": 4,
      "type": "BARRIER",
      "name": "Barrier North",
      "modbus_register": 120
    },
    {
      "id": 5,
      "type": "OCCUPANCY_SENSOR",
      "name": "Occupancy North",
      "modbus_register": 130
    }
  ]
}
```

### FILE: master-plc/slave_config.json

```json
{
  "slaves": [
    {
      "id": 1,
      "name": "North (Entrance)",
      "ip": "172.25.1.10",
      "port": 502,
      "heartbeat_interval": 5
    },
    {
      "id": 2,
      "name": "Central (Junction)",
      "ip": "172.25.2.10",
      "port": 502,
      "heartbeat_interval": 5
    },
    {
      "id": 3,
      "name": "South (Yard)",
      "ip": "172.25.3.10",
      "port": 502,
      "heartbeat_interval": 5
    }
  ]
}
```

---

## Deployment & Testing

### Quick Start Script

```bash
#!/bin/bash
# deploy.sh - Deploy Railroad North lab

set -e

echo "╔════════════════════════════════════════════════════╗"
echo "║   Railroad North - Master-Slave Lab Deployment     ║"
echo "╚════════════════════════════════════════════════════╝"

# Create networks
echo "Creating networks..."
docker network create ot-network 2>/dev/null || true
docker network create dmz-network 2>/dev/null || true
docker network create it-network 2>/dev/null || true

# Start services
echo "Starting services..."
docker-compose up -d

# Wait for services
echo "Waiting for services to start..."
sleep 10

# Verify services
echo ""
echo "Service Status:"
docker-compose ps

echo ""
echo "Access Points:"
echo "  SCADA:        http://localhost:8080"
echo "  Master PLC:   http://localhost:8080 (API)"
echo "  Kibana:       http://localhost:5601"
echo "  Elasticsearch: http://localhost:9200"

echo ""
echo "Deployment complete!"
```

---

**Continue to next part for complete training scenarios, monitoring setup, and lab exercises...**

