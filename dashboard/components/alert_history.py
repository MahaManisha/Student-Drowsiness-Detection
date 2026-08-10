"""
Student Drowsiness Detection System - Alert History Component

Renders a scrollable chronological alert history event stream displaying historical events (newest first).
Safely supports both dictionary event objects and string log messages.
"""

import textwrap
import streamlit as st
from typing import Dict, Any, List, Union


def render_alert_history(events: List[Union[Dict[str, Any], str]]) -> None:
    """
    Renders scrollable alert history stream (newest event first).
    Guarantees clean HTML rendering without markdown code block artifacts.
    """
    if not events:
        content_html = '<div style="font-size: 0.75rem; color: #6B7280; padding: 8px 0;">No active alerts logged yet.</div>'
    else:
        # Display newest events first
        reversed_events = list(reversed(events))
        items_html = ""

        for event in reversed_events:
            if isinstance(event, dict):
                icon = event.get("icon", "📌")
                ev_time = event.get("time", "--:--:--")
                msg = event.get("message", "Event logged")
                details = event.get("details", "")
            else:
                event_str = str(event)
                if "HIGHLY" in event_str.upper() or "CRITICAL" in event_str.upper():
                    icon = "🚨"
                elif "DROWSY" in event_str.upper() or "ALERT" in event_str.upper():
                    icon = "⚠️"
                else:
                    icon = "ℹ️"
                icon = event_str.split(" ")[0] if len(event_str) > 0 and event_str[0] in ["🚨", "⚠️", "ℹ️", "📌"] else icon
                ev_time = "--:--:--"
                msg = event_str
                details = ""

            details_html = f'<div style="color: #6B7280; font-size: 0.7rem;">{details}</div>' if details else ''

            items_html += (
                f'<div style="display: flex; justify-content: space-between; align-items: flex-start; font-size: 0.75rem; border-bottom: 1px solid rgba(255,255,255,0.04); padding: 6px 0;">'
                f'<div style="display: flex; gap: 8px; align-items: center;">'
                f'<span>{icon}</span>'
                f'<div>'
                f'<div style="color: #F9FAFB; font-weight: 600;">{msg}</div>'
                f'{details_html}'
                f'</div>'
                f'</div>'
                f'<span class="mono-val" style="color: #9CA3AF; font-size: 0.7rem;">[{ev_time}]</span>'
                f'</div>'
            )

        content_html = f'<div style="max-height: 180px; overflow-y: auto; padding-right: 4px;">{items_html}</div>'

    html = (
        f'<div class="dash-card">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
        f'<div style="font-weight: 700; color: #F9FAFB; font-size: 0.95rem;">📜 Alert Event History</div>'
        f'<span style="font-size: 0.7rem; color: #9CA3AF;">Newest First</span>'
        f'</div>'
        f'{content_html}'
        f'</div>'
    )

    st.markdown(html, unsafe_allow_html=True)
