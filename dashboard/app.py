"""
Student Drowsiness Detection System - Main Streamlit Dashboard Entry Point

Decoupled Multi-Rate Fragment Refresh Architecture:
- FAST Tier (30 FPS / 0.033s): Camera Image, Alert Banner, Eye State, Mouth State, EAR, MAR, Head Pose degrees, Drowsiness Risk Score
- SLOW Tier (1 Hz / 1.0s): Session Timer, Blink Count, Yawn Count, Plotly 3D Compass, Plotly Gauge, Historical Analytics, Alert Event History
"""

import sys
import pathlib

# Add project root directory to path for clean imports
ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import os
import time
import datetime
import traceback
import pandas as pd
import streamlit as st
from collections import deque
from typing import Any, Optional

# Page configuration
st.set_page_config(
    page_title="Student Drowsiness Detection System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import dashboard components & Singleton Lifecycle Manager
import importlib
import dashboard.components.camera_panel as camera_panel
importlib.reload(camera_panel)

from dashboard.components.header import render_header
from dashboard.components.sidebar import render_sidebar
from dashboard.components.camera_panel import (
    render_camera_panel_header,
    render_camera_panel_footer,
    render_camera_error_state,
    render_camera_viewport,
)
from dashboard.components.fast_panel import render_fast_telemetry_panel
from dashboard.components.head_pose_panel import render_head_pose_panel
from dashboard.components.decision_panel import render_decision_panel
from dashboard.components.bottom_analytics import render_bottom_analytics
from dashboard.components.analytics_dashboard import render_analytics_dashboard
from dashboard.components.lifecycle import (
    get_singleton_camera_manager,
    print_singleton_health_log,
)
from utils.logger import get_logger
from dashboard.utils.mock_data import MockTelemetryProvider

logger = get_logger(__name__)


def load_css(css_file_path: str) -> None:
    """Injects custom CSS file into Streamlit DOM."""
    if os.path.exists(css_file_path):
        with open(css_file_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def render_live_runtime_instrumentation(snapshot: Any, t_st_image_ms: float, st_fps: float) -> None:
    telemetry = snapshot.telemetry if snapshot else {}
    live_perf = telemetry.get("live_perf", {})

    cam_fps = live_perf.get("camera_fps", 0.0)
    prod_fps = live_perf.get("producer_fps", 0.0)
    ai_fps = live_perf.get("ai_worker_fps", 0.0)

    if "ui_fps_timestamps" not in st.session_state:
        st.session_state.ui_fps_timestamps = deque()

    now_ui = time.time()
    st.session_state.ui_fps_timestamps.append(now_ui)
    while st.session_state.ui_fps_timestamps and st.session_state.ui_fps_timestamps[0] < now_ui - 1.0:
        st.session_state.ui_fps_timestamps.popleft()

    if len(st.session_state.ui_fps_timestamps) > 1:
        elapsed_ui = now_ui - st.session_state.ui_fps_timestamps[0]
        st_render_fps = round((len(st.session_state.ui_fps_timestamps) - 1) / elapsed_ui, 1) if elapsed_ui > 0 else 30.0
    else:
        st_render_fps = 30.0
    browser_fps = st_render_fps

    queue_len = live_perf.get("queue_len", 0)
    latest_frame_id = live_perf.get("latest_frame_id", 0)
    displayed_frame_id = getattr(snapshot, "frame_id", 0)
    proc_time_ms = live_perf.get("ai_total_frame_ms", 0.0)

    t_vcap = live_perf.get("t_videocapture_read_ms", 0.0)
    t_fmesh = live_perf.get("t_facemesh_ms", 0.0)
    t_ear = live_perf.get("t_ear_ms", 0.0)
    t_mar = live_perf.get("t_mar_ms", 0.0)
    t_pose = live_perf.get("t_headpose_ms", 0.0)
    t_hud = live_perf.get("t_hud_draw_ms", 0.0)
    t_rgb = live_perf.get("t_rgb_conversion_ms", 0.0)
    t_st_img = t_st_image_ms

    stages = [
        ("VideoCapture.read()", t_vcap, "camera/camera.py:208"),
        ("FaceMesh (MediaPipe)", t_fmesh, "detection/face_mesh.py:102"),
        ("EAR Calculation", t_ear, "detection/ear_calculator.py:45"),
        ("MAR Calculation", t_mar, "detection/mar_calculator.py:40"),
        ("Head Pose Estimation", t_pose, "detection/head_pose_estimator.py:85"),
        ("HUD Draw Overlay", t_hud, "dashboard/hud.py:110"),
        ("RGB Conversion", t_rgb, "dashboard/components/camera_manager.py:423"),
        ("Streamlit Image Rendering (st.image)", t_st_img, "dashboard/components/camera_panel.py:25 (st.image)")
    ]

    slowest = max(stages, key=lambda x: x[1])
    slowest_name = slowest[0]
    slowest_ms = slowest[1]
    slowest_loc = slowest[2]

    rows_html = ""
    for name, duration_ms, location in stages:
        is_slowest = (name == slowest_name)
        row_bg = "rgba(239, 68, 68, 0.25)" if is_slowest else "transparent"
        text_color = "#EF4444" if is_slowest else "#E5E7EB"
        font_weight = "bold" if is_slowest else "normal"
        badge = ' <span style="background:#EF4444; color:white; padding:2px 6px; border-radius:4px; font-size:0.7rem;">SLOWEST STAGE</span>' if is_slowest else ""

        rows_html += f"""
        <tr style="background-color: {row_bg}; color: {text_color}; font-weight: {font_weight};">
            <td style="padding: 4px 8px; border-bottom: 1px solid rgba(255,255,255,0.05);">{name}{badge}</td>
            <td style="padding: 4px 8px; border-bottom: 1px solid rgba(255,255,255,0.05); text-align: right;">{duration_ms:.2f} ms</td>
            <td style="padding: 4px 8px; border-bottom: 1px solid rgba(255,255,255,0.05); text-align: right; font-size:0.75rem; color:#9CA3AF;">{location}</td>
        </tr>
        """

    bottleneck_msg = f"<strong>FPS Collapse Bottleneck Identified:</strong> {slowest_name} takes <strong>{slowest_ms:.1f} ms</strong> per frame, capping real-time UI refresh at <strong>{st_render_fps} FPS</strong> (File: {slowest_loc})."

    st.markdown(
        f"""
        <div style="background: #1F2937; border: 1px solid #374151; border-radius: 10px; padding: 14px; margin-top: 12px; font-family: monospace;">
            <div style="font-size: 1.0rem; font-weight: bold; color: #F59E0B; margin-bottom: 10px; border-bottom: 1px solid #374151; padding-bottom: 6px;">
                ⚡ LIVE REAL-TIME RUNTIME PERFORMANCE INSTRUMENTATION
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin-bottom: 12px; text-align: center;">
                <div style="background:#111827; padding:6px; border-radius:6px;">
                    <div style="font-size:0.7rem; color:#9CA3AF;">Camera FPS</div>
                    <div style="font-size:1.1rem; font-weight:bold; color:#10B981;">{cam_fps:.1f}</div>
                </div>
                <div style="background:#111827; padding:6px; border-radius:6px;">
                    <div style="font-size:0.7rem; color:#9CA3AF;">Producer FPS</div>
                    <div style="font-size:1.1rem; font-weight:bold; color:#10B981;">{prod_fps:.1f}</div>
                </div>
                <div style="background:#111827; padding:6px; border-radius:6px;">
                    <div style="font-size:0.7rem; color:#9CA3AF;">AI Worker FPS</div>
                    <div style="font-size:1.1rem; font-weight:bold; color:#38BDF8;">{ai_fps:.1f}</div>
                </div>
                <div style="background:#111827; padding:6px; border-radius:6px;">
                    <div style="font-size:0.7rem; color:#9CA3AF;">Streamlit Render FPS</div>
                    <div style="font-size:1.1rem; font-weight:bold; color:#EF4444;">{st_render_fps:.1f}</div>
                </div>
                <div style="background:#111827; padding:6px; border-radius:6px;">
                    <div style="font-size:0.7rem; color:#9CA3AF;">Browser Display FPS</div>
                    <div style="font-size:0.9rem; font-weight:bold; color:#9CA3AF;">N/A (unmeasured)</div>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 12px; text-align: center;">
                <div style="background:#111827; padding:6px; border-radius:6px;">
                    <div style="font-size:0.7rem; color:#9CA3AF;">Queue Length</div>
                    <div style="font-size:1.0rem; font-weight:bold; color:#F59E0B;">{queue_len}</div>
                </div>
                <div style="background:#111827; padding:6px; border-radius:6px;">
                    <div style="font-size:0.7rem; color:#9CA3AF;">Latest AI Frame ID</div>
                    <div style="font-size:1.0rem; font-weight:bold; color:#F59E0B;">#{latest_frame_id}</div>
                </div>
                <div style="background:#111827; padding:6px; border-radius:6px;">
                    <div style="font-size:0.7rem; color:#9CA3AF;">Displayed Frame ID</div>
                    <div style="font-size:1.0rem; font-weight:bold; color:#F59E0B;">#{displayed_frame_id}</div>
                </div>
                <div style="background:#111827; padding:6px; border-radius:6px;">
                    <div style="font-size:0.7rem; color:#9CA3AF;">Processing Time/Frame</div>
                    <div style="font-size:1.0rem; font-weight:bold; color:#F59E0B;">{proc_time_ms:.1f} ms</div>
                </div>
            </div>

            <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem; margin-bottom: 10px;">
                <thead>
                    <tr style="border-bottom: 2px solid #374151; color: #9CA3AF; text-align: left;">
                        <th style="padding: 4px 8px;">Pipeline Stage</th>
                        <th style="padding: 4px 8px; text-align: right;">Measured Time</th>
                        <th style="padding: 4px 8px; text-align: right;">Source File & Location</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>

            <div style="background: rgba(239, 68, 68, 0.15); border: 1px solid #EF4444; border-radius: 6px; padding: 8px; font-size: 0.85rem; color: #FCA5A5;">
                {bottleneck_msg}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


@st.fragment(run_every=0.033)
def render_live_camera_viewport_fragment(camera_mgr) -> None:
    """
    Isolated 30 FPS Video Viewport Fragment.
    Renders the live video feed smoothly on every cycle, guaranteeing
    the image never freezes or sticks on a single frame.
    """
    snapshot = camera_mgr.get_latest_snapshot()
    render_camera_viewport(snapshot, camera_mgr)


@st.fragment(run_every=0.033)
def render_live_telemetry_fragment(camera_mgr) -> None:
    """
    Isolated Telemetry Metrics Fragment.
    Updates telemetry gauges & reticle orientation without re-rendering video columns.
    """
    snapshot = camera_mgr.get_latest_snapshot()
    telemetry = snapshot.telemetry if snapshot else {}
    render_fast_telemetry_panel(telemetry)
    render_head_pose_panel(telemetry)
    render_decision_panel(telemetry)


def render_main_live_grid(camera_mgr) -> None:
    """
    Static Fixed Main Live Grid Layout.
    Columns, headers, and footers are created ONCE on the main thread and NEVER torn down,
    eliminating blinking, flickering, and column re-creation overhead completely.
    """
    snapshot = camera_mgr.get_latest_snapshot()
    telemetry = snapshot.telemetry if snapshot else {}

    col_center, col_right = st.columns([1.8, 1.2], gap="medium")

    with col_center:
        render_camera_panel_header(
            is_live=True,
            has_face=telemetry.get("has_face", True),
            state_str=telemetry.get("drowsiness_state", "ALERT"),
            is_stalled=False
        )
        # Isolated Viewport Fragment
        render_live_camera_viewport_fragment(camera_mgr)

        render_camera_panel_footer(
            fps=telemetry.get("fps", 30.0),
            resolution="1280x720",
            frame_id=getattr(snapshot, "frame_id", telemetry.get("frame_id"))
        )

    with col_right:
        # Isolated Telemetry Fragment
        render_live_telemetry_fragment(camera_mgr)


def render_live_dashboard(camera_mgr) -> None:
    """
    Assembles decoupled multi-rate dashboard layout.
    """
    snapshot = camera_mgr.get_latest_snapshot()
    telemetry = snapshot.telemetry if snapshot else {}

    # 1. Render Top Header Bar
    render_header(telemetry)

    # 2. Render Live Viewport & Telemetry Grid (Ultra-Fast Fragment)
    render_main_live_grid(camera_mgr)

    # 3. Bottom Analytics & Event History (Cached Plotly Refresh)
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
    if len(st.session_state.telemetry_history) > 100:
        st.session_state.telemetry_history = st.session_state.telemetry_history[-100:]

    history_df = pd.DataFrame(st.session_state.telemetry_history)

    render_bottom_analytics(telemetry, camera_connected=telemetry.get("has_face", True))
    render_analytics_dashboard(telemetry, history_df, force_chart_update=False)
    render_live_runtime_instrumentation(snapshot, 0.0, 30.0)



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
