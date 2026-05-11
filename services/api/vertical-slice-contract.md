# Vertical Slice Behavior Contract

## 1) Submit Run
- Insert row in `runs` with status `PENDING`.
- Push `run_id` to Redis queue `run_jobs`.

## 2) Worker Claims/Progress
- Worker sets run to `RUNNING` and updates `worker_id`.
- Worker sends progress and log lines.

## 3) Completion/Failure
- On complete: set `SUCCEEDED`, fill `completed_at`.
- On failure: set `FAILED` with `error_code/error_message`.
