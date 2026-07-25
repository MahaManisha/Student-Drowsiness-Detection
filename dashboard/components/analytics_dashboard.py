"""
Student Drowsiness Detection System - Comprehensive Session Analytics Dashboard Container

Master layout container combining 8 KPI metric cards, 5 Plotly interactive charts,
and Session Summary metadata panel.
Phase O1 Optimization: Implements session-state figure caching and unique container keys to decouple
Plotly serialization from the live 30 FPS webcam rendering loop.
"""

import time
import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional
from dashboard.components.kpi_cards import render_kpi_cards
from dashboard.components.charts import (
    render_ear_trend_chart,
    render_mar_trend_chart,
    render_score_trend_chart,
    render_blink_frequency_chart,
    render_alert_distribution_chart,
)
from dashboard.components.session_summary import render_session_summary


def render_analytics_dashboard(
    raw_telemetry: Dict[str, Any],
    history_df: Optional[pd.DataFrame],
    force_chart_update: bool = False
) -> None:
    """
    Renders comprehensive Session Analytics dashboard section with Phase O1 Plotly caching.
    """
    st.markdown('<div style="margin-top: 10px;">', unsafe_allow_html=True)
    
    # 1. Top 8 KPI Metric Cards (Fast HTML rendering on every frame)
    render_kpi_cards(raw_telemetry)

    # 2. Phase O1 Session State Plotly Chart Caching (1.5-Second Refresh Interval)
    if "cached_plotly_figures" not in st.session_state:
        st.session_state.cached_plotly_figures = {}
        st.session_state.last_chart_update_time = 0.0

    now = time.time()
    time_since_update = now - st.session_state.last_chart_update_time

    # Regenerate charts if force_chart_update is True, or if 1.5 seconds have elapsed, or if cache is empty
    if force_chart_update or time_since_update > 1.5 or not st.session_state.cached_plotly_figures:
        st.session_state.cached_plotly_figures = {
            "ear_trend": render_ear_trend_chart(history_df),
            "mar_trend": render_mar_trend_chart(history_df),
            "score_trend": render_score_trend_chart(history_df),
            "blink_freq": render_blink_frequency_chart(history_df),
            "alert_pie": render_alert_distribution_chart(history_df),
        }
        st.session_state.last_chart_update_time = now

    figs = st.session_state.cached_plotly_figures

    # Render Plotly Charts with static unique keys to prevent element collisions
    c1, c2, c3 = st.columns(3, gap="small")

    with c1:
        st.markdown('<div class="dash-card">', unsafe_allow_html=True)
        if "ear_trend" in figs:
            st.plotly_chart(figs["ear_trend"], use_container_width=True, config={'displayModeBar': False}, key="key_ear_trend")
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="dash-card">', unsafe_allow_html=True)
        if "mar_trend" in figs:
            st.plotly_chart(figs["mar_trend"], use_container_width=True, config={'displayModeBar': False}, key="key_mar_trend")
        st.markdown('</div>', unsafe_allow_html=True)

    with c3:
        st.markdown('<div class="dash-card">', unsafe_allow_html=True)
        if "score_trend" in figs:
            st.plotly_chart(figs["score_trend"], use_container_width=True, config={'displayModeBar': False}, key="key_score_trend")
        st.markdown('</div>', unsafe_allow_html=True)

    # Secondary Charts Grid (Blink Frequency & Alert Distribution)
    c_b1, c_b2 = st.columns([1.2, 1.0], gap="medium")

    with c_b1:
        st.markdown('<div class="dash-card">', unsafe_allow_html=True)
        if "blink_freq" in figs:
            st.plotly_chart(figs["blink_freq"], use_container_width=True, config={'displayModeBar': False}, key="key_blink_freq")
        st.markdown('</div>', unsafe_allow_html=True)

    with c_b2:
        st.markdown('<div class="dash-card">', unsafe_allow_html=True)
        if "alert_pie" in figs:
            st.plotly_chart(figs["alert_pie"], use_container_width=True, config={'displayModeBar': False}, key="key_alert_pie")
        st.markdown('</div>', unsafe_allow_html=True)

    # 3. Session Summary & Export Payload Metadata
    render_session_summary(raw_telemetry, history_df)

    st.markdown('</div>', unsafe_allow_html=True)
