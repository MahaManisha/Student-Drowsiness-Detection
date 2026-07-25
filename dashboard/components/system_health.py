"""
Student Drowsiness Detection System - System Health Component

Renders 4 diagnostic system health status indicators with green/red status indicators:
  - Camera Connected
  - AI Running
  - Decision Engine Active
  - Telemetry Updating
"""

import streamlit as st
from typing import Dict, Any


def render_system_health(raw_telemetry: Dict[str, Any], camera_connected: bool = True) -> None:
    """
    Renders 4-item System Health diagnostic panel.
    """
    fps = raw_telemetry.get("fps", 0.0)
    ai_running = camera_connected and (fps > 0.0)
    decision_active = ai_running and ("drowsiness_score" in raw_telemetry)
    telemetry_updating = ai_running and (fps >= 10.0)

    def get_indicator(status: bool, active_txt: str, inactive_txt: str) -> str:
        if status:
            return f'<span style="color: #10B981; font-weight: 700;">● {active_txt}</span>'
        else:
            return f'<span style="color: #EF4444; font-weight: 700;">● {inactive_txt}</span>'

    cam_str = get_indicator(camera_connected, "Connected", "Disconnected")
    ai_str = get_indicator(ai_running, "Active", "Inactive")
    dec_str = get_indicator(decision_active, "Evaluating", "Idle")
    tel_str = get_indicator(telemetry_updating, f"{fps:.1f} FPS", "Stalled")

    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="font-weight: 700; color: #F9FAFB; font-size: 0.95rem; margin-bottom: 8px;">⚙️ System Diagnostics & Health</div>
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; font-size: 0.75rem; background: #111827; padding: 10px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.06);">
            <div><span style="color: #9CA3AF;">Camera Feed:</span> {cam_str}</div>
            <div><span style="color: #9CA3AF;">AI Engine:</span> {ai_str}</div>
            <div><span style="color: #9CA3AF;">Decision Engine:</span> {dec_str}</div>
            <div><span style="color: #9CA3AF;">Telemetry Pipeline:</span> {tel_str}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)
