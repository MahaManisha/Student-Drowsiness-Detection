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
    is_valid = raw_telemetry.get("head_pose_valid", False)

    # Safe Formatted Degree Strings
    pitch_str = safe_angle(pitch, precision=1, default="N/A")
    yaw_str = safe_angle(yaw, precision=1, default="N/A")
    roll_str = safe_angle(roll, precision=1, default="N/A")

    # Plotly 2D Reticle Compass setup
    p_val = pitch if pitch is not None else 0.0
    y_val = yaw if yaw is not None else 0.0

    fig = go.Figure()
    fig.add_shape(type="circle", x0=-30, y0=-30, x1=30, y1=30, line=dict(color="#374151", width=1.5))
    fig.add_shape(type="line", x0=-30, y0=0, x1=30, y1=0, line=dict(color="#4B5563", width=1, dash="dash"))
    fig.add_shape(type="line", x0=0, y0=-30, x1=0, y1=30, line=dict(color="#4B5563", width=1, dash="dash"))

    reticle_color = "#10B981" if is_valid and (abs(p_val) <= 15 and abs(y_val) <= 15) else "#EF4444"
    fig.add_trace(go.Scatter(
        x=[y_val],
        y=[p_val],
        mode="markers",
        marker=dict(size=12, color=reticle_color, line=dict(width=2, color="#F9FAFB")),
        hoverinfo="text",
        text=f"Pitch: {pitch_str}, Yaw: {yaw_str}"
    ))

    fig.update_layout(
        xaxis=dict(range=[-35, 35], showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(range=[-35, 35], showgrid=False, zeroline=False, showticklabels=False),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        width=140,
        height=140
    )

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
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

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
