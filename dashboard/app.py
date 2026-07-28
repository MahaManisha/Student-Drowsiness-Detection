"""
Student Drowsiness Detection System - Main Streamlit Dashboard Entry Point

Decoupled Multi-Rate Fragment Refresh Architecture:
- Camera Viewport Fragment: 30 FPS (0.033s) isolated st.image video stream
- Telemetry Cards Fragment: 10 FPS (0.100s) numerical & status indicator cards
- Plotly Charts & Decision Panel Fragment: 1 FPS (1.0s) Plotly SVG reticle & gauges
- Session Statistics Fragment: 1 FPS (1.0s) bottom historical analytics
"""

import os
import sys
import time
import datetime
import pathlib
import traceback
import pandas as pd
import streamlit as st

# Add project root directory to path for clean imports
ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Page configuration
st.set_page_config(
    page_title="Student Drowsiness Detection System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import dashboard components & Singleton Lifecycle Manager
from dashboard.components.header import render_header
from dashboard.components.sidebar import render_sidebar
from dashboard.components.camera_panel import (
    render_camera_panel_header,
    render_camera_panel_footer,
    render_camera_error_state,
)
from dashboard.components.telemetry_panel import render_telemetry_panel
from dashboard.components.head_pose_panel import render_head_pose_panel
from dashboard.components.decision_panel import render_decision_panel
from dashboard.components.bottom_analytics import render_bottom_analytics
from dashboard.components.analytics_dashboard import render_analytics_dashboard
from dashboard.components.lifecycle import (
    get_singleton_camera_manager,
    print_singleton_health_log,
)
from dashboard.utils.mock_data import MockTelemetryProvider


def load_css(css_file_path: str) -> None:
    """Injects custom CSS file into Streamlit DOM."""
    if os.path.exists(css_file_path):
        with open(css_file_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


@st.fragment(run_every="0.033s")
def render_camera_viewport(camera_mgr) -> None:
    """
    Stage 1: Camera Viewport Fragment (≈30 FPS / 0.033s).
    Renders ONLY live video viewport. Never waits for Plotly or analytics rendering.
    """
    success, rgb_frame, telemetry = camera_mgr.get_processed_frame()
    if success and (rgb_frame is not None or telemetry.get("jpeg_bytes") is not None):
        img_payload = telemetry.get("jpeg_bytes") if telemetry.get("jpeg_bytes") is not None else rgb_frame
        try:
            st.image(img_payload, use_container_width=True)
        except Exception:
            pass
    else:
        error_msg = camera_mgr.last_error or "Camera device is offline or busy."
        st.error(f"⚠️ {error_msg}")


@st.fragment(run_every="0.100s")
def render_telemetry_cards(camera_mgr) -> None:
    """
    Stage 2: Telemetry Cards Fragment (10 FPS / 0.100s).
    Renders numerical stat cards: EAR, MAR, Blinks, Yawns, Eye & Mouth State Badges.
    """
    _, _, telemetry = camera_mgr.get_processed_frame()
    render_telemetry_panel(telemetry)


@st.fragment(run_every="1.0s")
def render_charts_and_decision(camera_mgr) -> None:
    """
    Stage 3: Plotly Charts & Decision Panel Fragment (1 FPS / 1.0s).
    Renders Plotly 3D reticle compass, circular drowsiness gauge, and XAI matrix.
    """
    _, _, telemetry = camera_mgr.get_processed_frame()
    render_head_pose_panel(telemetry)
    render_decision_panel(telemetry)


@st.fragment(run_every="1.0s")
def render_session_analytics(camera_mgr) -> None:
    """
    Stage 4: Session Statistics & Historical Analytics Fragment (1 FPS / 1.0s).
    Renders bottom session stats and long-term trend line charts.
    """
    _, _, telemetry = camera_mgr.get_processed_frame()

    if "telemetry_history" not in st.session_state:
        st.session_state.telemetry_history = []

    now_str = time.strftime("%H:%M:%S", time.localtime())
    st.session_state.telemetry_history.append({
        "timestamp": now_str,
        "ear": telemetry.get("avg_ear", 0.285) if telemetry.get("avg_ear") is not None else 0.0,
        "mar": telemetry.get("mar", 0.180) if telemetry.get("mar") is not None else 0.0,
        "score": telemetry.get("drowsiness_score", 0.0),
        "blinks": telemetry.get("blink_count", 0),
        "yawns": telemetry.get("yawn_count", 0),
        "state": telemetry.get("drowsiness_state", "ALERT")
    })
    if len(st.session_state.telemetry_history) > 150:
        st.session_state.telemetry_history = st.session_state.telemetry_history[-150:]

    history_df = pd.DataFrame(st.session_state.telemetry_history)

    render_bottom_analytics(telemetry, camera_connected=telemetry.get("has_face", True))
    render_analytics_dashboard(telemetry, history_df, force_chart_update=True)


def render_live_dashboard(camera_mgr) -> None:
    """
    Assembles multi-rate decoupled dashboard layout.
    """
    _, _, telemetry = camera_mgr.get_processed_frame()

    # Render Header (Outer Page)
    render_header(telemetry)

    col_center, col_right = st.columns([1.8, 1.2], gap="medium")

    with col_center:
        st.markdown('<div class="dash-card">', unsafe_allow_html=True)
        render_camera_panel_header(
            is_live=True,
            has_face=telemetry.get("has_face", True),
            state_str=telemetry.get("drowsiness_state", "ALERT")
        )

        # Isolated Container 1: 30 FPS Camera Feed
        viewport_container = st.container()
        with viewport_container:
            render_camera_viewport(camera_mgr)

        render_camera_panel_footer(fps=telemetry.get("fps", 30.0), resolution="1280x720")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        # Isolated Container 2: 10 FPS Telemetry Cards
        telemetry_container = st.container()
        with telemetry_container:
            render_telemetry_cards(camera_mgr)

        # Isolated Container 3: 1 FPS Plotly Charts & Decision Panel
        charts_container = st.container()
        with charts_container:
            render_charts_and_decision(camera_mgr)

    # Isolated Container 4: 1 FPS Bottom Analytics & Session Stats
    analytics_container = st.container()
    with analytics_container:
        render_session_analytics(camera_mgr)


def main() -> None:
    """Main application driver."""
    css_path = os.path.join(os.path.dirname(__file__), "styles", "custom.css")
    load_css(css_path)

    selected_page = render_sidebar()

    if selected_page == "Reports":
        st.switch_page("pages/1_📊_Reports.py")
    elif selected_page == "Session History":
        st.switch_page("pages/2_📜_Session_History.py")
    elif selected_page == "Settings":
        st.switch_page("pages/3_⚙️_Settings.py")
    elif selected_page == "About":
        st.switch_page("pages/4_ℹ️_About.py")

    # Retrieve Singleton Camera Manager Instance
    camera_mgr = get_singleton_camera_manager()

    # Render Multi-Rate Decoupled Live Dashboard
    render_live_dashboard(camera_mgr)


if __name__ == "__main__":
    main()
