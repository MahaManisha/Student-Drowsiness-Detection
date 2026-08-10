"""
Student Drowsiness Detection System - Live Camera Viewport Component

Renders the live camera video stream using Streamlit st.empty() placeholders,
providing dynamic status indicators (● LIVE MESH LATCHED vs 🔍 SEARCHING FOR FACE)
and friendly error recovery UI.
"""

import sys
import pathlib

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import cv2
import streamlit as st
import numpy as np
from typing import Dict, Any, Optional

try:
    from utils.logger import get_logger
    logger = get_logger(__name__)
except Exception:
    import logging
    logger = logging.getLogger(__name__)


import base64
import textwrap
from PIL import Image
import time

from dashboard.components.mjpeg_server import get_mjpeg_stream_port

def render_camera_viewport(snapshot: Any, camera_mgr: Any = None) -> float:
    """
    Renders live camera video viewport using native HTTP MJPEG stream (http://localhost:8089/video_feed).
    Eliminates Base64 encoding lag, Streamlit fragment locking, and video freezing permanently.
    """
    t_start = time.perf_counter()
    port = get_mjpeg_stream_port()

    if port > 0:
        img_html = (
            f'<div style="width:100%; text-align:center; background-color:#0d0e12; border-radius:12px; overflow:hidden; padding:4px;">'
            f'<img src="http://localhost:{port}/video_feed" style="width:100%; max-height:460px; object-fit:contain; border-radius:10px; display:block; margin:0 auto;" />'
            f'</div>'
        )
        st.markdown(img_html, unsafe_allow_html=True)
        t_end = time.perf_counter()
        return (t_end - t_start) * 1000.0

    # Fallback to Base64 frame rendering if MJPEG server is unavailable
    bgr_frame = getattr(snapshot, "bgr_frame", None) if snapshot is not None else None
    if bgr_frame is None and snapshot is not None and getattr(snapshot, "rgb_frame", None) is not None:
        bgr_frame = cv2.cvtColor(snapshot.rgb_frame, cv2.COLOR_RGB2BGR)

    if bgr_frame is not None and isinstance(bgr_frame, np.ndarray) and bgr_frame.size > 0:
        is_ok, jpeg_buf = cv2.imencode('.jpg', bgr_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if is_ok:
            b64_str = base64.b64encode(jpeg_buf).decode('utf-8')
            img_html = (
                f'<div style="width:100%; text-align:center; background-color:#0d0e12; border-radius:12px; overflow:hidden; padding:4px;">'
                f'<img src="data:image/jpeg;base64,{b64_str}" style="width:100%; max-height:460px; object-fit:contain; border-radius:10px; display:block; margin:0 auto;" />'
                f'</div>'
            )
            st.markdown(img_html, unsafe_allow_html=True)
            t_end = time.perf_counter()
            return (t_end - t_start) * 1000.0

    st.markdown(
        '<div style="width:100%; height:440px; background-color:#0d0e12; border-radius:12px; display:flex; align-items:center; justify-content:center; color:#6B7280;">Connecting camera device...</div>',
        unsafe_allow_html=True
    )

    t_end = time.perf_counter()
    return (t_end - t_start) * 1000.0



def render_camera_panel_header(is_live: bool, has_face: bool = True, state_str: str = "ALERT", is_stalled: bool = False) -> None:
    """
    Renders top camera panel card header with live status pill.
    """
    if is_stalled:
        pill_html = '<span class="status-pill pill-critical" style="font-size: 0.75rem; padding: 4px 10px; background: rgba(239, 68, 68, 0.25); color: #EF4444;">⚠️ STREAM STALLED</span>'
    elif is_live:
        if has_face:
            pill_html = '<span class="status-pill pill-alert" style="font-size: 0.75rem; padding: 4px 10px;">● LIVE MESH LATCHED</span>'
        else:
            pill_html = '<span class="status-pill pill-slightly" style="font-size: 0.75rem; padding: 4px 10px;">🔍 SEARCHING FOR FACE</span>'
    else:
        pill_html = '<span class="status-pill pill-critical" style="font-size: 0.75rem; padding: 4px 10px;">⚠️ CAMERA OFFLINE</span>'

    st.markdown(
        textwrap.dedent(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div style="font-weight: 800; color: #F9FAFB; font-size: 1.0rem; display: flex; align-items: center; gap: 8px;">
                <span>📹</span> Live Viewport Stream
            </div>
            {pill_html}
        </div>
        """),
        unsafe_allow_html=True
    )


def render_camera_panel_footer(fps: float, resolution: str = "1280x720", frame_id: Optional[int] = None) -> None:
    """
    Renders camera viewport footer with resolution, FPS, and synchronized Frame ID metrics.
    """
    frame_str = f"#{frame_id}" if frame_id is not None and frame_id > 0 else "#--"
    st.markdown(
        textwrap.dedent(f"""
        <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #9CA3AF; margin-top: 8px; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 6px;">
            <span>Frame: <strong style="color: #F59E0B;">{frame_str}</strong></span>
            <span>Resolution: <strong style="color: #F9FAFB;">{resolution}</strong></span>
            <span>Speed: <strong style="color: #10B981;">{fps:.1f} FPS</strong></span>
            <span>Device: <strong style="color: #38BDF8;">WebCam (ID: 0)</strong></span>
        </div>
        """),
        unsafe_allow_html=True
    )



def render_camera_error_state(error_message: str) -> bool:
    """
    Renders a friendly error message banner and a Retry Camera button.
    
    Returns:
        bool: True if user clicked "Retry Camera Connection", False otherwise.
    """
    st.markdown(
        textwrap.dedent(f"""
        <div style="background-color: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.5); border-radius: 12px; padding: 20px; text-align: center; margin: 10px 0;">
            <div style="font-size: 2rem; margin-bottom: 6px;">📹⚠️</div>
            <h4 style="color: #EF4444; margin: 0 0 6px 0; font-weight: 700;">Camera Stream Unavailable</h4>
            <p style="color: #D1D5DB; font-size: 0.85rem; margin: 0 0 12px 0;">
                {error_message}
            </p>
            <div style="font-size: 0.75rem; color: #9CA3AF;">
                Please verify that your webcam is connected, not locked by another app, and camera permissions are granted.
            </div>
        </div>
        """),
        unsafe_allow_html=True
    )

    retry_clicked = st.button("🔄 Retry Camera Connection", type="primary", use_container_width=True)
    return retry_clicked
