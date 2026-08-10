"""
Student Drowsiness Detection System - Sidebar Navigation Component

Renders the left navigation menu inside the Streamlit sidebar.
"""

import streamlit as st
from streamlit_option_menu import option_menu


def render_sidebar() -> str:
    """
    Renders sidebar navigation and returns selected page name.
    """
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align: center; padding: 10px 0 20px 0;">
                <h3 style="color: #F9FAFB; margin: 0; font-weight: 800;">Triton Detection</h3>
                <p style="color: #10B981; font-size: 0.8rem; margin: 4px 0 0 0; font-weight: 600;">v2.5 Enterprise Edition</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        selected = option_menu(
            menu_title=None,
            options=["Dashboard", "Reports", "Session History", "Settings", "About"],
            icons=["speedometer2", "file-earmark-bar-graph", "clock-history", "gear", "info-circle"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#10B981", "font-size": "18px"},
                "nav-link": {
                    "font-size": "15px",
                    "text-align": "left",
                    "margin": "6px 4px",
                    "color": "#E2E8F0",
                    "border-radius": "8px",
                    "font-weight": "600",
                },
                "nav-link-selected": {
                    "background-color": "#1F2937",
                    "color": "#FFFFFF",
                    "font-weight": "800",
                    "border-left": "4px solid #10B981",
                },
            },
        )

        st.markdown("---")
        st.markdown(
            """
            <div style="padding: 10px; background-color: #1F2937; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08);">
                <div style="font-size: 0.75rem; color: #9CA3AF; font-weight: 600;">SYSTEM STATUS</div>
                <div style="font-size: 0.85rem; color: #10B981; font-weight: 700; margin-top: 4px;">● MediaPipe Solver Active</div>
                <div style="font-size: 0.75rem; color: #6B7280; margin-top: 4px;">Camera ID: 0 (WebCam)</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        return selected
