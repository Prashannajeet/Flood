INSERT INTO organizations (id, name) VALUES
('00000000-0000-0000-0000-000000000001', 'Demo Org')
ON CONFLICT (id) DO NOTHING;

INSERT INTO users (id, username, email, full_name) VALUES
('00000000-0000-0000-0000-000000000001', 'demo_user', 'demo@example.com', 'Demo User')
ON CONFLICT (id) DO NOTHING;

INSERT INTO projects (id, org_id, name, description, created_by) VALUES
('00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'Demo Project', 'Seeded demo project', '00000000-0000-0000-0000-000000000001')
ON CONFLICT (id) DO NOTHING;

INSERT INTO scenarios (id, project_id, name, description, parameters, created_by) VALUES
('00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'Demo Scenario', 'Seeded demo scenario', '{}'::jsonb, '00000000-0000-0000-0000-000000000001')
ON CONFLICT (id) DO NOTHING;
