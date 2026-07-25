"""
Student Drowsiness Detection System - Contributing Signals Indicator Component

Renders a 4-grid matrix displaying active vs. inactive contributing AI signals
(Eye Closure, Yawning, Head Pose, Blink Pattern).
"""

import streamlit as st
from typing import Dict, Any, Tuple


def render_signal_indicators(co_occurrences: Dict[str, bool], is_blink_active: bool = False) -> None:
    """
    Renders 4 contributing signal badges for Explainable AI (XAI).
    """
    eye_active = co_occurrences.get("EYE", False)
    mouth_active = co_occurrences.get("MOUTH", False)
    pose_active = co_occurrences.get("POSE", False)
    blink_active = is_blink_active

    def get_style(active: bool) -> Tuple[str, str]:
        if active:
            return "background: rgba(239, 68, 68, 0.2); color: #EF4444; border: 1px solid #EF4444;", "✔"
        else:
            return "background: #111827; color: #4B5563; border: 1px solid #374151;", "✖"

    eye_style, eye_icon = get_style(eye_active)
    mouth_style, mouth_icon = get_style(mouth_active)
    pose_style, pose_icon = get_style(pose_active)
    blink_style, blink_icon = get_style(blink_active)

    st.markdown(
        f"""
        <div style="margin-bottom: 12px;">
            <div style="font-size: 0.75rem; color: #9CA3AF; margin-bottom: 6px; font-weight: 600;">CONTRIBUTING AI SIGNALS</div>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px;">
                <div style="{eye_style} padding: 6px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; display: flex; align-items: center; justify-content: space-between;">
                    <span>👁️ Eye Closure</span>
                    <span>{eye_icon}</span>
                </div>
                <div style="{mouth_style} padding: 6px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; display: flex; align-items: center; justify-content: space-between;">
                    <span>👄 Yawning</span>
                    <span>{mouth_icon}</span>
                </div>
                <div style="{pose_style} padding: 6px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; display: flex; align-items: center; justify-content: space-between;">
                    <span>📐 Head Pose</span>
                    <span>{pose_icon}</span>
                </div>
                <div style="{blink_style} padding: 6px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; display: flex; align-items: center; justify-content: space-between;">
                    <span>⚡ Blink Rate</span>
                    <span>{blink_icon}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
