from datetime import datetime, timezone
from typing import Literal
import os
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import psycopg
from psycopg.rows import dict_row
import redis

app = FastAPI(title="Flood API", version="0.1.0")

DB_URL = os.getenv("DATABASE_URL", "postgresql://flood_user:flood_pass@localhost:5432/flood")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_NAME = os.getenv("RUN_QUEUE_NAME", "run_jobs")

r = redis.Redis.from_url(REDIS_URL, decode_responses=True)


class RunCreate(BaseModel):
    project_id: uuid.UUID
    scenario_id: uuid.UUID
    input_artifact_ids: list[uuid.UUID] = Field(min_length=1)
    priority: Literal["low", "normal", "high"] = "normal"


class RunStatusResponse(BaseModel):
    run_id: uuid.UUID
    status: str
    progress_pct: float
    queued_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    worker_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class WorkerProgress(BaseModel):
    progress_pct: float = Field(ge=0, le=100)
    log_chunk: list[dict] = []


class WorkerFail(BaseModel):
    error_code: str
    error_message: str


def _priority_to_int(priority: str) -> int:
    return {"high": 1, "normal": 5, "low": 9}[priority]


def _conn():
    return psycopg.connect(DB_URL, row_factory=dict_row)


@app.get("/health/live")
def live():
    return {"status": "ok"}


@app.post("/api/v1/runs", status_code=202)
def submit_run(payload: RunCreate):
    run_id = uuid.uuid4()
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO runs (id, project_id, scenario_id, status, priority, progress_pct, queued_at)
            VALUES (%s, %s, %s, 'PENDING', %s, 0, %s)
            """,
            (str(run_id), str(payload.project_id), str(payload.scenario_id), _priority_to_int(payload.priority), datetime.now(timezone.utc)),
        )
        conn.commit()

    r.rpush(QUEUE_NAME, str(run_id))
    return {"run_id": str(run_id), "status": "PENDING"}


@app.get("/api/v1/runs/{run_id}", response_model=RunStatusResponse)
def get_run(run_id: uuid.UUID):
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id AS run_id, status, progress_pct, queued_at, started_at, completed_at, worker_id, error_code, error_message FROM runs WHERE id = %s", (str(run_id),))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Run not found")
    return row


@app.get("/api/v1/runs/{run_id}/logs")
def get_logs(run_id: uuid.UUID, offset: int = 0, limit: int = 200):
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, ts, level, message FROM run_logs WHERE run_id = %s ORDER BY id OFFSET %s LIMIT %s",
            (str(run_id), offset, limit),
        )
        rows = cur.fetchall()
    return {"run_id": str(run_id), "offset": offset, "limit": limit, "entries": rows}


@app.post("/api/v1/internal/runs/{run_id}/progress")
def progress(run_id: uuid.UUID, payload: WorkerProgress):
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("UPDATE runs SET status='RUNNING', progress_pct=%s, started_at=COALESCE(started_at, now()) WHERE id=%s", (payload.progress_pct, str(run_id)))
        for line in payload.log_chunk:
            cur.execute("INSERT INTO run_logs (run_id, level, message) VALUES (%s, %s, %s)", (str(run_id), line.get("level", "INFO"), line.get("message", "")))
        conn.commit()
    return {"ok": True}


@app.post("/api/v1/internal/runs/{run_id}/complete")
def complete(run_id: uuid.UUID):
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("UPDATE runs SET status='SUCCEEDED', progress_pct=100, completed_at=now() WHERE id=%s", (str(run_id),))
        conn.commit()
    return {"ok": True}


@app.post("/api/v1/internal/runs/{run_id}/fail")
def fail(run_id: uuid.UUID, payload: WorkerFail):
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE runs SET status='FAILED', completed_at=now(), error_code=%s, error_message=%s WHERE id=%s",
            (payload.error_code, payload.error_message, str(run_id)),
        )
        conn.commit()
    return {"ok": True}
