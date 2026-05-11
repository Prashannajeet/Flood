#!/usr/bin/env bash
set -euo pipefail

echo "Starting infrastructure + API containers..."
( cd deploy && docker compose up -d )

echo "Applying demo seed data..."
docker exec -i flood_db psql -U flood_user -d flood < db/seed/001_demo_seed.sql

echo "Starting fake worker (background)..."
nohup python3 scripts/fake-worker.py > /tmp/fake-worker.log 2>&1 &

echo "Serving demo UI at http://localhost:8090 ..."
cd services/demo-ui
python3 -m http.server 8090
