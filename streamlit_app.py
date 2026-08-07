import os
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

APP_DIR = Path(__file__).resolve().parent
DASHBOARD_FILE = APP_DIR / "dashboard.html"

st.set_page_config(
    page_title="NITA AI - Mohanpura Kundaliya Dam Break & EAP Project",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      .block-container {
        max-width: 100%;
        padding: 0;
      }
      header[data-testid="stHeader"],
      div[data-testid="stToolbar"],
      footer {
        display: none;
      }
      iframe {
        border: 0;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

if not DASHBOARD_FILE.exists():
    st.error("dashboard.html was not found in the app repository.")
    st.stop()

mapbox_token = st.secrets.get("MAPBOX_TOKEN", os.environ.get("MAPBOX_TOKEN", ""))
html = DASHBOARD_FILE.read_text(encoding="utf-8").replace("__MAPBOX_TOKEN__", mapbox_token)
components.html(html, height=940, scrolling=False)
