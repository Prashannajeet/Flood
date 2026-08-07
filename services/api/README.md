# API Service (Starter Skeleton)

This is a minimal implementation scaffold for the run orchestration vertical slice.

## MVP endpoints to implement first
- `POST /api/v1/runs`
- `GET /api/v1/runs/{run_id}`
- `POST /api/v1/internal/runs/{run_id}/progress`
- `POST /api/v1/internal/runs/{run_id}/complete`
- `POST /api/v1/internal/runs/{run_id}/fail`

## Suggested stack
- ASP.NET Core Web API (.NET 8)
- PostgreSQL (Npgsql + Dapper/EF Core)
- Redis queue

## Environment variables
- `DATABASE_URL`
- `REDIS_URL`
- `INTERNAL_WORKER_TOKEN`
