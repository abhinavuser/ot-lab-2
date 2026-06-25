#!/bin/bash

echo "╔═══════════════════════════════════════════════╗"
echo "║   Railroad North - System Health Check        ║"
echo "╚═══════════════════════════════════════════════╝"

echo ""
echo "Container Status:"
docker-compose ps

echo ""
echo "Master PLC Status:"
curl -s http://localhost:8085/health | python3 -m json.tool 2>/dev/null || echo "OFFLINE"

echo ""
echo "Segment Status:"
curl -s http://localhost:8085/api/status | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for seg in data.get('segments', []):
        print(f\"  Segment {seg['segment_id']}: {seg['name']} - State: {seg['state']} - Route: {seg.get('current_route', 'NONE')}\")
except: print('  ERROR: Cannot read status')
" 2>/dev/null || echo "  ERROR: Master PLC unreachable"

echo ""
echo "Elasticsearch:"
curl -s http://localhost:9200/_cluster/health | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"  Status: {data['status']}, Shards: {data['active_shards']}\")
except: print('  OFFLINE')
" 2>/dev/null || echo "  OFFLINE"

echo ""
echo "Kibana:"
curl -s http://localhost:5601/api/status 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"  Status: {data.get('status', {}).get('overall', {}).get('state', 'unknown')}\")
except: print('  OFFLINE')
" 2>/dev/null || echo "  OFFLINE"

echo ""
echo "Recent Syslog Messages:"
docker logs railroad-collector 2>/dev/null | tail -10 || echo "  No logs"

echo ""
echo "Network Connectivity:"
docker exec railroad-master-plc python3 -c "
import urllib.request
try:
    urllib.request.urlopen('http://172.25.1.10:8080/health', timeout=2)
    print('  Master ↔ Slave1: ✓')
except: print('  Master ↔ Slave1: ✗')
try:
    urllib.request.urlopen('http://172.25.2.10:8080/health', timeout=2)
    print('  Master ↔ Slave2: ✓')
except: print('  Master ↔ Slave2: ✗')
try:
    urllib.request.urlopen('http://172.25.3.10:8080/health', timeout=2)
    print('  Master ↔ Slave3: ✓')
except: print('  Master ↔ Slave3: ✗')
" 2>/dev/null || echo "  Cannot check (Master PLC not running)"

echo ""
echo "Resource Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null | head -20
