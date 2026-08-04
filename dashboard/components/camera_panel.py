"""
Student Drowsiness Detection System - Live Camera Viewport Component

Renders the live camera video stream using Streamlit st.empty() placeholders,
providing dynamic status indicators (● LIVE MESH LATCHED vs 🔍 SEARCHING FOR FACE)
and friendly error recovery UI.
"""

import streamlit as st
import numpy as np
from typing import Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


import time

def render_camera_viewport(snapshot: Any, camera_mgr: Any = None) -> float:
    """
    Renders live OpenCV annotated NumPy RGB video feed directly into the viewport.
    This is the SOLE st.image() caller in the dashboard rendering pipeline.
    Consumes the already-fetched FrameSnapshot object (Phase F2).
    Returns exact st.image() serialization duration in milliseconds.
    """
    t_start = time.perf_counter()
    if snapshot is not None and getattr(snapshot, "success", False) and getattr(snapshot, "rgb_frame", None) is not None:
        try:
            img = snapshot.rgb_frame
            if isinstance(img, np.ndarray) and not img.flags['C_CONTIGUOUS']:
                img = np.ascontiguousarray(img)
            st.image(img, channels="RGB", use_container_width=True)
        except Exception as e:
            logger.error(f"[VIEWPORT_RENDER_ERROR] Failed to render image in st.image(): {e}", exc_info=True)
            st.error(f"⚠️ Viewport Render Error: {e}")
    else:
        error_msg = getattr(camera_mgr, "last_error", None) or "Camera device is offline or busy."
        st.error(f"⚠️ {error_msg}")
    t_end = time.perf_counter()
    return (t_end - t_start) * 1000.0



def render_camera_panel_header(is_live: bool, has_face: bool = True, state_str: str = "ALERT") -> None:
    """
    Renders top camera panel card header with live status pill.
    """
    if is_live:
        if has_face:
            pill_html = '<span class="status-pill pill-alert" style="font-size: 0.75rem; padding: 4px 10px;">● LIVE MESH LATCHED</span>'
        else:
            pill_html = '<span class="status-pill pill-slightly" style="font-size: 0.75rem; padding: 4px 10px;">🔍 SEARCHING FOR FACE</span>'
    else:
        pill_html = '<span class="status-pill pill-critical" style="font-size: 0.75rem; padding: 4px 10px;">⚠️ CAMERA OFFLINE</span>'

    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div style="font-weight: 800; color: #F9FAFB; font-size: 1.0rem; display: flex; align-items: center; gap: 8px;">
                <span>📹</span> Live Viewport Stream
            </div>
            {pill_html}
        </div>
        """,
        unsafe_allow_html=True
    )


def render_camera_panel_footer(fps: float, resolution: str = "1280x720", frame_id: Optional[int] = None) -> None:
    """
    Renders camera viewport footer with resolution, FPS, and synchronized Frame ID metrics.
    """
    frame_str = f"#{frame_id}" if frame_id is not None and frame_id > 0 else "#--"
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #9CA3AF; margin-top: 8px; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 6px;">
            <span>Frame: <strong style="color: #F59E0B;">{frame_str}</strong></span>
            <span>Resolution: <strong style="color: #F9FAFB;">{resolution}</strong></span>
            <span>Speed: <strong style="color: #10B981;">{fps:.1f} FPS</strong></span>
            <span>Device: <strong style="color: #38BDF8;">WebCam (ID: 0)</strong></span>
        </div>
        """,
        unsafe_allow_html=True
    )



def render_camera_error_state(error_message: str) -> bool:
    """
    Renders a friendly error message banner and a Retry Camera button.
    
    Returns:
        bool: True if user clicked "Retry Camera Connection", False otherwise.
    """
    st.markdown(
        f"""
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
        """,
        unsafe_allow_html=True
    )

    retry_clicked = st.button("🔄 Retry Camera Connection", type="primary", use_container_width=True)
    return retry_clicked
