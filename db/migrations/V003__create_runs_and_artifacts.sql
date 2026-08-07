DO $$ BEGIN
  CREATE TYPE artifact_kind AS ENUM ('INPUT','OUTPUT','LOG','REPORT','LAYER_TILE');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
  CREATE TYPE artifact_type AS ENUM ('terrain','geometry','boundary','flow','plan','result','timeseries','other');
EXCEPTION WHEN duplicate_object THEN null; END $$;

CREATE TABLE runs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  scenario_id UUID NOT NULL REFERENCES scenarios(id) ON DELETE RESTRICT,
  status run_status NOT NULL DEFAULT 'PENDING',
  priority SMALLINT NOT NULL DEFAULT 5,
  progress_pct NUMERIC(5,2) NOT NULL DEFAULT 0.00,
  queued_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  worker_id TEXT,
  error_code TEXT,
  error_message TEXT,
  execution_metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE artifacts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  run_id UUID REFERENCES runs(id) ON DELETE SET NULL,
  kind artifact_kind NOT NULL,
  artifact_type artifact_type NOT NULL,
  filename TEXT NOT NULL,
  content_type TEXT,
  size_bytes BIGINT,
  checksum_sha256 TEXT,
  storage_uri TEXT NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE run_logs (
  id BIGSERIAL PRIMARY KEY,
  run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
  ts TIMESTAMPTZ NOT NULL DEFAULT now(),
  level TEXT NOT NULL CHECK (level IN ('DEBUG','INFO','WARN','ERROR')),
  message TEXT NOT NULL
);
