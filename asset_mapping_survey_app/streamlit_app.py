from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


ROOT = Path(__file__).parent
MOBILE_APP = ROOT / "asset-mapping-mobile-app.html"
DASHBOARD_APP = ROOT / "control-points-dashboard.html"


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
          html, body { margin: 0; min-height: 100%; background: #f6f4ee; }
          .phone { min-height: 100vh; }
        </style>
        </head>
        """,
    )


st.markdown(
    """
    <style>
      .block-container { padding: 0; max-width: none; }
      header, footer, [data-testid="stToolbar"] { display: none; }
      iframe { display: block; border: 0; }
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
    components.html(load_html(MOBILE_APP), height=920, scrolling=True)
else:
    components.html(load_html(DASHBOARD_APP), height=920, scrolling=True)
