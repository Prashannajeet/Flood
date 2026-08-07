#!/usr/bin/env bash
set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8080/api/v1}"

# Requires jq and a live API implementation.
echo "Submitting run..."
RUN_ID=$(curl -sS -X POST "$API_BASE/runs" \
  -H 'Content-Type: application/json' \
  -d '{"project_id":"00000000-0000-0000-0000-000000000001","scenario_id":"00000000-0000-0000-0000-000000000001","input_artifact_ids":["00000000-0000-0000-0000-000000000001"]}' | jq -r '.run_id')

echo "Run ID: $RUN_ID"

echo "Polling status..."
for i in {1..30}; do
  STATUS=$(curl -sS "$API_BASE/runs/$RUN_ID" | jq -r '.status')
  echo "Status: $STATUS"
  if [[ "$STATUS" == "SUCCEEDED" || "$STATUS" == "FAILED" ]]; then
    break
  fi
  sleep 2
done

curl -sS "$API_BASE/runs/$RUN_ID/logs?offset=0&limit=100" | jq .
