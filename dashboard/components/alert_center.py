"""
Student Drowsiness Detection System - Real-Time Alert Center Component

Renders prominent alert notifications, audio status indicators, active warning banners,
and chronological event logging.
Integrates safe telemetry formatting utilities to prevent TypeError exceptions.
"""

import time
import streamlit as st
from typing import Dict, Any
from dashboard.components.alert_badge import get_alert_badge_style
from dashboard.utils.formatters import safe_duration


def render_alert_center(raw_telemetry: Dict[str, Any]) -> None:
    """
    Renders the active Alert Center status banner and controls.
    """
    state = raw_telemetry.get("drowsiness_state", "ALERT")
    current_msg = raw_telemetry.get("current_message", "System operating normally.")
    severity = raw_telemetry.get("current_severity", "subtle")
    alert_time = raw_telemetry.get("last_alert_time", time.strftime("%H:%M:%S", time.localtime()))
    closed_duration = raw_telemetry.get("eye_closed_duration")
    audio_enabled = raw_telemetry.get("audio_enabled", True)
    audio_status = raw_telemetry.get("audio_status", "READY")

    # Safe formatted closed duration string
    closed_dur_str = safe_duration(closed_duration, precision=1, default="0.0s")

    # Audio Status Display Only (🔊 Alarm Active / 🔇 Alarm Muted)
    if audio_enabled and audio_status != "DISABLED":
        audio_html = '<span style="color: #10B981; font-weight: 700; font-size: 0.75rem;">🔊 Alarm Active</span>'
    else:
        audio_html = '<span style="color: #6B7280; font-weight: 700; font-size: 0.75rem;">🔇 Alarm Muted</span>'

    pill_class, label_str, _ = get_alert_badge_style(state)

    # Determine Banner Border Color based on Severity
    if state == "ALERT":
        border_color = "#10B981"
    elif state == "SLIGHTLY_DROWSY":
        border_color = "#F59E0B"
    elif state == "DROWSY":
        border_color = "#F97316"
    else:
        border_color = "#EF4444"

    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <div style="font-weight: 800; color: #F9FAFB; font-size: 1.0rem;">🚨 Real-Time Alert Center</div>
            <div style="display: flex; gap: 8px; align-items: center;">
                {audio_html}
                <span class="status-pill {pill_class}" style="font-size: 0.7rem; padding: 3px 8px;">{label_str}</span>
            </div>
        </div>

        <div style="background-color: #111827; border-left: 4px solid {border_color}; border-radius: 8px; padding: 12px 14px; margin-bottom: 10px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.4);">
            <div style="display: flex; justify-content: space-between; font-size: 0.7rem; color: #9CA3AF; margin-bottom: 4px;">
                <span>ACTIVE WARNING BANNER</span>
                <span class="mono-val">Timestamp: {alert_time}</span>
            </div>
            <div style="font-size: 0.9rem; font-weight: 700; color: #F9FAFB; margin-bottom: 4px;">
                {current_msg}
            </div>
            <div style="font-size: 0.75rem; color: #9CA3AF;">
                Alert Duration: <strong class="mono-val" style="color: #F9FAFB;">{closed_dur_str}</strong> | Severity: <strong style="color: {border_color}; text-transform: uppercase;">{severity}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)
