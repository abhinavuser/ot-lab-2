# Railroad North Lab - Quick Start Deployment
## Copy-Paste Ready Step-by-Step Guide

---

## 🚀 DEPLOYMENT IN 5 STEPS (Total Time: 30 minutes)

### Step 1: Create Lab Directory & Clone Files (5 minutes)

```bash
# Create main directory
mkdir -p /home/railroad-north
cd /home/railroad-north

# Create subdirectories
mkdir -p {master-plc,slave-plc,scada,network-config,monitoring,scripts,training-materials}
mkdir -p {master-plc,slave-plc,scada}/config

echo "✓ Directories created"
```

### Step 2: Create Docker Compose File (5 minutes)

**COPY THE ENTIRE docker-compose.yml from Part 1 into:**
```bash
/home/railroad-north/docker-compose.yml
```

**Then verify:**
```bash
cd /home/railroad-north
docker-compose config > /dev/null && echo "✓ Valid configuration"
```

### Step 3: Deploy Python Code Files (10 minutes)

#### Master PLC Code

**File:** `/home/railroad-north/master-plc/master_plc.py`

```bash
cat > /home/railroad-north/master-plc/master_plc.py << 'EOFPYTHON'
# COPY ENTIRE master_plc.py CODE FROM PART 1 HERE
EOFPYTHON
```

**File:** `/home/railroad-north/master-plc/slave_config.json`

```bash
cat > /home/railroad-north/master-plc/slave_config.json << 'EOFJSON'
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
EOFJSON

echo "✓ Master PLC files created"
```

#### Slave PLC Code

**File:** `/home/railroad-north/slave-plc/slave_plc.py`

```bash
cat > /home/railroad-north/slave-plc/slave_plc.py << 'EOFPYTHON'
# COPY ENTIRE slave_plc.py CODE FROM PART 1 HERE
EOFPYTHON
```

**Create segment configs:**

```bash
# Segment 1 (North)
cat > /home/railroad-north/slave-plc/segment_1.json << 'EOF'
{
  "segment_id": 1,
  "name": "North (Entrance)",
  "devices": [
    {"id": 1, "type": "TRACK_SWITCH", "name": "Switch North-A", "modbus_register": 100},
    {"id": 2, "type": "TRACK_SWITCH", "name": "Switch North-B", "modbus_register": 101},
    {"id": 3, "type": "SIGNAL", "name": "Signal North", "modbus_register": 110},
    {"id": 4, "type": "BARRIER", "name": "Barrier North", "modbus_register": 120},
    {"id": 5, "type": "OCCUPANCY_SENSOR", "name": "Occupancy North", "modbus_register": 130}
  ]
}
EOF

# Segment 2 (Central)
cat > /home/railroad-north/slave-plc/segment_2.json << 'EOF'
{
  "segment_id": 2,
  "name": "Central (Junction)",
  "devices": [
    {"id": 1, "type": "TRACK_SWITCH", "name": "Switch Central-A", "modbus_register": 100},
    {"id": 2, "type": "TRACK_SWITCH", "name": "Switch Central-B", "modbus_register": 101},
    {"id": 3, "type": "SIGNAL", "name": "Signal Central", "modbus_register": 110},
    {"id": 4, "type": "BARRIER", "name": "Barrier Central", "modbus_register": 120},
    {"id": 5, "type": "OCCUPANCY_SENSOR", "name": "Occupancy Central", "modbus_register": 130}
  ]
}
EOF

# Segment 3 (South)
cat > /home/railroad-north/slave-plc/segment_3.json << 'EOF'
{
  "segment_id": 3,
  "name": "South (Yard)",
  "devices": [
    {"id": 1, "type": "TRACK_SWITCH", "name": "Switch South-A", "modbus_register": 100},
    {"id": 2, "type": "TRACK_SWITCH", "name": "Switch South-B", "modbus_register": 101},
    {"id": 3, "type": "SIGNAL", "name": "Signal South", "modbus_register": 110},
    {"id": 4, "type": "BARRIER", "name": "Barrier South", "modbus_register": 120},
    {"id": 5, "type": "OCCUPANCY_SENSOR", "name": "Occupancy South", "modbus_register": 130}
  ]
}
EOF

echo "✓ Slave PLC segment configs created"
```

