"""
Student Drowsiness Detection System - Main Streamlit Dashboard Entry Point

Authoritative Singleton Session Lifecycle Manager Integration.
Retrieves persistent DashboardCameraManager via get_singleton_camera_manager().
Guarantees exactly ONE CameraProducerThread, ONE AIWorkerThread, ONE VideoCapture,
and ONE MediaPipe FaceMesh instance across all reruns and page navigations.
Does NOT modify any backend AI detection algorithms, math calculators, or thresholds.
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
    get_singleton_object_ids,
    print_singleton_health_log,
)
from dashboard.utils.mock_data import MockTelemetryProvider


def log_frame_profile(thread_name: str, func_name: str, stage_marker: str, frame_id: int, elapsed_ms: float, status: str = "OK", extra: str = "") -> None:
    """Logs standardized diagnostic entry into frame_profile.log."""
    try:
        now_str = datetime.datetime.now().isoformat()
        log_line = f"[{now_str}] | [{thread_name}] | [{func_name}] | [{stage_marker}] | Frame: {frame_id} | Elapsed: {elapsed_ms:.3f} ms | Status: {status} {extra}\n"
        with open("frame_profile.log", "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception:
        pass


def load_css(css_file_path: str) -> None:
    """Injects custom CSS file into Streamlit DOM."""
    if os.path.exists(css_file_path):
        with open(css_file_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


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

    if "telemetry_history" not in st.session_state:
        st.session_state.telemetry_history = []

    if "frame_counter" not in st.session_state:
        st.session_state.frame_counter = 0

    st.session_state.frame_counter += 1
    frame_id = st.session_state.frame_counter

    # Log Singleton Health & Object IDs every 30 frames
    if frame_id % 30 == 1:
        print_singleton_health_log()

    success, rgb_frame, telemetry = camera_mgr.get_processed_frame()

    if not success or rgb_frame is None:
        if "mock_provider" not in st.session_state:
            st.session_state.mock_provider = MockTelemetryProvider()
        fallback_telemetry = st.session_state.mock_provider.get_telemetry()
        telemetry.update(fallback_telemetry)

    # Telemetry Update Diagnostic Stage
    t_tel_start = time.time()
    log_frame_profile("StreamlitRenderer", "main", "[BEFORE_TELEMETRY_UPDATE]", frame_id, 0.0)

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

    t_tel_end = time.time()
    log_frame_profile("StreamlitRenderer", "main", "[AFTER_TELEMETRY_UPDATE]", frame_id, (t_tel_end - t_tel_start) * 1000.0, "OK")

    # Render Header
    render_header(telemetry)

    col_center, col_right = st.columns([1.8, 1.2], gap="medium")

    with col_center:
        st.markdown('<div class="dash-card">', unsafe_allow_html=True)
        render_camera_panel_header(
            is_live=success,
            has_face=telemetry.get("has_face", True),
            state_str=telemetry.get("drowsiness_state", "ALERT")
        )

        if success and rgb_frame is not None:
            t_img_start = time.time()
            log_frame_profile("StreamlitRenderer", "main", "[BEFORE_STREAMLIT_IMAGE]", frame_id, 0.0)

            try:
                st.image(rgb_frame, use_container_width=True)
                t_img_end = time.time()
                log_frame_profile("StreamlitRenderer", "main", "[AFTER_STREAMLIT_IMAGE]", frame_id, (t_img_end - t_img_start) * 1000.0, "OK")
            except Exception as e:
                tb_str = traceback.format_exc().replace('\n', ' ')
                log_frame_profile("StreamlitRenderer", "main", "[AFTER_STREAMLIT_IMAGE]", frame_id, 0.0, "EXCEPT", tb_str)

            render_camera_panel_footer(fps=telemetry.get("fps", 30.0), resolution="1280x720")
        else:
            error_msg = camera_mgr.last_error or "Camera device is offline or busy."
            retry_clicked = render_camera_error_state(error_msg)
            if retry_clicked:
                camera_mgr.start()
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        render_telemetry_panel(telemetry)
        render_head_pose_panel(telemetry)
        render_decision_panel(telemetry)

    render_bottom_analytics(telemetry, camera_connected=success)

    force_charts = (st.session_state.frame_counter % 45 == 0) or (st.session_state.frame_counter < 3)
    render_analytics_dashboard(telemetry, history_df, force_chart_update=force_charts)

    log_frame_profile("StreamlitRenderer", "main", "[END_OF_FRAME]", frame_id, 0.0, "OK")

    if success and rgb_frame is not None:
        time.sleep(0.01)
        st.rerun()


if __name__ == "__main__":
    main()
