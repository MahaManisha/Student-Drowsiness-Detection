"""
Student Drowsiness Detection System - Report History Component

Renders a historical reports catalog displaying completed session records with instant download triggers.
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional
from dashboard.components.export_panel import generate_json_bytes


def render_report_history(reports_catalog: Optional[List[Dict[str, Any]]] = None) -> None:
    """
    Renders Report History cards with instant download controls.
    """
    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <div style="font-weight: 800; color: #F9FAFB; font-size: 1.0rem;">📜 Historical Session Reports</div>
            <span style="font-size: 0.7rem; color: #9CA3AF;">Saved Reports Archive</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    if reports_catalog is None:
        reports_catalog = [
            {
                "session_id": "Session 001",
                "status": "COMPLETED",
                "date": "July 25, 2026",
                "duration": "01:24:15",
                "avg_ear": 0.285,
                "peak_score": 12.0,
            },
            {
                "session_id": "Session 002",
                "status": "COMPLETED",
                "date": "July 24, 2026",
                "duration": "00:45:10",
                "avg_ear": 0.271,
                "peak_score": 48.5,
            },
            {
                "session_id": "Session 003",
                "status": "COMPLETED",
                "date": "July 24, 2026",
                "duration": "02:10:00",
                "avg_ear": 0.264,
                "peak_score": 85.0,
            },
        ]

    if not reports_catalog:
        st.markdown(
            """
            <div style="background-color: #111827; border: 1px solid rgba(255,255,255,0.06); padding: 16px; border-radius: 8px; text-align: center; color: #9CA3AF; font-size: 0.85rem;">
                No completed monitoring sessions available.
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        for idx, report in enumerate(reports_catalog):
            col_info, col_btn = st.columns([3, 1])

            with col_info:
                st.markdown(
                    f"""
                    <div style="background: #111827; border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 10px 12px; margin-bottom: 6px;">
                        <div style="display: flex; justify-content: space-between; font-weight: 700; color: #F9FAFB; font-size: 0.85rem;">
                            <span>{report['session_id']}</span>
                            <span style="color: #10B981; font-weight: 800; font-size: 0.75rem;">● {report['status']}</span>
                        </div>
                        <div style="display: flex; gap: 16px; font-size: 0.75rem; color: #9CA3AF; margin-top: 4px;">
                            <span>Date: <strong style="color: #F9FAFB;">{report['date']}</strong></span>
                            <span>Duration: <strong style="color: #F9FAFB;">{report['duration']}</strong></span>
                            <span>Avg EAR: <strong style="color: #10B981;">{report['avg_ear']:.3f}</strong></span>
                            <span>Peak Score: <strong style="color: #F59E0B;">{report['peak_score']:.0f}</strong></span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col_btn:
                # Generate sample bytes for history download
                sample_bytes = generate_json_bytes({"session_stats": {"total_session_time": report['duration'], "average_ear": report['avg_ear'], "highest_score": report['peak_score']}}, None)
                st.download_button(
                    label=f"📥 Download",
                    data=sample_bytes,
                    file_name=f"{report['session_id'].replace(' ', '_').lower()}_report.json",
                    mime="application/json",
                    key=f"dl_hist_{idx}",
                    use_container_width=True
                )

    st.markdown('</div>', unsafe_allow_html=True)
