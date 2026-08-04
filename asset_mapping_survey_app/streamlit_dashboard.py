from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
import streamlit as st
import streamlit.components.v1 as components


ROOT = Path(__file__).parent
DEFAULT_SUPABASE_URL = "https://lagrhtwsomtwvwkhtchg.supabase.co"
CLOUD_TABLE = "field_records"


def configure_page() -> None:
    st.set_page_config(
        page_title="DGPS Control Points Dashboard",
        page_icon="AM",
        layout="wide",
        initial_sidebar_state="collapsed",
    )


def apply_style() -> None:
    st.markdown(
        """
        <style>
          html, body, .stApp {
            background: #f6f4ee !important;
            color: #17201f;
          }
          [data-testid="stHeader"],
          [data-testid="stToolbar"],
          [data-testid="stDecoration"],
          #MainMenu,
          footer {
            display: none !important;
          }
          .block-container {
            max-width: none !important;
            padding: 14px 16px 26px !important;
          }
          .dash-title {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 14px;
            margin-bottom: 10px;
          }
          .dash-title h1 {
            margin: 0;
            font-size: 28px;
            letter-spacing: 0;
          }
          .dash-title p {
            margin: 4px 0 0;
            color: #66736f;
          }
          .metric-card {
            min-height: 92px;
            padding: 14px;
            border: 1px solid rgba(23,32,31,.1);
            border-radius: 8px;
            background: #fffdfa;
            box-shadow: 0 10px 24px rgba(23,32,31,.06);
          }
          .metric-card b {
            display: block;
            font-size: 26px;
            line-height: 1.1;
          }
          .metric-card span {
            color: #66736f;
            font-size: 13px;
          }
          .panel {
            padding: 14px;
            border: 1px solid rgba(23,32,31,.1);
            border-radius: 8px;
            background: #fffdfa;
            box-shadow: 0 10px 24px rgba(23,32,31,.06);
          }
          .small-muted {
            color: #66736f;
            font-size: 13px;
          }
          div[data-testid="stMetric"] {
            padding: 12px;
            border: 1px solid rgba(23,32,31,.1);
            border-radius: 8px;
            background: #fffdfa;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def secret_value(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, default))
    except Exception:
        return default


def fetch_records(supabase_url: str, anon_key: str) -> tuple[list[dict[str, Any]], str]:
    if not supabase_url or not anon_key:
        return [], "Add Supabase URL and public/publishable key, then press Refresh."

    base = supabase_url.rstrip("/")
    endpoint = f"{base}/rest/v1/{CLOUD_TABLE}"
    headers = {
        "apikey": anon_key,
        "Authorization": f"Bearer {anon_key}",
        "Accept": "application/json",
    }
    params = {"select": "*", "order": "updated_at.desc"}

    try:
        response = requests.get(endpoint, headers=headers, params=params, timeout=20)
    except requests.RequestException as exc:
        return [], f"Could not reach Supabase: {exc}"

    if response.status_code >= 400:
        try:
            details = response.json()
            message = details.get("message") or details.get("hint") or response.text
        except ValueError:
            message = response.text
        return [], f"Supabase returned {response.status_code}: {message}"

    try:
        return response.json(), ""
    except ValueError:
        return [], "Supabase returned data that could not be read."


def payload(row: dict[str, Any]) -> dict[str, Any]:
    data = row.get("payload") or {}
    return data if isinstance(data, dict) else {}


def control_data(record: dict[str, Any]) -> dict[str, Any]:
    control = record.get("control") or {}
    return control if isinstance(control, dict) else {}


def normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    record = payload(row)
    control = control_data(record)
    lat = control.get("lat") or row.get("latitude") or record.get("lat")
    lng = control.get("lng") or row.get("longitude") or record.get("lng")
    photos = control.get("photos") or record.get("media") or []
    return {
        "id": row.get("id") or record.get("id") or "",
        "project": row.get("project_name") or record.get("projectName") or "Mohanpura",
        "asset_name": row.get("asset_name") or record.get("name") or "",
        "record_type": row.get("record_type") or record.get("type") or "",
        "condition": row.get("condition") or record.get("condition") or "",
        "latitude": to_float(lat),
        "longitude": to_float(lng),
        "control_type": row.get("control_type") or control.get("type") or "",
        "control_id": row.get("control_id") or control.get("id") or "",
        "control_name": control.get("name") or "",
        "surveyor_name": row.get("surveyor_name") or control.get("surveyorName") or "",
        "northing": control.get("northing") or "",
        "easting": control.get("easting") or "",
        "ellipsoidal_height": control.get("ellipsoidalHeight") or "",
        "elevation": control.get("elevation") or "",
        "vertical_datum": control.get("verticalDatum") or "",
        "dgps_accuracy": control.get("dgpsAccuracy") or "",
        "observation_time": control.get("observationTime") or "",
        "drone_flight": control.get("droneFlightId") or "",
        "drone_altitude": control.get("droneAltitude") or "",
        "photo_count": row.get("photo_count") or len(photos or []),
        "updated_at": row.get("updated_at") or "",
        "description": control.get("description") or record.get("issue") or "",
    }


def to_float(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if -180 <= result <= 180 else None


def records_to_table(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [normalize_row(row) for row in rows]


def metric_cards(records: list[dict[str, Any]]) -> None:
    controls = [item for item in records if item["record_type"] == "Control" or item["control_type"]]
    dgps = [item for item in controls if "DGPS" in item["control_type"]]
    drone = [item for item in controls if "Drone" in item["control_type"]]
    missing_photos = [item for item in controls if not item["photo_count"]]
    projects = sorted({item["project"] for item in records if item["project"]})

    cols = st.columns(5)
    values = [
        (len(controls), "Total control points"),
        (len(dgps), "DGPS BM/TBM"),
        (len(drone), "Drone GCP/checkpoints"),
        (len(missing_photos), "Missing photos"),
        (len(projects), "Projects"),
    ]
    for col, (value, label) in zip(cols, values):
        with col:
            st.markdown(f'<div class="metric-card"><b>{value}</b><span>{label}</span></div>', unsafe_allow_html=True)


def render_map(records: list[dict[str, Any]]) -> None:
    mapped = [item for item in records if item["latitude"] is not None and item["longitude"] is not None]
    center_lat = mapped[0]["latitude"] if mapped else 21.1498
    center_lng = mapped[0]["longitude"] if mapped else 79.0806
    markers = json.dumps(mapped)

    html = f"""
    <!doctype html>
    <html>
    <head>
      <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
      <style>
        html, body, #map {{ margin:0; width:100%; height:520px; }}
        .leaflet-control-layers-toggle {{
          background-image: none !important;
          display: grid;
          place-items: center;
        }}
        .leaflet-control-layers-toggle::after {{
          content: "Layers";
          font-size: 11px;
          font-weight: 800;
          color: #123a43;
        }}
      </style>
    </head>
    <body>
      <div id="map"></div>
      <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
      <script>
        const records = {markers};
        const map = L.map('map').setView([{center_lat}, {center_lng}], records.length ? 13 : 5);
        const streets = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{{z}}/{{y}}/{{x}}', {{ attribution: 'Tiles Esri' }});
        const satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{ attribution: 'Tiles Esri' }});
        const labels = L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{{z}}/{{y}}/{{x}}', {{ attribution: 'Labels Esri' }});
        const hybrid = L.layerGroup([satellite, labels]);
        streets.addTo(map);
        L.control.layers({{
          'ArcGIS Streets': streets,
          'ArcGIS Satellite': satellite,
          'ArcGIS Satellite Hybrid': hybrid
        }}, null, {{ collapsed: true }}).addTo(map);

        const bounds = [];
        records.forEach((record) => {{
          const color = record.control_type && record.control_type.includes('Drone') ? '#1c7d99' : '#123a43';
          const marker = L.circleMarker([record.latitude, record.longitude], {{
            radius: 8,
            color: '#fffdfa',
            weight: 2,
            fillColor: color,
            fillOpacity: .95
          }}).addTo(map);
          marker.bindPopup(`
            <b>${{record.control_name || record.control_id || record.asset_name || record.id}}</b><br>
            Project: ${{record.project}}<br>
            Type: ${{record.control_type || record.record_type}}<br>
            Surveyor: ${{record.surveyor_name || 'Pending'}}<br>
            Northing: ${{record.northing || 'Pending'}}<br>
            Easting: ${{record.easting || 'Pending'}}<br>
            Ellipsoidal Ht: ${{record.ellipsoidal_height || 'Pending'}}
          `);
          bounds.push([record.latitude, record.longitude]);
        }});
        if (bounds.length > 1) map.fitBounds(bounds, {{ padding: [30, 30] }});
        if (bounds.length === 1) map.setView(bounds[0], 17);
      </script>
    </body>
    </html>
    """
    components.html(html, height=520, scrolling=False)


def render_table(records: list[dict[str, Any]]) -> None:
    columns = [
        "control_id",
        "project",
        "control_name",
        "surveyor_name",
        "control_type",
        "record_type",
        "latitude",
        "longitude",
        "northing",
        "easting",
        "ellipsoidal_height",
        "elevation",
        "vertical_datum",
        "dgps_accuracy",
        "photo_count",
        "updated_at",
    ]
    table = [{column: item.get(column, "") for column in columns} for item in records]
    st.dataframe(table, use_container_width=True, hide_index=True)


def apply_filters(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    projects = ["All"] + sorted({item["project"] for item in records if item["project"]})
    control_types = ["All"] + sorted({item["control_type"] for item in records if item["control_type"]})
    col1, col2, col3, col4 = st.columns([1.3, 1.1, 1.1, 1.4])
    with col1:
        project = st.selectbox("Project", projects)
    with col2:
        control_type = st.selectbox("Control type", control_types)
    with col3:
        photo_filter = st.selectbox("Photo evidence", ["All", "With photos", "Missing photos"])
    with col4:
        search = st.text_input("Search", placeholder="BM/TBM name, surveyor, asset, ID")

    filtered = records
    if project != "All":
        filtered = [item for item in filtered if item["project"] == project]
    if control_type != "All":
        filtered = [item for item in filtered if item["control_type"] == control_type]
    if photo_filter == "With photos":
        filtered = [item for item in filtered if item["photo_count"]]
    if photo_filter == "Missing photos":
        filtered = [item for item in filtered if not item["photo_count"]]
    if search:
        needle = search.lower()
        filtered = [
            item for item in filtered
            if needle in " ".join(str(value).lower() for value in item.values())
        ]
    return filtered


def render_dashboard() -> None:
    apply_style()
    st.markdown(
        """
        <div class="dash-title">
          <div>
            <h1>DGPS Control Points Dashboard</h1>
            <p>Streamlit online report for BM, TBM, drone GCP, checkpoint and mapped control records</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Online database connection", expanded=True):
        col1, col2, col3 = st.columns([1.3, 1.8, 0.7])
        with col1:
            supabase_url = st.text_input(
                "Supabase project URL",
                value=secret_value("SUPABASE_URL", DEFAULT_SUPABASE_URL),
            )
        with col2:
            anon_key = st.text_input(
                "Supabase public / publishable key",
                value=secret_value("SUPABASE_ANON_KEY", ""),
                type="password",
                help="Use the public/publishable client key. Do not use service-role or secret keys here.",
            )
        with col3:
            refresh = st.button("Refresh", type="primary", use_container_width=True)

    if "dashboard_rows" not in st.session_state or refresh:
        rows, error = fetch_records(supabase_url, anon_key)
        st.session_state.dashboard_rows = rows
        st.session_state.dashboard_error = error
        st.session_state.dashboard_refreshed_at = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    if st.session_state.get("dashboard_error"):
        st.warning(st.session_state.dashboard_error)

    records = records_to_table(st.session_state.get("dashboard_rows", []))
    st.caption(f"Last refresh: {st.session_state.get('dashboard_refreshed_at', 'Not refreshed')}")

    metric_cards(records)
    st.write("")

    filtered = apply_filters(records)

    left, right = st.columns([1.35, 1])
    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.subheader("Control Map")
        render_map(filtered)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.subheader("Selected / latest record")
        latest = filtered[0] if filtered else None
        if latest:
            st.write(f"**{latest['control_name'] or latest['control_id'] or latest['asset_name'] or latest['id']}**")
            st.write(f"Project: {latest['project']}")
            st.write(f"Surveyor: {latest['surveyor_name'] or 'Pending'}")
            st.write(f"Type: {latest['control_type'] or latest['record_type']}")
            st.write(f"Northing: {latest['northing'] or 'Pending'}")
            st.write(f"Easting: {latest['easting'] or 'Pending'}")
            st.write(f"Ellipsoidal Ht: {latest['ellipsoidal_height'] or 'Pending'}")
            st.write(f"Photos: {latest['photo_count']}")
        else:
            st.info("No records match the current filters.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.subheader("Control Data Elements")
    render_table(filtered)

    csv_rows = records_to_table(st.session_state.get("dashboard_rows", []))
    st.download_button(
        "Download CSV",
        data=to_csv(csv_rows),
        file_name="dgps-control-points-streamlit.csv",
        mime="text/csv",
    )


def csv_escape(value: Any) -> str:
    text = "" if value is None else str(value)
    return '"' + text.replace('"', '""') + '"'


def to_csv(records: list[dict[str, Any]]) -> str:
    if not records:
        return ""
    columns = list(records[0].keys())
    lines = [",".join(columns)]
    for record in records:
        lines.append(",".join(csv_escape(record.get(column, "")) for column in columns))
    return "\n".join(lines)


if __name__ == "__main__":
    configure_page()
    render_dashboard()
