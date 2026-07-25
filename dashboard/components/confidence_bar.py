"""
Student Drowsiness Detection System - Decision Confidence Bar Component

Renders a horizontal confidence progress bar with percentage fill and gradient styling.
"""

import streamlit as st
from typing import Optional


def render_confidence_bar(confidence: Optional[float] = 98.0) -> None:
    """
    Renders an animated horizontal decision confidence progress bar.
    """
    if confidence is None:
        conf_val = 0.0
        conf_str = "N/A"
    else:
        conf_val = min(100.0, max(0.0, float(confidence)))
        conf_str = f"{conf_val:.0f}%"

    st.markdown(
        f"""
        <div style="margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #9CA3AF; margin-bottom: 4px;">
                <span style="font-weight: 600;">Decision Confidence</span>
                <span class="mono-val" style="color: #38BDF8; font-weight: 700;">{conf_str}</span>
            </div>
            <div style="height: 8px; background-color: #374151; border-radius: 4px; overflow: hidden; position: relative;">
                <div style="width: {conf_val}%; height: 100%; background: linear-gradient(90deg, #0284C7, #38BDF8); border-radius: 4px; transition: width 0.3s ease;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
