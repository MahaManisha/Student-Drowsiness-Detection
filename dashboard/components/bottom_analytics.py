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


def _format_seconds(seconds: Any) -> str:
    if seconds is None:
        return "00:00:00"
    try:
        secs = int(float(seconds))
        hrs = secs // 3600
        mins = (secs % 3600) // 60
        secs = secs % 60
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    except Exception:
        return "00:00:00"


def _render_metric_box(icon: str, label: str, value: str) -> str:
    return (
        f'<div style="background: #111827; padding: 10px 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08); margin-bottom: 8px;">'
        f'<div style="font-size: 0.8rem; font-weight: 700; color: #CBD5E1; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">'
        f'<span>{icon}</span> <span>{label}</span>'
        f'</div>'
        f'<div class="mono-val" style="font-size: 1.3rem; font-weight: 800; color: #FFFFFF; letter-spacing: -0.5px;">{value}</div>'
        f'</div>'
    )


def render_bottom_analytics(raw_telemetry: Dict[str, Any], camera_connected: bool = True) -> None:
    """
    Renders Bottom Analytics section inside Streamlit layout.
    """
    telemetry = TelemetryProvider.process_payload(raw_telemetry)

    stats = telemetry.get("session_stats", {})
    events = telemetry.get("events", [])

    total_session_sec = stats.get("total_session_time", 0.0)
    state_times = stats.get("time_spent_in_states", {})
    alert_sec = state_times.get("ALERT", 0.0)
    drowsy_sec = state_times.get("DROWSY", 0.0) + state_times.get("SLIGHTLY_DROWSY", 0.0) + state_times.get("HIGHLY_DROWSY", 0.0)

    session_dur_str = _format_seconds(total_session_sec)
    time_in_alert_str = _format_seconds(alert_sec)
    time_in_drowsy_str = _format_seconds(drowsy_sec)

    avg_ear_val = f"{stats.get('average_ear', 0.0):.3f}" if stats.get('average_ear') is not None else "N/A"
    avg_mar_val = f"{stats.get('average_mar', 0.0):.3f}" if stats.get('average_mar') is not None else "N/A"
    longest_closure_val = f"{stats.get('longest_eye_closure', 0.0):.2f}s" if stats.get('longest_eye_closure') is not None else "N/A"
    highest_score_val = f"{stats.get('highest_score', 0.0):.0f} / 100" if stats.get('highest_score') is not None else "N/A"

    col_stats, col_alerts = st.columns([1.5, 1.1], gap="medium")

    with col_stats:
        # 1. 9 Session Statistics Summary Cards with High-Contrast Bright Styling
        b1 = _render_metric_box("⏱️", "Session Duration", session_dur_str)
        b2 = _render_metric_box("👁️", "Blink Count", f"{stats.get('blink_count', 0)} blinks")
        b3 = _render_metric_box("👄", "Yawn Count", f"{stats.get('yawn_count', 0)} yawns")

        b4 = _render_metric_box("📊", "Average EAR", avg_ear_val)
        b5 = _render_metric_box("📏", "Average MAR", avg_mar_val)
        b6 = _render_metric_box("🔥", "Highest Score", highest_score_val)

        b7 = _render_metric_box("⏳", "Longest Closure", longest_closure_val)
        b8 = _render_metric_box("🛡️", "Time in ALERT", time_in_alert_str)
        b9 = _render_metric_box("⚠️", "Time in DROWSY", time_in_drowsy_str)

        card_html = (
            f'<div class="dash-card">'
            f'<div style="font-weight: 800; color: #F9FAFB; font-size: 0.95rem; margin-bottom: 12px;">📈 Session Statistics Summary</div>'
            f'<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;">'
            f'{b1}{b2}{b3}{b4}{b5}{b6}{b7}{b8}{b9}'
            f'</div>'
            f'</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)

        # 2. System Diagnostics & Health Panel
        render_system_health(raw_telemetry, camera_connected=camera_connected)

    with col_alerts:
        # 3. Main Real-Time Alert Center Banner
        render_alert_center(raw_telemetry)

        # 4. Scrollable Alert Event Stream (Newest First)
        render_alert_history(events)
