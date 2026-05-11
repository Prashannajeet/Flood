#!/usr/bin/env python3
import os
import time
import requests
import redis

API_BASE = os.getenv("API_BASE", "http://localhost:8080/api/v1")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_NAME = os.getenv("RUN_QUEUE_NAME", "run_jobs")

client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

print("Fake worker started. Waiting for jobs...")
while True:
    msg = client.blpop(QUEUE_NAME, timeout=5)
    if not msg:
        continue

    _, run_id = msg
    print(f"Processing run_id={run_id}")

    for pct, note in [(10, "Workspace prepared"), (45, "Running simulation"), (80, "Post-processing outputs")]:
        requests.post(
            f"{API_BASE}/internal/runs/{run_id}/progress",
            json={"progress_pct": pct, "log_chunk": [{"level": "INFO", "message": note}]},
            timeout=15,
        ).raise_for_status()
        time.sleep(2)

    requests.post(f"{API_BASE}/internal/runs/{run_id}/complete", timeout=15).raise_for_status()
    print(f"Completed run_id={run_id}")
