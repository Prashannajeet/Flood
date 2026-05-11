# Flood Modeling Platform Artifacts

This repository provides production-focused architecture assets for a web-enabled HEC-RAS platform using the final recommendation: **Windows-hosted .NET workers** with an API-driven orchestration layer.

## Deliverables

- `openapi/openapi.yaml`: OpenAPI 3.0.3 contract for auth, projects/scenarios, run orchestration, results, and worker callbacks.
- `db/migrations/*.sql`: Versioned Postgres/PostGIS schema migrations for core entities, run tracking, artifacts, and indexes.
- `deploy/docker-compose.yml`: On-prem pilot stack for API dependencies (PostGIS, Redis, MinIO, GeoServer).
- `docs/appendix-e-worker-implementation.md`: .NET worker implementation and operational guidance.

## Quick Start (Pilot)

```bash
cd deploy
docker compose up -d
```

Then:
1. Apply/verify DB migrations from `db/migrations`.
2. Point your API service to the compose dependencies.
3. Deploy Windows .NET workers using the Appendix E guidance.

## Next Implementation Step (Added)

- `services/api/`: API vertical-slice scaffold and behavior contract.
- `services/worker-dotnet/`: .NET worker scaffold docs + example settings.
- `scripts/smoke-test.sh`: end-to-end run lifecycle smoke-test script (for when API is implemented/running).
