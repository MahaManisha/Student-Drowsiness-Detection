"""
Student Drowsiness Detection System - System Information Component

Reports runtime environment diagnostics (Python, Streamlit, OpenCV, MediaPipe, OS, CPU, RAM)
with safe 'Information unavailable' fallbacks.
"""

import sys
import platform
import streamlit as st
import cv2
import mediapipe as mp
from typing import Dict, Any


def get_system_info() -> Dict[str, str]:
    """
    Queries runtime environment diagnostics.
    """
    python_ver = sys.version.split()[0] if sys.version else "Information unavailable"
    streamlit_ver = st.__version__ if hasattr(st, "__version__") else "Information unavailable"
    opencv_ver = cv2.__version__ if hasattr(cv2, "__version__") else "Information unavailable"
    mediapipe_ver = mp.__version__ if hasattr(mp, "__version__") else "Information unavailable"
    os_platform = platform.platform() if hasattr(platform, "platform") else "Information unavailable"

    # CPU & RAM query with psutil fallback
    try:
        import psutil
        cpu_usage = f"{psutil.cpu_percent(interval=None):.1f}%"
        mem = psutil.virtual_memory()
        mem_usage = f"{mem.percent:.1f}% ({mem.used // (1024**2)} MB / {mem.total // (1024**2)} MB)"
    except Exception:
        cpu_usage = "Information unavailable"
        mem_usage = "Information unavailable"

    return {
        "python_ver": python_ver,
        "streamlit_ver": streamlit_ver,
        "opencv_ver": opencv_ver,
        "mediapipe_ver": mediapipe_ver,
        "os_platform": os_platform,
        "cpu_usage": cpu_usage,
        "mem_usage": mem_usage,
    }


def render_system_info_card() -> None:
    """
    Renders System Information diagnostic card.
    """
    info = get_system_info()

    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="font-weight: 800; color: #F9FAFB; font-size: 1.0rem; margin-bottom: 10px;">💻 System & Environment Diagnostics</div>
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; font-size: 0.75rem; background: #111827; padding: 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.06);">
            <div><span style="color: #9CA3AF;">Python Version:</span> <strong style="color: #F9FAFB; font-family: monospace;">{info['python_ver']}</strong></div>
            <div><span style="color: #9CA3AF;">Streamlit Version:</span> <strong style="color: #F9FAFB; font-family: monospace;">{info['streamlit_ver']}</strong></div>
            <div><span style="color: #9CA3AF;">OpenCV Version:</span> <strong style="color: #F9FAFB; font-family: monospace;">{info['opencv_ver']}</strong></div>
            <div><span style="color: #9CA3AF;">MediaPipe Version:</span> <strong style="color: #F9FAFB; font-family: monospace;">{info['mediapipe_ver']}</strong></div>
            <div><span style="color: #9CA3AF;">Platform OS:</span> <strong style="color: #38BDF8; font-family: monospace;">{info['os_platform']}</strong></div>
            <div><span style="color: #9CA3AF;">CPU Load:</span> <strong style="color: #10B981; font-family: monospace;">{info['cpu_usage']}</strong></div>
            <div><span style="color: #9CA3AF;">Memory Usage:</span> <strong style="color: #10B981; font-family: monospace;">{info['mem_usage']}</strong></div>
            <div><span style="color: #9CA3AF;">Hardware Delegate:</span> <strong style="color: #10B981;">CPU (XNNPACK)</strong></div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)
