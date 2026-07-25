"""
Student Drowsiness Detection System - Alert Badge Component

Renders reusable severity status badges with state-driven color accents and animations.
"""

import streamlit as st
from typing import Tuple


def get_alert_badge_style(state: str) -> Tuple[str, str, str]:
    """
    Returns (pill_class, status_label, icon_symbol) for a given drowsiness state.
    
    Severities:
      - NORMAL (ALERT): Green static
      - WARNING (SLIGHTLY_DROWSY): Amber slow pulse
      - DROWSY: Orange pulse
      - HIGHLY DROWSY (CRITICAL): Red flashing pulse
    """
    state_upper = (state or "ALERT").upper()

    if state_upper in ["ALERT", "NORMAL"]:
        return "pill-alert", "🟢 NORMAL", "🛡️"
    elif state_upper in ["SLIGHTLY_DROWSY", "WARNING", "SLIGHTLY"]:
        return "pill-slightly", "🟡 WARNING", "⚠️"
    elif state_upper in ["DROWSY"]:
        return "pill-drowsy", "🟠 DROWSY", "🚨"
    else:
        return "pill-critical", "🔴 HIGHLY DROWSY", "🚨"


def render_alert_badge(state: str, font_size: str = "0.75rem") -> None:
    """
    Renders an animated alert status badge HTML component.
    """
    pill_class, label, _ = get_alert_badge_style(state)
    html = f'<span class="status-pill {pill_class}" style="font-size: {font_size}; padding: 4px 10px;">{label}</span>'
    st.markdown(html, unsafe_allow_html=True)