#### SCADA Server

**File:** `/home/railroad-north/scada/scada_server.py`

```bash
cat > /home/railroad-north/scada/scada_server.py << 'EOFPYTHON'
# COPY ENTIRE scada_server.py CODE FROM PART 1 HERE
EOFPYTHON

echo "✓ SCADA Server files created"
```

#### Monitoring Configuration

**File:** `/home/railroad-north/monitoring/logstash.conf`

```bash
cat > /home/railroad-north/monitoring/logstash.conf << 'EOF'
# COPY ENTIRE logstash.conf CODE FROM PART 2 HERE
EOF

echo "✓ Logstash configuration created"
```

**File:** `/home/railroad-north/monitoring/elasticsearch.yml`

```bash
cat > /home/railroad-north/monitoring/elasticsearch.yml << 'EOF'
cluster.name: "railroad-north"
node.name: "node-1"
network.host: 0.0.0.0
network.publish_host: elasticsearch
http.port: 9200
transport.port: 9300
discovery.type: single-node
action.auto_create_index: "+railr*,-.watch_*"
index.number_of_shards: 1
index.number_of_replicas: 0
xpack.security.enabled: false
xpack.ml.enabled: false
xpack.graph.enabled: false
logger.level: info
EOF

echo "✓ Elasticsearch configuration created"
```

**File:** `/home/railroad-north/monitoring/syslog_collector.py`

```bash
cat > /home/railroad-north/monitoring/syslog_collector.py << 'EOFPYTHON'
# COPY ENTIRE syslog_collector.py CODE FROM PART 2 HERE
EOFPYTHON

chmod +x /home/railroad-north/monitoring/syslog_collector.py
echo "✓ Syslog collector created"
```

### Step 4: Create Deployment Script (5 minutes)

**File:** `/home/railroad-north/deploy.sh`

```bash
cat > /home/railroad-north/deploy.sh << 'EOFSCRIPT'
#!/bin/bash

set -e

echo "╔════════════════════════════════════════════════════╗"
echo "║   Railroad North - Deployment Script               ║"
echo "║   Master-Slave Distributed PLC Architecture        ║"
echo "╚════════════════════════════════════════════════════╝"

# Change to lab directory
cd "$(dirname "$0")"

# Step 1: Create networks
echo ""
echo "[1/5] Creating Docker networks..."
docker network create ot-network 2>/dev/null || echo "  ✓ ot-network already exists"
docker network create dmz-network 2>/dev/null || echo "  ✓ dmz-network already exists"
docker network create it-network 2>/dev/null || echo "  ✓ it-network already exists"

# Step 2: Create volumes
echo ""
echo "[2/5] Creating Docker volumes..."
docker volume create master-plc-data 2>/dev/null || echo "  ✓ master-plc-data already exists"
docker volume create slave-plc-1-data 2>/dev/null || echo "  ✓ slave-plc-1-data already exists"
docker volume create slave-plc-2-data 2>/dev/null || echo "  ✓ slave-plc-2-data already exists"
docker volume create slave-plc-3-data 2>/dev/null || echo "  ✓ slave-plc-3-data already exists"
docker volume create scada-data 2>/dev/null || echo "  ✓ scada-data already exists"
docker volume create elasticsearch-data 2>/dev/null || echo "  ✓ elasticsearch-data already exists"

# Step 3: Start services
echo ""
echo "[3/5] Starting services (this may take 2-3 minutes)..."
docker-compose up -d

# Step 4: Wait for services
echo ""
echo "[4/5] Waiting for services to start..."
sleep 15

# Step 5: Verify services
echo ""
echo "[5/5] Verifying services..."
docker-compose ps

echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║           Deployment Complete!                     ║"
echo "╚════════════════════════════════════════════════════╝"

echo ""
echo "Access Points:"
echo "  SCADA UI:        http://localhost:8080"
echo "  Master PLC API:  http://localhost:8080/api/status"
echo "  Kibana:          http://localhost:5601"
echo "  Elasticsearch:   http://localhost:9200"
echo ""
echo "Useful Commands:"
echo "  View logs:       docker-compose logs -f"
echo "  Health check:    bash scripts/health-check.sh"
echo "  Reset lab:       bash scripts/reset-lab.sh"
echo ""
EOFSCRIPT

chmod +x /home/railroad-north/deploy.sh
echo "✓ Deployment script created"
```

