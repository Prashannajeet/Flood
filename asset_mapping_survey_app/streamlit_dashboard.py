from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


ROOT = Path(__file__).parent
DASHBOARD_APP = ROOT / "control-points-dashboard.html"


st.set_page_config(
    page_title="DGPS Control Points Dashboard",
    page_icon="AM",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def load_dashboard() -> str:
    html = DASHBOARD_APP.read_text(encoding="utf-8")
    return html.replace(
        "</head>",
        """
        <style>
          html, body {
            margin: 0;
            width: 100%;
            min-height: 100vh;
            overflow-x: hidden;
            background: #f6f4ee;
          }
          .page {
            max-width: none;
            padding: 14px;
          }
        </style>
        </head>
        """,
    )


st.markdown(
    """
    <style>
      html, body, #root, .stApp {
        margin: 0 !important;
        padding: 0 !important;
        min-height: 100vh !important;
        overflow: hidden !important;
        background: #f6f4ee !important;
      }
      [data-testid="stHeader"],
      [data-testid="stToolbar"],
      [data-testid="stDecoration"],
      #MainMenu,
      footer {
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        visibility: hidden !important;
      }
      [data-testid="stAppViewContainer"],
      [data-testid="stMain"],
      [data-testid="stMainBlockContainer"],
      .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: none !important;
      }
      iframe {
        display: block !important;
        width: 100% !important;
        border: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

components.html(load_dashboard(), height=1180, scrolling=True)
