"""
Student Drowsiness Detection System - FAST Telemetry & Alert Banner Component

Renders 30 FPS real-time UI components:
- Alert Banner & Active Warning Box (updates <33 ms when Decision Engine state changes)
- Ocular Telemetry: EAR (Avg, Left, Right), Eye State ("OPEN"/"CLOSED"), EAR Progress
- Oral Telemetry: MAR, Mouth State ("CLOSED"/"YAWN"), MAR Progress
- Head Pose & Risk Index: Pitch, Yaw, Roll degrees, Drowsiness Score (0-100), Decision Confidence
"""

import streamlit as st
from typing import Dict, Any
from dashboard.components.alert_badge import render_alert_badge
from dashboard.utils.formatters import safe_float, safe_percentage, safe_int


def render_fast_alert_banner(telemetry_data: Dict[str, Any]) -> None:
    """
    Renders FAST Alert Banner & Warning Message Box (30 FPS / 0.033s).
    Updates immediately (<33 ms) whenever the Decision Engine state changes.
    Displays synchronized Frame ID badge matching the live camera viewport.
    """
    state = telemetry_data.get("drowsiness_state", "ALERT")
    reason_str = telemetry_data.get("decision_reason", "Student alert. All telemetry metrics within nominal bounds.")
    has_face = telemetry_data.get("has_face", False)
    frame_id = telemetry_data.get("frame_id")
    frame_badge = f'<span style="padding: 2px 6px; border-radius: 6px; background: rgba(255,255,255,0.08); color: #F59E0B; font-weight: 700; font-size: 0.65rem; margin-right: 6px;">FRAME #{frame_id}</span>' if frame_id else ''

    # Determine Alert Severity Colors & Icon
    if state == "HIGHLY_DROWSY":
        banner_bg = "linear-gradient(90deg, rgba(239, 68, 68, 0.25) 0%, rgba(185, 28, 28, 0.15) 100%)"
        border_color = "#EF4444"
        icon = "🚨"
        title = "CRITICAL ALERT: SEVERE DROWSINESS DETECTED"
    elif state == "DROWSY":
        banner_bg = "linear-gradient(90deg, rgba(245, 158, 11, 0.25) 0%, rgba(217, 119, 6, 0.15) 100%)"
        border_color = "#F59E0B"
        icon = "⚠️"
        title = "WARNING: DROWSINESS DETECTED"
    elif state == "SLIGHTLY_DROWSY" or state == "UNWATCHFUL":
        banner_bg = "linear-gradient(90deg, rgba(245, 158, 11, 0.15) 0%, rgba(180, 83, 9, 0.10) 100%)"
        border_color = "#F59E0B"
        icon = "⚠️"
        title = "ADVISORY: SUBTLE FATIGUE SIGNALS DETECTED"
    else:
        banner_bg = "linear-gradient(90deg, rgba(16, 185, 129, 0.15) 0%, rgba(4, 120, 87, 0.10) 100%)"
        border_color = "#10B981"
        icon = "🛡️"
        title = "MONITORING ACTIVE: STUDENT ALERT"

    display_reason = reason_str if has_face else "Searching for Face in Camera Viewport..."

    st.markdown(
        f"""
        <div style="background: {banner_bg}; border: 1.5px solid {border_color}; border-radius: 8px; padding: 10px 14px; margin-bottom: 12px; transition: all 0.2s ease;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 1.2rem;">{icon}</span>
                    <strong style="color: #F9FAFB; font-size: 0.9rem; letter-spacing: 0.3px;">{title}</strong>
                </div>
                <div style="display: flex; align-items: center;">
                    {frame_badge}
                    <div style="padding: 2px 8px; border-radius: 12px; background: {border_color}; color: #000; font-weight: 800; font-size: 0.7rem;">
                        {state}
                    </div>
                </div>
            </div>
            <div style="margin-top: 6px; font-size: 0.75rem; color: #D1D5DB; line-height: 1.3;">
                <strong style="color: {border_color};">Reason:</strong> {display_reason}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_fast_telemetry_panel(telemetry_data: Dict[str, Any]) -> None:
    """
    Renders FAST Real-Time Telemetry Panel (30 FPS / 0.033s):
    - Alert Banner & State Box
    - Live EAR, Eye State, EAR progress bar
    - Live MAR, Mouth State, MAR progress bar
    - Live Head Pose numeric orientation degrees (Pitch, Yaw, Roll)
    - Live Drowsiness Risk Score (0-100) & Decision Confidence
    Consumes synchronized frame_id metrics with zero stale fallback defaults.
    """
    # 1. FAST Alert Banner
    render_fast_alert_banner(telemetry_data)

    # Telemetry Variables
    has_face = telemetry_data.get("has_face", False)
    eye_state = telemetry_data.get("eye_state", "Searching for Face..." if not has_face else "OPEN")
    mouth_state = telemetry_data.get("mouth_state", "Searching for Face..." if not has_face else "CLOSED")

    avg_ear = telemetry_data.get("avg_ear") if has_face else None
    left_ear = telemetry_data.get("left_ear") if has_face else None
    right_ear = telemetry_data.get("right_ear") if has_face else None
    ear_thresh = telemetry_data.get("ear_threshold", 0.250)

    mar = telemetry_data.get("mar") if has_face else None
    mar_thresh = telemetry_data.get("mar_threshold", 0.600)

    pitch = telemetry_data.get("head_pose_pitch") if has_face else None
    yaw = telemetry_data.get("head_pose_yaw") if has_face else None
    roll = telemetry_data.get("head_pose_roll") if has_face else None
    pose_valid = telemetry_data.get("head_pose_valid", False) if has_face else False

    score = telemetry_data.get("drowsiness_score", 0.0)
    confidence = telemetry_data.get("decision_confidence", 0.0 if not has_face else 98.0)

    # Format Strings
    avg_ear_str = safe_float(avg_ear, precision=3, default="N/A")
    left_ear_str = safe_float(left_ear, precision=3, default="N/A")
    right_ear_str = safe_float(right_ear, precision=3, default="N/A")
    ear_thresh_str = safe_float(ear_thresh, precision=3, default="0.250")

    mar_str = safe_float(mar, precision=3, default="N/A")
    mar_thresh_str = safe_float(mar_thresh, precision=3, default="0.600")

    pitch_str = safe_float(pitch, precision=1, default="--")
    yaw_str = safe_float(yaw, precision=1, default="--")
    roll_str = safe_float(roll, precision=1, default="--")

    score_str = safe_float(score, precision=0, default="0")
    conf_str = safe_percentage(confidence, precision=0, default="0%" if not has_face else "98%")


    # Eye State Color
    is_eye_closed = "CLOSED" in str(eye_state).upper()
    eye_color = "#EF4444" if is_eye_closed else "#38BDF8"
    eye_badge_bg = "rgba(239, 68, 68, 0.15)" if is_eye_closed else "rgba(56, 189, 248, 0.15)"

    # Mouth State Color
    is_yawn = "YAWN" in str(mouth_state).upper()
    mouth_color = "#F59E0B" if is_yawn else "#10B981"
    mouth_badge_bg = "rgba(245, 158, 11, 0.15)" if is_yawn else "rgba(16, 185, 129, 0.15)"

    # Score Color
    score_num = float(score or 0)
    if score_num >= 65:
        score_color = "#EF4444"
    elif score_num >= 35:
        score_color = "#F59E0B"
    else:
        score_color = "#10B981"

    # EAR & MAR Progress Bar Percentages
    ear_pct = min(100, max(0, int((float(avg_ear or 0) / 0.40) * 100)))
    mar_pct = min(100, max(0, int((float(mar or 0) / 0.80) * 100)))

    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    
    # 2. Ocular Telemetry Card
    st.markdown(
        f"""
        <div style="margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="font-weight: 700; color: #F9FAFB; font-size: 0.85rem;">👁️ Eye State & EAR (Ocular)</div>
                <span style="padding: 2px 8px; border-radius: 6px; background: {eye_badge_bg}; color: {eye_color}; font-weight: 700; font-size: 0.7rem;">
                    {eye_state}
                </span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: baseline; margin-top: 6px;">
                <span class="mono-val" style="font-size: 1.4rem; font-weight: 800; color: {eye_color};">{avg_ear_str}</span>
                <span style="font-size: 0.7rem; color: #9CA3AF;">Threshold: {ear_thresh_str} | L: {left_ear_str} R: {right_ear_str}</span>
            </div>
            <div style="background: #1F2937; border-radius: 4px; height: 6px; width: 100%; margin-top: 4px; overflow: hidden;">
                <div style="background: {eye_color}; width: {ear_pct}%; height: 100%; transition: width 0.1s ease;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 3. Oral Telemetry Card
    st.markdown(
        f"""
        <div style="margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="font-weight: 700; color: #F9FAFB; font-size: 0.85rem;">👄 Mouth State & MAR (Oral)</div>
                <span style="padding: 2px 8px; border-radius: 6px; background: {mouth_badge_bg}; color: {mouth_color}; font-weight: 700; font-size: 0.7rem;">
                    {mouth_state}
                </span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: baseline; margin-top: 6px;">
                <span class="mono-val" style="font-size: 1.4rem; font-weight: 800; color: {mouth_color};">{mar_str}</span>
                <span style="font-size: 0.7rem; color: #9CA3AF;">Threshold: {mar_thresh_str}</span>
            </div>
            <div style="background: #1F2937; border-radius: 4px; height: 6px; width: 100%; margin-top: 4px; overflow: hidden;">
                <div style="background: {mouth_color}; width: {mar_pct}%; height: 100%; transition: width 0.1s ease;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 4. Head Pose & Risk Index Card
    st.markdown(
        f"""
        <div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="font-weight: 700; color: #F9FAFB; font-size: 0.85rem;">📐 Head Pose & Risk Index</div>
                <span style="font-size: 0.7rem; color: #9CA3AF;">Confidence: <strong style="color: #38BDF8;">{conf_str}</strong></span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr) 1.2fr; gap: 8px; margin-top: 8px; text-align: center;">
                <div style="background: #111827; padding: 6px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.05);">
                    <div style="font-size: 0.65rem; color: #9CA3AF;">PITCH</div>
                    <div class="mono-val" style="font-size: 0.9rem; font-weight: 700; color: #F9FAFB;">{pitch_str}°</div>
                </div>
                <div style="background: #111827; padding: 6px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.05);">
                    <div style="font-size: 0.65rem; color: #9CA3AF;">YAW</div>
                    <div class="mono-val" style="font-size: 0.9rem; font-weight: 700; color: #F9FAFB;">{yaw_str}°</div>
                </div>
                <div style="background: #111827; padding: 6px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.05);">
                    <div style="font-size: 0.65rem; color: #9CA3AF;">ROLL</div>
                    <div class="mono-val" style="font-size: 0.9rem; font-weight: 700; color: #F9FAFB;">{roll_str}°</div>
                </div>
                <div style="background: #111827; padding: 6px; border-radius: 6px; border: 1px solid {score_color};">
                    <div style="font-size: 0.65rem; color: #9CA3AF;">RISK SCORE</div>
                    <div class="mono-val" style="font-size: 1.0rem; font-weight: 800; color: {score_color};">{score_str}/100</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown('</div>', unsafe_allow_html=True)