### Step 5: Run Deployment (5 minutes)

```bash
cd /home/railroad-north

# Execute deployment
bash deploy.sh

# Wait for all services to start
echo ""
echo "⏳ Waiting for services to stabilize..."
sleep 30

# Verify deployment
echo ""
echo "Checking system status..."
curl -s http://localhost:8080/health | jq '.' || echo "⚠️  Master PLC not ready yet, waiting..."
sleep 10

# Final check
echo ""
echo "✓ Deployment successful!"
```

---

## 📊 VERIFY DEPLOYMENT

### Check All Containers Running

```bash
docker-compose ps

# Should show 15 containers:
# ✓ railroad-ews (Engineering Workstation)
# ✓ railroad-scada (Central SCADA)
# ✓ railroad-master-plc (Master Controller)
# ✓ railroad-slave-plc-1 (North Segment)
# ✓ railroad-slave-plc-2 (Central Segment)
# ✓ railroad-slave-plc-3 (South Segment)
# ✓ railroad-ids (Zeek Network Monitoring)
# ✓ railroad-collector (Syslog Collector)
# ✓ railroad-dmz-collector (DMZ Syslog)
# ✓ railroad-dmz-transfer (DMZ File Transfer)
# ✓ railroad-dmz-pentest (DMZ Pentest Tools)
# ✓ railroad-pentest (OT Pentest Tools)
# ✓ railroad-router (OT Router)
# ✓ railroad-dmz-router (DMZ Router)
# ✓ railroad-elasticsearch (Search & Analytics)
# ✓ railroad-kibana (Visualization)
# ✓ railroad-logstash (Log Processing)
```

### Test Key Services

```bash
# 1. Test Master PLC
echo "Testing Master PLC..."
curl -s http://localhost:8080/health | jq '.status'
# Expected output: "healthy"

# 2. Test SCADA Status
echo "Testing SCADA..."
curl -s http://localhost:8080/api/status | jq '.master_plc.status' 
# Expected output: should show segment data

# 3. Test Elasticsearch
echo "Testing Elasticsearch..."
curl -s http://localhost:9200/_cluster/health | jq '.status'
# Expected output: "green" or "yellow"

# 4. Test Kibana
echo "Testing Kibana..."
curl -s http://localhost:5601/api/status | jq '.state'
# Expected output: "green"
```

### Access the SCADA Interface

Open in web browser: **http://localhost:8080**

You should see:
- Green terminal-style interface
- Master PLC status: ONLINE
- Three track segments (North, Central, South)
- Route control buttons for each segment

---

## 🧪 QUICK TEST: Send Your First Command

### Test 1: Send a Route Change Command

```bash
# Send command via API
curl -X POST http://localhost:8080/api/command \
  -H "Content-Type: application/json" \
  -d '{
    "segment_id": 1,
    "route": "ROUTE_A"
  }' | jq '.'

# Expected response:
# {
#   "success": true,
#   "segment_id": 1,
#   "requested_route": "ROUTE_A"
# }
```

### Test 2: Check System Status

```bash
# Get complete system status
curl -s http://localhost:8080/api/status | jq '.segments'

# Shows status of all 3 track segments
```

