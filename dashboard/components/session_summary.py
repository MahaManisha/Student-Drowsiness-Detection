"""
Student Drowsiness Detection System - Session Summary Component

Renders the Session Summary Metadata Panel and prepares export-ready data structures
(CSV, PDF, JSON compatible schemas).
Integrates type-safe telemetry formatters to prevent numeric formatting crashes.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional
from dashboard.utils.formatters import safe_float, safe_percentage, safe_duration, safe_int


def build_export_payload(raw_telemetry: Dict[str, Any], history_df: Optional[pd.DataFrame]) -> Dict[str, Any]:
    """
    Constructs an export-ready data payload dictionary (CSV/JSON/PDF compatible).
    """
    stats = raw_telemetry.get("session_stats", {}) if raw_telemetry else {}
    longest_closure = stats.get('longest_eye_closure', raw_telemetry.get('eye_closed_duration'))
    confidence = raw_telemetry.get('decision_confidence', 98.0)
    highest_score = stats.get('highest_score', raw_telemetry.get('drowsiness_score', 0.0))
    fps_val = raw_telemetry.get('fps', 30.0) if raw_telemetry else 30.0

    summary = {
        "monitoring_started": "09:24:00",
        "monitoring_status": "ACTIVE" if float(fps_val or 0) > 0 else "COMPLETED",
        "total_runtime": stats.get("total_session_time", "00:00:00"),
        "longest_continuous_alert": safe_duration(longest_closure, precision=2, default="0.00s"),
        "average_confidence": safe_percentage(confidence, precision=0, default="98%"),
        "peak_score": f"{safe_float(highest_score, precision=0, default='0')} / 100",
        "average_fps": f"{safe_float(fps_val, precision=1, default='30.0')} FPS"
    }

    telemetry_records = history_df.to_dict(orient="records") if history_df is not None and not history_df.empty else []

    return {
        "session_summary": summary,
        "telemetry_records_count": len(telemetry_records),
        "telemetry_records": telemetry_records,
        "events": raw_telemetry.get("events", []) if raw_telemetry else []
    }


def render_session_summary(raw_telemetry: Dict[str, Any], history_df: Optional[pd.DataFrame]) -> None:
    """
    Renders Session Summary metadata panel and export preview readiness.
    """
    payload = build_export_payload(raw_telemetry, history_df)
    s = payload["session_summary"]

    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="font-weight: 700; color: #F9FAFB; font-size: 0.95rem; margin-bottom: 10px;">📋 Session Summary & Export Metadata</div>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; font-size: 0.75rem; background: #111827; padding: 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.06); margin-bottom: 10px;">
            <div><span style="color: #9CA3AF;">Started:</span> <strong style="color: #F9FAFB;">{s['monitoring_started']}</strong></div>
            <div><span style="color: #9CA3AF;">Status:</span> <strong style="color: #10B981;">{s['monitoring_status']}</strong></div>
            <div><span style="color: #9CA3AF;">Total Runtime:</span> <strong style="color: #F9FAFB;">{s['total_runtime']}</strong></div>
            <div><span style="color: #9CA3AF;">Longest Alert:</span> <strong style="color: #EF4444;">{s['longest_continuous_alert']}</strong></div>
            <div><span style="color: #9CA3AF;">Avg Confidence:</span> <strong style="color: #38BDF8;">{s['average_confidence']}</strong></div>
            <div><span style="color: #9CA3AF;">Peak Score:</span> <strong style="color: #F59E0B;">{s['peak_score']}</strong></div>
            <div><span style="color: #9CA3AF;">Avg Speed:</span> <strong style="color: #F9FAFB;">{s['average_fps']}</strong></div>
            <div><span style="color: #9CA3AF;">Data Points:</span> <strong style="color: #38BDF8;">{payload['telemetry_records_count']} rows</strong></div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)
