"""
Student Drowsiness Detection System - KPI Cards Component

Renders 8 Top Key Performance Indicator (KPI) metric cards for Phase S7/S8 Analytics.
Integrates type-safe telemetry formatters to prevent numeric formatting crashes.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any
from dashboard.utils.formatters import safe_float, safe_int, safe_duration


def render_kpi_cards(raw_telemetry: Dict[str, Any]) -> None:
    """
    Renders 8 Top Key Performance Indicator (KPI) metric cards in a responsive grid.
    """
    stats = raw_telemetry.get("session_stats", {}) if raw_telemetry else {}

    # Extract KPI Values
    duration = stats.get("total_session_time", "00:00:00")
    blinks = raw_telemetry.get("blink_count", stats.get("blink_count", 0))
    yawns = raw_telemetry.get("yawn_count", stats.get("yawn_count", 0))
    highest_score = raw_telemetry.get("drowsiness_score", stats.get("highest_score", 0.0))
    
    # Priority lookup: Read live frame telemetry first, fallback to session stats summary
    avg_ear = raw_telemetry.get("avg_ear") if raw_telemetry.get("avg_ear") is not None else stats.get("average_ear")
    avg_mar = raw_telemetry.get("mar") if raw_telemetry.get("mar") is not None else stats.get("average_mar")
    max_closure = raw_telemetry.get("eye_closed_duration") if raw_telemetry.get("eye_closed_duration") is not None else stats.get("longest_eye_closure")
    
    events = raw_telemetry.get("events", []) if raw_telemetry else []
    alert_count = 0
    for e in events:
        if isinstance(e, dict):
            if e.get("type") in ["ALERT", "DROWSY", "CRITICAL"]:
                alert_count += 1
        elif isinstance(e, str):
            if any(kw in e.upper() for kw in ["ALERT", "DROWSY", "CRITICAL"]):
                alert_count += 1

    # Format Strings
    blinks_str = safe_int(blinks, default="0")
    yawns_str = safe_int(yawns, default="0")
    score_str = safe_float(highest_score, precision=0, default="0")
    avg_ear_str = safe_float(avg_ear, precision=3, default="N/A")
    avg_mar_str = safe_float(avg_mar, precision=3, default="N/A")
    max_closure_str = safe_duration(max_closure, precision=1, default="0.0s")
    alert_str = safe_int(alert_count, default="0")

    # Row 1: Top 4 KPI Cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="dash-card" style="padding: 12px 14px;">
                <div style="font-size: 0.75rem; color: #9CA3AF;">⏱️ Session Duration</div>
                <div class="mono-val" style="font-size: 1.25rem; font-weight: 800; color: #F9FAFB; margin-top: 4px;">{duration}</div>
                <div style="font-size: 0.7rem; color: #10B981; margin-top: 2px;">▲ Active Monitoring</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class="dash-card" style="padding: 12px 14px;">
                <div style="font-size: 0.75rem; color: #9CA3AF;">👁️ Total Blinks</div>
                <div class="mono-val" style="font-size: 1.25rem; font-weight: 800; color: #38BDF8; margin-top: 4px;">{blinks_str}</div>
                <div style="font-size: 0.7rem; color: #9CA3AF; margin-top: 2px;">Ocular Micro-Blinks</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div class="dash-card" style="padding: 12px 14px;">
                <div style="font-size: 0.75rem; color: #9CA3AF;">👄 Yawn Events</div>
                <div class="mono-val" style="font-size: 1.25rem; font-weight: 800; color: #F59E0B; margin-top: 4px;">{yawns_str}</div>
                <div style="font-size: 0.7rem; color: #9CA3AF; margin-top: 2px;">Oral Fatigue Signals</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            f"""
            <div class="dash-card" style="padding: 12px 14px;">
                <div style="font-size: 0.75rem; color: #9CA3AF;">🔥 Peak Risk Score</div>
                <div class="mono-val" style="font-size: 1.25rem; font-weight: 800; color: #EF4444; margin-top: 4px;">{score_str} / 100</div>
                <div style="font-size: 0.7rem; color: #9CA3AF; margin-top: 2px;">Multi-Modal Decision Index</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Row 2: Bottom 4 KPI Cards
    col5, col6, col7, col8 = st.columns(4)

    with col5:
        st.markdown(
            f"""
            <div class="dash-card" style="padding: 12px 14px; margin-top: 8px;">
                <div style="font-size: 0.75rem; color: #9CA3AF;">👁️ Current EAR</div>
                <div class="mono-val" style="font-size: 1.25rem; font-weight: 800; color: #38BDF8; margin-top: 4px;">{avg_ear_str}</div>
                <div style="font-size: 0.7rem; color: #9CA3AF; margin-top: 2px;">Threshold: 0.250</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col6:
        st.markdown(
            f"""
            <div class="dash-card" style="padding: 12px 14px; margin-top: 8px;">
                <div style="font-size: 0.75rem; color: #9CA3AF;">👄 Current MAR</div>
                <div class="mono-val" style="font-size: 1.25rem; font-weight: 800; color: #F59E0B; margin-top: 4px;">{avg_mar_str}</div>
                <div style="font-size: 0.7rem; color: #9CA3AF; margin-top: 2px;">Threshold: 0.600</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col7:
        st.markdown(
            f"""
            <div class="dash-card" style="padding: 12px 14px; margin-top: 8px;">
                <div style="font-size: 0.75rem; color: #9CA3AF;">⏳ Longest Eye Closure</div>
                <div class="mono-val" style="font-size: 1.25rem; font-weight: 800; color: #EF4444; margin-top: 4px;">{max_closure_str}</div>
                <div style="font-size: 0.7rem; color: #9CA3AF; margin-top: 2px;">Continuous Duration</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col8:
        st.markdown(
            f"""
            <div class="dash-card" style="padding: 12px 14px; margin-top: 8px;">
                <div style="font-size: 0.75rem; color: #9CA3AF;">🚨 Active Alarms</div>
                <div class="mono-val" style="font-size: 1.25rem; font-weight: 800; color: #EF4444; margin-top: 4px;">{alert_str}</div>
                <div style="font-size: 0.7rem; color: #9CA3AF; margin-top: 2px;">Alarm Threshold Violations</div>
            </div>
            """,
            unsafe_allow_html=True
        )
