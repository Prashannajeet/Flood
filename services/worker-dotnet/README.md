# .NET Worker Service (Starter Skeleton)

Production recommendation: Windows-hosted .NET BackgroundService.

## Responsibilities
1. Poll Redis `run_jobs` queue.
2. Call internal API claim/progress/complete/fail endpoints.
3. Execute HEC-RAS runner wrapper (replace fake executor).
4. Persist logs/progress continuously.

## Initial prototype mode
- Use a fake executor that sleeps and emits progress (10%, 50%, 100%).
- Verify end-to-end run lifecycle before integrating HEC-RAS binary automation.