### Test 3: View Syslog in Collector

```bash
# Check collector logs
docker logs railroad-collector | tail -20

# Should show audit messages like:
# [SLAVE-1] DEVICE_CONTROL: Switch North-A ACTIVATE
# [MASTER] Command approved: Segment 1 route ROUTE_A
```

### Test 4: View Logs in Kibana

```bash
# Open Kibana
firefox http://localhost:5601

# In Kibana:
# 1. Click "Discover" (left sidebar)
# 2. Create new index pattern: "railroad-*"
# 3. Set timestamp field: "@timestamp"
# 4. View recent logs with "railroad" in them
```

---

## 📁 Complete File Structure After Setup

```
/home/railroad-north/
├── docker-compose.yml          ← Main configuration (15 containers)
├── deploy.sh                   ← Deployment script
├── scripts/
│   ├── health-check.sh        ← Monitor system health
│   ├── reset-lab.sh           ← Clean reset
│   └── traffic-generator.py   ← Generate test traffic
├── master-plc/
│   ├── master_plc.py          ← Master PLC implementation
│   └── slave_config.json      ← Slave PLC addresses
├── slave-plc/
│   ├── slave_plc.py           ← Slave PLC implementation
│   ├── segment_1.json         ← North segment config
│   ├── segment_2.json         ← Central segment config
│   └── segment_3.json         ← South segment config
├── scada/
│   └── scada_server.py        ← Central SCADA server
├── monitoring/
│   ├── logstash.conf          ← Log processing
│   ├── elasticsearch.yml      ← Search config
│   ├── syslog_collector.py   ← Syslog aggregation
│   └── zeek-rules.sig        ← IDS signatures
└── training-materials/
    ├── lab-manual.md
    └── scenarios/
        ├── unauthorized-switching.md
        ├── heartbeat-failure.md
        ├── safety-interlock-bypass.md
        └── modbus-attack.md
```

---

## 🎯 NEXT STEPS AFTER DEPLOYMENT

### 1. Access SCADA Interface (Immediate)
```bash
# Open in browser
firefox http://localhost:8080
# Or Chrome/Safari on http://localhost:8080

# Try the route control buttons
# Observe real-time status updates
```

### 2. Run First Training Scenario (15 minutes)
```bash
# Scenario 1: Normal Operations
# 1. In SCADA, change Segment 1 to Route A
# 2. Observe Master PLC accepts it
# 3. View in logs: docker logs railroad-master-plc

# Expected logs:
# "APPROVED: Segment North route changed to ROUTE_A"
```

### 3. Test Firewall Rules (20 minutes)
```bash
# From IT network (DMZ Pentest), try to reach OT network
docker exec railroad-dmz-pentest ping 172.25.0.10

# From OT network, try to reach external
docker exec railroad-master-plc ping 8.8.8.8

# Both should be blocked by firewall rules
```

### 4. Generate Test Traffic (30 minutes)
```bash
# Create traffic generator script
cat > /home/railroad-north/scripts/test-traffic.py << 'EOF'
#!/usr/bin/env python3
import requests
import time

url = "http://172.25.0.20:8080/api/command"
headers = {"Content-Type": "application/json"}

# Normal operation
for i in range(10):
    data = {
        "segment_id": (i % 3) + 1,
        "route": ["ROUTE_A", "ROUTE_B", "ROUTE_C"][i % 3]
    }
    requests.post(url, json=data, headers=headers)
    print(f"Sent command {i+1}")
    time.sleep(2)

# Rapid-fire (potential attack pattern)
print("\nRapid-fire test...")
for i in range(20):
    requests.post(url, json={"segment_id": 1, "route": "ROUTE_A"}, headers=headers)
    time.sleep(0.1)
EOF

python3 /home/railroad-north/scripts/test-traffic.py
```

### 5. Monitor in Kibana (30 minutes)
```bash
# Open Kibana
firefox http://localhost:5601

# Create dashboard showing:
# - Command history
# - Rejected commands
# - System alerts
# - Device status
```

