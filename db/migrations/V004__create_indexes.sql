CREATE INDEX idx_projects_org ON projects(org_id);
CREATE INDEX idx_scenarios_project ON scenarios(project_id);
CREATE INDEX idx_runs_project ON runs(project_id);
CREATE INDEX idx_runs_status ON runs(status);
CREATE INDEX idx_artifacts_project_kind ON artifacts(project_id, kind);
CREATE INDEX idx_artifacts_run ON artifacts(run_id);
