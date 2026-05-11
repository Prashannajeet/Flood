CREATE TYPE artifact_kind AS ENUM ('INPUT','OUTPUT','LOG','REPORT','LAYER_TILE');
CREATE TYPE artifact_type AS ENUM ('terrain','geometry','boundary','flow','plan','result','timeseries','other');

CREATE TABLE runs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  scenario_id UUID NOT NULL REFERENCES scenarios(id) ON DELETE RESTRICT,
  status run_status NOT NULL DEFAULT 'PENDING',
  progress_pct NUMERIC(5,2) NOT NULL DEFAULT 0.00,
  queued_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  worker_id TEXT,
  error_code TEXT,
  error_message TEXT
);

CREATE TABLE artifacts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  run_id UUID REFERENCES runs(id) ON DELETE SET NULL,
  kind artifact_kind NOT NULL,
  artifact_type artifact_type NOT NULL,
  filename TEXT NOT NULL,
  storage_uri TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