---

## ⚠️ TROUBLESHOOTING

### Issue: Containers won't start

```bash
# Check Docker disk space
docker system df

# If space is low, clean up
docker system prune

# Then retry deployment
bash deploy.sh
```

### Issue: Master PLC shows OFFLINE

```bash
# Check logs
docker logs railroad-master-plc

# Verify network
docker exec railroad-master-plc ping 172.25.1.10

# If needed, restart
docker-compose restart railroad-master-plc
sleep 10
curl http://localhost:8080/health
```

### Issue: No logs in Kibana

```bash
# Check Elasticsearch
curl http://localhost:9200/_cat/indices

# Check Logstash
docker logs railroad-logstash | grep -i error

# Manually send test syslog
docker exec railroad-collector logger -h 172.25.0.40 "TEST_MESSAGE"

# Wait 5 seconds and check Kibana
```

### Issue: Network connectivity problems

```bash
# Check networks created
docker network ls | grep railroad

# Check container network connections
docker inspect railroad-master-plc | grep -A 20 NetworkSettings

# Test connectivity
docker exec railroad-master-plc ping 172.25.1.10
docker exec railroad-scada ping 172.25.0.10
```

### Issue: SCADA interface not loading

```bash
# Check SCADA container
docker logs railroad-scada

# Verify port is open
curl -I http://localhost:8080

# If port issue, check for conflicts
lsof -i :8080  # See what's using port 8080
```

---

## 📚 TRAINING SCENARIOS QUICK LINKS

Once deployed, try these scenarios:

### Quick Test (5 min)
```bash
# Send conflicting route commands
# Observe Master PLC rejects due to safety interlock
curl -X POST http://localhost:8080/api/command \
  -H "Content-Type: application/json" \
  -d '{"segment_id": 2, "route": "ROUTE_A"}'
```

### Medium Test (20 min)
```bash
# Run normal operations, capture baseline
# Then run rapid commands
# Check logs for anomalies
bash scripts/test-traffic.py
```

### Advanced Test (60 min)
```bash
# Implement Modbus attack scenario
# Try to forge commands from unauthorized source
# Test IDS detection
python3 scripts/modbus-attack.py  # (from Part 2)
```

---

## 📞 SUPPORT & DOCUMENTATION

After deployment, refer to:

**Part 1:** Complete architecture, PLC code, Docker setup  
**Part 2:** Monitoring, scenarios, training exercises, grading rubrics  

Both parts are in `/mnt/user-data/outputs/`:
- `Railroad_North_Complete_Guide.md`
- `Railroad_North_Part2_Scenarios_Training.md`

---

## ✅ DEPLOYMENT CHECKLIST

- [ ] Directory created: `/home/railroad-north`
- [ ] docker-compose.yml copied
- [ ] All Python files created (master, slave, scada, collector)
- [ ] All JSON configs created (slave configs, segment configs)
- [ ] Monitoring configs created (logstash, elasticsearch)
- [ ] Scripts created (deploy, health-check)
- [ ] Deployment executed: `bash deploy.sh`
- [ ] All 15+ containers running: `docker-compose ps`
- [ ] SCADA accessible: `http://localhost:8080`
- [ ] Kibana accessible: `http://localhost:5601`
- [ ] Test command successful
- [ ] Logs appearing in Kibana

---

## 🎓 YOU'RE READY!

Congratulations! You now have a fully functional:
✓ Master-Slave PLC distributed control system
✓ Multi-segment track coordination
✓ Safety interlocking system
✓ Complete monitoring and logging
✓ Security testing infrastructure
✓ Training environment for 20+ lab exercises

**Next:** Run the training scenarios in Part 2!

---

**Duration:** ~30 minutes from zero to fully operational  
**Difficulty:** Intermediate  
**Prerequisites:** Docker installed, basic CLI knowledge  

Happy training! 🚂
