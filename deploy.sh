#!/bin/bash
set -e

echo "╔════════════════════════════════════════════════════╗"
echo "║   Railroad North - Deployment Script               ║"
echo "║   Master-Slave Distributed PLC Architecture        ║"
echo "╚════════════════════════════════════════════════════╝"

cd "$(dirname "$0")"

echo ""
echo "[1/4] Creating Docker networks..."
docker network create ot-network 2>/dev/null || echo "  ✓ ot-network already exists"
docker network create dmz-network 2>/dev/null || echo "  ✓ dmz-network already exists"
docker network create it-network 2>/dev/null || echo "  ✓ it-network already exists"

echo ""
echo "[2/4] Starting services (this may take 2-3 minutes)..."
docker-compose up -d

echo ""
echo "[3/4] Waiting for services to start..."
sleep 15

echo ""
echo "[4/4] Verifying services..."
docker-compose ps

echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║           Deployment Complete!                     ║"
echo "╚════════════════════════════════════════════════════╝"

echo ""
echo "Access Points:"
echo "  SCADA UI:        http://localhost:8080"
echo "  Master PLC API:  http://localhost:8085/api/status"
echo "  Kibana:          http://localhost:5601"
echo "  Elasticsearch:   http://localhost:9200"
echo ""
echo "Useful Commands:"
echo "  View logs:       docker-compose logs -f"
echo "  Health check:    bash scripts/health-check.sh"
echo "  Reset lab:       bash scripts/reset-lab.sh"
echo ""
