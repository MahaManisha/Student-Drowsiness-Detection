"""
Student Drowsiness Detection System - Head Pose Panel Component

Renders 3D Head Pose Reticle Compass & Degree Metrics (Pitch, Yaw, Roll).
Integrates type-safe telemetry formatters to prevent numeric formatting crashes.
"""

import streamlit as st
import plotly.graph_objects as go
from typing import Dict, Any
from dashboard.utils.formatters import safe_angle


def render_head_pose_panel(raw_telemetry: Dict[str, Any]) -> None:
    """
    Renders 3D Head Pose Orientational Reticle & Pitch/Yaw/Roll metrics.
    """
    pitch = raw_telemetry.get("head_pose_pitch")
    yaw = raw_telemetry.get("head_pose_yaw")
    roll = raw_telemetry.get("head_pose_roll")
    raw_valid = raw_telemetry.get("head_pose_valid", False)
    is_valid = bool(raw_valid or raw_telemetry.get("has_face", False) or pitch is not None)

    # Safe Formatted Degree Strings
    pitch_str = safe_angle(pitch, precision=1, default="N/A")
    yaw_str = safe_angle(yaw, precision=1, default="N/A")
    roll_str = safe_angle(roll, precision=1, default="N/A")

    # Ultra-Fast High-Performance Inline SVG Reticle Compass (0ms serialization, zero browser freezes)
    p_val = pitch if pitch is not None else 0.0
    y_val = yaw if yaw is not None else 0.0

    reticle_color = "#10B981" if is_valid and (abs(p_val) <= 15 and abs(y_val) <= 15) else "#EF4444"
    cx = 50 + int(max(-35.0, min(35.0, y_val)) / 35.0 * 35.0)
    cy = 50 - int(max(-35.0, min(35.0, p_val)) / 35.0 * 35.0)

    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div style="font-weight: 800; color: #F9FAFB; font-size: 0.95rem;">📐 Head Pose Orientation</div>
            <span style="font-size: 0.75rem; color: {'#10B981' if is_valid else '#6B7280'}; font-weight: 700;">
                ● {'MESH LATCHED' if is_valid else 'SEARCHING...'}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_compass, col_metrics = st.columns([1, 1])

    with col_compass:
        st.markdown(
            f"""
            <div style="text-align: center; padding: 4px 0;">
                <svg width="120" height="120" viewBox="0 0 100 100" style="background: transparent;">
                    <circle cx="50" cy="50" r="40" stroke="rgba(255,255,255,0.12)" stroke-width="1.5" fill="none"/>
                    <line x1="10" y1="50" x2="90" y2="50" stroke="rgba(255,255,255,0.2)" stroke-width="1" stroke-dasharray="3,3"/>
                    <line x1="50" y1="10" x2="50" y2="90" stroke="rgba(255,255,255,0.2)" stroke-width="1" stroke-dasharray="3,3"/>
                    <circle cx="{cx}" cy="{cy}" r="6" fill="{reticle_color}" stroke="#F9FAFB" stroke-width="2"/>
                </svg>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_metrics:
        st.markdown(
            f"""
            <div style="display: flex; flex-direction: column; gap: 6px; font-size: 0.8rem; margin-top: 10px;">
                <div style="display: flex; justify-content: space-between; background: #111827; padding: 4px 8px; border-radius: 4px;">
                    <span style="color: #9CA3AF;">Pitch:</span>
                    <strong class="mono-val" style="color: #F9FAFB;">{pitch_str}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; background: #111827; padding: 4px 8px; border-radius: 4px;">
                    <span style="color: #9CA3AF;">Yaw:</span>
                    <strong class="mono-val" style="color: #F9FAFB;">{yaw_str}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; background: #111827; padding: 4px 8px; border-radius: 4px;">
                    <span style="color: #9CA3AF;">Roll:</span>
                    <strong class="mono-val" style="color: #F9FAFB;">{roll_str}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown('</div>', unsafe_allow_html=True)
