# Flood Modeling Platform Artifacts

This repository contains implementation-ready architecture artifacts for moving to the final recommendation: a production-oriented **.NET Windows Worker Service** for HEC-RAS run orchestration, while keeping interfaces compatible with local on-prem deployment and future online migration.

## Included Deliverables

- `openapi/openapi.yaml`: Complete API contract (OpenAPI 3.0.3).
- `db/migrations/*.sql`: Versioned PostgreSQL/PostGIS migration files.
- `deploy/docker-compose.yml`: On-prem pilot compose stack (API, DB, MinIO, Redis, tile service).
- `docs/appendix-e-worker-implementation.md`: .NET-first implementation skeleton and rollout notes.

## Quick Start

1. Review API contract in `openapi/openapi.yaml`.
2. Apply migrations from `db/migrations` using your migration tool.
3. Launch pilot stack:

```bash
cd deploy
docker compose up -d
```

4. Deploy Windows .NET workers per `docs/appendix-e-worker-implementation.md`.
