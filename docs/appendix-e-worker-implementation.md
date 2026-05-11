# Appendix E: .NET Worker Implementation (Final Recommendation)

## Goal
Standardize production run execution on a Windows-hosted .NET Worker Service.

## Components
- `RunPollingService`: consumes queue messages.
- `InternalApiClient`: claim/progress/complete/fail endpoints.
- `ArtifactStorageClient`: download inputs and upload outputs.
- `HecRasRunner`: executes HEC-RAS workflows.
- `RunOrchestrator`: controls lifecycle and error mapping.

## Suggested Project Layout
```text
Flood.Worker/
  Program.cs
  WorkerOptions.cs
  Services/
    RunPollingService.cs
    RunOrchestrator.cs
    HecRasRunner.cs
    InternalApiClient.cs
    ArtifactStorageClient.cs
  Models/
  appsettings.json
```

## Runtime Policies
- Max concurrency per host: 1 (start), then scale horizontally.
- Global run timeout: 240 minutes.
- Heartbeat every 15 seconds.
- Use structured logs and persistent run IDs in every log event.

## Error Codes
- INPUT_VALIDATION_ERROR
- ARTIFACT_DOWNLOAD_ERROR
- RAS_EXECUTION_ERROR
- POSTPROCESS_ERROR
- ARTIFACT_UPLOAD_ERROR
- API_CALLBACK_ERROR
- TIMEOUT_ERROR
- UNHANDLED_ERROR

## Deployment
- Build self-contained executable for Windows Server.
- Register via Windows Service Manager.
- Store secrets in secure vault/credential store.
- Allocate dedicated scratch workspace per run: `D:\flood-runs\<run_id>`.
