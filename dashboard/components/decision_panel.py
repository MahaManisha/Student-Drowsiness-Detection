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
        fig_gauge = render_drowsiness_gauge(score_val)
        st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})

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
