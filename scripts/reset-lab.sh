#!/bin/bash

echo "Resetting Railroad North Lab..."

# Stop all containers
docker-compose down -v

# Recreate volumes
docker volume create master-plc-data 2>/dev/null || true
docker volume create slave-plc-1-data 2>/dev/null || true
docker volume create slave-plc-2-data 2>/dev/null || true
docker volume create slave-plc-3-data 2>/dev/null || true
docker volume create scada-data 2>/dev/null || true
docker volume create elasticsearch-data 2>/dev/null || true
docker volume create zeek-logs 2>/dev/null || true
docker volume create collector-logs 2>/dev/null || true

# Start fresh
docker-compose up -d

echo "Lab reset complete. Waiting for services..."
sleep 30
echo ""
bash scripts/health-check.sh
