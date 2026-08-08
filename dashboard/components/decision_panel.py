"""
Student Drowsiness Detection System - Explainable AI (XAI) Decision Panel Component

Renders 2D circular score gauge, confidence meter, 4-grid signal matrix, and primary decision explanation box.
Integrates type-safe telemetry formatters to prevent numeric formatting crashes.
"""

import streamlit as st
from typing import Dict, Any
from dashboard.components.gauge_component import render_drowsiness_gauge
from dashboard.components.confidence_bar import render_confidence_bar
from dashboard.components.signal_indicators import render_signal_indicators
from dashboard.components.alert_badge import render_alert_badge
from dashboard.utils.formatters import safe_float, safe_percentage


def render_decision_panel(raw_telemetry: Dict[str, Any]) -> None:
    """
    Renders the Explainable AI (XAI) Decision Engine Panel.
    """
    score = raw_telemetry.get("drowsiness_score", 0.0)
    confidence = raw_telemetry.get("decision_confidence", 98.0)
    state = raw_telemetry.get("drowsiness_state", "ALERT")
    co_occurrences = raw_telemetry.get("co_occurrences", {"EYE": False, "MOUTH": False, "POSE": False})
    reason_str = raw_telemetry.get("decision_reason", "Student alert. All metrics within nominal bounds.")
    has_face = raw_telemetry.get("has_face", True)

    score_val = score if score is not None else 0.0
    conf_val = confidence if confidence is not None else 0.0

    score_str = safe_float(score_val, precision=0, default="0")
    conf_str = safe_percentage(conf_val, precision=0, default="0%")

    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <div style="font-weight: 800; color: #F9FAFB; font-size: 1.0rem;">🧠 AI Decision Engine (XAI)</div>
            <span style="font-size: 0.7rem; color: #9CA3AF; font-weight: 700;">Multi-Modal Evaluator</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_gauge, col_meta = st.columns([1.2, 1.0])

    with col_gauge:
        val = min(100.0, max(0.0, float(score_val)))
        if val < 25:
            bar_color = "#10B981"
        elif val < 50:
            bar_color = "#F59E0B"
        elif val < 75:
            bar_color = "#F97316"
        else:
            bar_color = "#EF4444"

        pct_dash = (val / 100.0) * 251.3
        st.markdown(
            f"""
            <div style="position: relative; width: 120px; height: 120px; margin: 0 auto;">
                <svg width="120" height="120" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="40" stroke="#111827" stroke-width="9" fill="none"/>
                    <circle cx="50" cy="50" r="40" stroke="{bar_color}" stroke-width="9" fill="none"
                            stroke-dasharray="{pct_dash:.1f} 251.3" stroke-dashoffset="0" transform="rotate(-90 50 50)" stroke-linecap="round"/>
                </svg>
                <div style="position: absolute; top: 0; left: 0; width: 120px; height: 120px; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.3rem; font-weight: 800; color: #F9FAFB;">{score_val:.0f}<span style="font-size: 0.8rem; color: #9CA3AF;">/100</span></div>
                    <div style="font-size: 0.6rem; color: #9CA3AF; font-weight: 700; text-transform: uppercase;">RISK SCORE</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_meta:
        st.markdown('<div style="margin-top: 10px;"></div>', unsafe_allow_html=True)
        render_alert_badge(state)
        st.markdown('<div style="margin-top: 14px;"></div>', unsafe_allow_html=True)
        render_confidence_bar(conf_val)

    # 4-Grid Contributing Signal Indicators
    render_signal_indicators(co_occurrences, is_blink_active=False)

    # Primary Decision Explanation Box
    display_reason = reason_str if has_face else "Searching for Face..."
    st.markdown(
        f"""
        <div style="background-color: #111827; border-left: 3px solid #38BDF8; border-radius: 6px; padding: 10px 12px; margin-top: 8px; font-size: 0.8rem; color: #D1D5DB; line-height: 1.4;">
            <strong style="color: #38BDF8;">Primary Reason:</strong> {display_reason}
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)
