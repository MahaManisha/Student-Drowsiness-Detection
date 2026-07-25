"""
Student Drowsiness Detection System - Dashboard Header Component

Renders the top application header bar containing title badge, session timer,
FPS throughput counter, and alert status pill.
Integrates type-safe telemetry formatters to prevent numeric formatting crashes.
"""

import streamlit as st
from typing import Dict, Any
from dashboard.components.alert_badge import render_alert_badge
from dashboard.utils.formatters import safe_float


def render_header(telemetry_data: Dict[str, Any]) -> None:
    """
    Renders top application header bar.
    """
    session_time = telemetry_data.get("session_time_str", "00:00:00")
    fps_val = telemetry_data.get("fps", 30.0)
    drowsiness_state = telemetry_data.get("drowsiness_state", "ALERT")

    fps_str = safe_float(fps_val, precision=1, default="30.0")

    col_title, col_status = st.columns([2.2, 1.0])

    with col_title:
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 1.8rem;">🛡️</span>
                <div>
                    <h2 style="margin: 0; padding: 0; color: #F9FAFB; font-weight: 800; font-size: 1.5rem;">
                        Student Drowsiness Detection Platform
                    </h2>
                    <p style="margin: 0; padding: 0; color: #9CA3AF; font-size: 0.8rem;">
                        Real-Time Computer Vision & Multi-Modal Safety Analytics
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_status:
        st.markdown(
            f"""
            <div style="display: flex; justify-content: flex-end; align-items: center; gap: 16px; margin-top: 4px;">
                <div style="text-align: right;">
                    <div style="font-size: 0.7rem; color: #9CA3AF;">SESSION DURATION</div>
                    <div class="mono-val" style="font-size: 0.95rem; color: #F9FAFB; font-weight: 700;">⏱️ {session_time}</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 0.7rem; color: #9CA3AF;">FRAME RATE</div>
                    <div class="mono-val" style="font-size: 0.95rem; color: #10B981; font-weight: 700;">⚡ {fps_str} FPS</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div style="margin-bottom: 10px;"></div>', unsafe_allow_html=True)
