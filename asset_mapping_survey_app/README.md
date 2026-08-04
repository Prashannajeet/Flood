# Asset Mapping Survey App

Mobile-first asset mapping and DGPS control point survey app for dam, road, river protection, canal, and ground control point inventories.

## Contents

- `asset-mapping-mobile-app.html` - Field survey app with GPS, camera capture, Leaflet maps, Supabase sync, and export.
- `control-points-dashboard.html` - Control point dashboard with map, table, filters, and CSV export.
- `streamlit_app.py` - Streamlit wrapper for hosting the survey app and dashboard.
- `streamlit_dashboard.py` - Dashboard-only Streamlit entry point for publishing the control point dashboard directly.
- `requirements-streamlit.txt` - Streamlit hosting dependency file.
- `supabase-postgis-setup.sql` - Supabase PostgreSQL + PostGIS setup script.
- `asset-mapping-sw.js`, `asset-mapping.webmanifest`, `asset-mapping-icon.svg` - PWA/offline support files.

## Local Web App

Serve this folder with any static web server, then open:

```text
asset-mapping-mobile-app.html
```

## Streamlit Hosting

Install requirements:

```bash
pip install -r requirements-streamlit.txt
```

Run:

```bash
streamlit run streamlit_app.py
```

Run the dashboard-only app:

```bash
streamlit run streamlit_dashboard.py
```

## Supabase Setup

1. Create a Supabase project.
2. Run `supabase-postgis-setup.sql` in the Supabase SQL editor.
3. Open the app, go to `Online Report + Export`, paste the Supabase public / publishable key, and sync records.

The current Supabase project URL is prefilled:

```text
https://lagrhtwsomtwvwkhtchg.supabase.co
```

## GitHub / Streamlit Secrets

For hosted Streamlit deployment, add these repository or deployment secrets:

```text
SUPABASE_URL=https://lagrhtwsomtwvwkhtchg.supabase.co
SUPABASE_SECRET_KEY=<paste Supabase sb_secret key for hosted Streamlit>
SUPABASE_ANON_KEY=<optional public or publishable key fallback>
```

Use `SUPABASE_SECRET_KEY` only in server-side deployment secrets such as Streamlit Cloud or GitHub Actions. Do not paste `sb_secret_*`, `service_role`, or database passwords into browser-facing pages such as the mobile HTML app.

The mobile web app still needs a public/publishable key on the device for direct browser sync.

For Streamlit Community Cloud, add the same values in the app's Secrets settings. For local development, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in the key.

## Recommended Use

- Field survey: direct web app or APK for best GPS/camera behavior.
- Admin review: Streamlit or dashboard page.
- Central data: Supabase PostgreSQL + PostGIS.
