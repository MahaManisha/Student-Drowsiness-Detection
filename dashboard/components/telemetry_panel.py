"""
Student Drowsiness Detection System - Telemetry Panel Component

Renders live Eye Analysis (EAR, Eye State, Blinks) and Mouth Analysis (MAR, Mouth State, Yawns) cards.
Integrates type-safe telemetry formatters to prevent formatting crashes.
"""

import streamlit as st
from typing import Dict, Any
from dashboard.utils.formatters import safe_float, safe_int, safe_duration


def render_telemetry_panel(raw_telemetry: Dict[str, Any]) -> None:
    """
    Renders the Eye Analysis and Mouth Analysis telemetry status cards.
    """
    # 1. Extract & Format Ocular Metrics safely
    left_ear = raw_telemetry.get("left_ear")
    right_ear = raw_telemetry.get("right_ear")
    avg_ear = raw_telemetry.get("avg_ear")
    ear_thresh = raw_telemetry.get("ear_threshold", 0.25)
    eye_state = raw_telemetry.get("eye_state", "Searching for Face...")
    blink_count = raw_telemetry.get("blink_count", 0)
    eye_closed_dur = raw_telemetry.get("eye_closed_duration")

    # Safe Formatted Strings
    l_ear_str = safe_float(left_ear, precision=3, default="N/A")
    r_ear_str = safe_float(right_ear, precision=3, default="N/A")
    avg_ear_str = safe_float(avg_ear, precision=3, default="N/A")
    blink_str = safe_int(blink_count, default="0")
    closed_dur_str = safe_duration(eye_closed_dur, precision=1, default="0.0s")

    # EAR progress bar fill calculation
    ear_val_num = avg_ear if avg_ear is not None else 0.0
    ear_fill_pct = min(max(int((ear_val_num / 0.40) * 100), 0), 100)
    ear_bar_color = "#10B981" if ear_val_num >= ear_thresh else "#EF4444"

    # 2. Extract & Format Oral Metrics safely
    mar_val = raw_telemetry.get("mar")
    mar_thresh = raw_telemetry.get("mar_threshold", 0.60)
    mouth_state = raw_telemetry.get("mouth_state", "Searching for Face...")
    yawn_count = raw_telemetry.get("yawn_count", 0)
    mouth_open_dur = raw_telemetry.get("mouth_open_duration")

    # Safe Formatted Strings
    mar_str = safe_float(mar_val, precision=3, default="N/A")
    yawn_str = safe_int(yawn_count, default="0")
    open_dur_str = safe_duration(mouth_open_dur, precision=1, default="0.0s")

    # MAR progress bar fill calculation
    mar_val_num = mar_val if mar_val is not None else 0.0
    mar_fill_pct = min(max(int((mar_val_num / 0.80) * 100), 0), 100)
    mar_bar_color = "#EF4444" if mar_val_num >= mar_thresh else "#10B981"

    # Render Eye Analysis Card
    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div style="font-weight: 800; color: #F9FAFB; font-size: 0.95rem;">👁️ Eye Analysis</div>
            <span style="font-size: 0.75rem; color: {'#10B981' if 'OPEN' in str(eye_state).upper() else '#EF4444'}; font-weight: 700;">
                ● {eye_state}
            </span>
        </div>

        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px;">
            <span style="font-size: 0.8rem; color: #9CA3AF;">Average EAR:</span>
            <span class="mono-val" style="font-size: 1.2rem; font-weight: 800; color: {ear_bar_color};">{avg_ear_str}</span>
        </div>

        <!-- Custom Progress Bar -->
        <div style="width: 100%; background: #111827; height: 8px; border-radius: 4px; overflow: hidden; margin-bottom: 8px; position: relative;">
            <div style="width: {ear_fill_pct}%; background: {ear_bar_color}; height: 100%; transition: width 0.2s ease;"></div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; font-size: 0.75rem; color: #9CA3AF; background: #111827; padding: 6px 8px; border-radius: 6px;">
            <div>Left: <strong class="mono-val" style="color: #F9FAFB;">{l_ear_str}</strong></div>
            <div>Right: <strong class="mono-val" style="color: #F9FAFB;">{r_ear_str}</strong></div>
            <div>Thresh: <strong class="mono-val" style="color: #F59E0B;">{ear_thresh:.2f}</strong></div>
        </div>

        <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #9CA3AF; margin-top: 8px;">
            <span>Blinks: <strong class="mono-val" style="color: #38BDF8;">{blink_str}</strong></span>
            <span>Closed Time: <strong class="mono-val" style="color: #F9FAFB;">{closed_dur_str}</strong></span>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # Render Mouth Analysis Card
    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div style="font-weight: 800; color: #F9FAFB; font-size: 0.95rem;">👄 Mouth Analysis</div>
            <span style="font-size: 0.75rem; color: {'#EF4444' if 'YAWN' in str(mouth_state).upper() else '#10B981'}; font-weight: 700;">
                ● {mouth_state}
            </span>
        </div>

        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px;">
            <span style="font-size: 0.8rem; color: #9CA3AF;">Current MAR:</span>
            <span class="mono-val" style="font-size: 1.2rem; font-weight: 800; color: {mar_bar_color};">{mar_str}</span>
        </div>

        <!-- Custom Progress Bar -->
        <div style="width: 100%; background: #111827; height: 8px; border-radius: 4px; overflow: hidden; margin-bottom: 8px;">
            <div style="width: {mar_fill_pct}%; background: {mar_bar_color}; height: 100%; transition: width 0.2s ease;"></div>
        </div>

        <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #9CA3AF; background: #111827; padding: 6px 8px; border-radius: 6px;">
            <span>MAR Threshold: <strong class="mono-val" style="color: #F59E0B;">{mar_thresh:.2f}</strong></span>
            <span>State: <strong style="color: #F9FAFB;">{mouth_state}</strong></span>
        </div>

        <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #9CA3AF; margin-top: 8px;">
            <span>Yawns: <strong class="mono-val" style="color: #EC4899;">{yawn_str}</strong></span>
            <span>Open Time: <strong class="mono-val" style="color: #F9FAFB;">{open_dur_str}</strong></span>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)
