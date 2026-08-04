from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from streamlit_dashboard import render_dashboard


ROOT = Path(__file__).parent
MOBILE_APP = ROOT / "asset-mapping-mobile-app.html"


st.set_page_config(
    page_title="Asset Mapping Survey",
    page_icon="AM",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def load_html(path: Path) -> str:
    html = path.read_text(encoding="utf-8")
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
          .phone {
            min-height: 100vh;
            box-shadow: none;
          }
          @media (min-width: 720px) {
            body { padding: 0; place-items: start center; }
            .phone { min-height: 100vh; border-radius: 0; }
            .bottom-nav { bottom: 0; border-radius: 0; }
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
      [data-testid="stMainBlockContainer"] {
        padding: 0 !important;
        margin: 0 !important;
        max-width: none !important;
      }
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

view = st.sidebar.radio(
    "View",
    ["Mobile survey app", "Control point dashboard"],
    label_visibility="collapsed",
)

if view == "Mobile survey app":
    components.html(load_html(MOBILE_APP), height=1080, scrolling=True)
else:
    render_dashboard()
