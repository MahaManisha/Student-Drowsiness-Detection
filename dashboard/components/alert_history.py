"""
Student Drowsiness Detection System - Alert History Component

Renders a scrollable chronological alert history event stream displaying historical events (newest first).
"""

import streamlit as st
from typing import Dict, Any, List


def render_alert_history(events: List[Dict[str, Any]]) -> None:
    """
    Renders scrollable alert history stream (newest event first).
    """
    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div style="font-weight: 700; color: #F9FAFB; font-size: 0.95rem;">📜 Alert Event History</div>
            <span style="font-size: 0.7rem; color: #9CA3AF;">Newest First</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    if not events:
        st.markdown('<div style="font-size: 0.75rem; color: #6B7280; padding: 8px 0;">No active alerts logged yet.</div>', unsafe_allow_html=True)
    else:
        # Display newest events first
        reversed_events = list(reversed(events))
        
        st.markdown('<div style="max-height: 180px; overflow-y: auto; padding-right: 4px;">', unsafe_allow_html=True)
        for event in reversed_events:
            icon = event.get("icon", "📌")
            ev_time = event.get("time", "00:00:00")
            msg = event.get("message", "Event logged")
            details = event.get("details", "")

            st.markdown(
                f"""
                <div style="display: flex; justify-content: space-between; align-items: flex-start; font-size: 0.75rem; border-bottom: 1px solid rgba(255,255,255,0.04); padding: 6px 0;">
                    <div style="display: flex; gap: 8px; align-items: center;">
                        <span>{icon}</span>
                        <div>
                            <div style="color: #F9FAFB; font-weight: 600;">{msg}</div>
                            <div style="color: #6B7280; font-size: 0.7rem;">{details}</div>
                        </div>
                    </div>
                    <span class="mono-val" style="color: #9CA3AF; font-size: 0.7rem;">[{ev_time}]</span>
                </div>
                """,
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
