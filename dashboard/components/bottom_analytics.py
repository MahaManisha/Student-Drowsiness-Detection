"""
Student Drowsiness Detection System - Bottom Analytics Component

Renders the bottom section containing Session Statistics, Alert Center, Alert History Stream,
and System Diagnostics Health.
"""

import streamlit as st
from typing import Dict, Any
from dashboard.utils.telemetry_provider import TelemetryProvider
from dashboard.components.alert_center import render_alert_center
from dashboard.components.alert_history import render_alert_history
from dashboard.components.system_health import render_system_health


def render_bottom_analytics(raw_telemetry: Dict[str, Any], camera_connected: bool = True) -> None:
    """
    Renders Bottom Analytics section inside Streamlit layout.
    """
    telemetry = TelemetryProvider.process_payload(raw_telemetry)

    stats = telemetry.get("session_stats", {})
    events = telemetry.get("events", [])

    col_stats, col_alerts = st.columns([1.5, 1.1], gap="medium")

    with col_stats:
        # 1. 9 Session Statistics Summary Cards
        st.markdown('<div class="dash-card">', unsafe_allow_html=True)
        st.markdown('<div style="font-weight: 700; color: #F9FAFB; font-size: 0.95rem; margin-bottom: 12px;">📈 Session Statistics Summary</div>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric(label="⏱️ Session Duration", value=stats.get("total_session_time", "00:00:00"))
            st.metric(label="📊 Average EAR", value=f"{stats.get('average_ear', 0.0):.3f}" if stats.get('average_ear') is not None else "N/A")
            st.metric(label="⏳ Longest Closure", value=f"{stats.get('longest_eye_closure', 0.0):.2f}s" if stats.get('longest_eye_closure') is not None else "N/A")

        with c2:
            st.metric(label="👁️ Blink Count", value=f"{stats.get('blink_count', 0)} blinks")
            st.metric(label="📏 Average MAR", value=f"{stats.get('average_mar', 0.0):.3f}" if stats.get('average_mar') is not None else "N/A")
            st.metric(label="🛡️ Time in ALERT", value=stats.get("time_in_alert", "00:00:00"))

        with c3:
            st.metric(label="👄 Yawn Count", value=f"{stats.get('yawn_count', 0)} yawns")
            st.metric(label="🔥 Highest Score", value=f"{stats.get('highest_score', 0.0):.0f} / 100" if stats.get('highest_score') is not None else "N/A")
            st.metric(label="⚠️ Time in DROWSY", value=stats.get("time_in_drowsy", "00:00:00"))

        st.markdown('</div>', unsafe_allow_html=True)

        # 2. System Diagnostics & Health Panel
        render_system_health(raw_telemetry, camera_connected=camera_connected)

    with col_alerts:
        # 3. Main Real-Time Alert Center Banner
        render_alert_center(raw_telemetry)

        # 4. Scrollable Alert Event Stream (Newest First)
        render_alert_history(events)
