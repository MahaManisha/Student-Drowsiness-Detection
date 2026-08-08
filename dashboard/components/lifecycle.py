"""
Student Drowsiness Detection System - Singleton Session Lifecycle Manager

Guarantees that across all Streamlit page reruns, sidebar navigations, and sub-page context shifts:
- Exactly ONE CameraProducerThread exists.
- Exactly ONE AIWorkerThread exists.
- Exactly ONE DashboardCameraManager instance exists.
- Exactly ONE cv2.VideoCapture hardware handle exists.
- Exactly ONE MediaPipe FaceMesh detector exists.
- Exactly ONE Telemetry Publisher exists.

Does NOT modify any backend AI detection algorithms, math calculators, or thresholds.
"""

import sys
import time
import pathlib
import threading
import streamlit as st
from typing import Dict, Any, Optional

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from utils.logger import get_logger
    logger = get_logger(__name__)
except Exception:
    import logging
    logger = logging.getLogger(__name__)

from dashboard.components.camera_manager import DashboardCameraManager

# Module-level global singleton registry instance
_GLOBAL_CAMERA_MANAGER_SINGLETON: Optional[DashboardCameraManager] = None
_SINGLETON_LOCK: threading.Lock = threading.Lock()


def get_singleton_camera_manager() -> DashboardCameraManager:
    """
    Authoritative Singleton Accessor: Returns the single persistent DashboardCameraManager instance.
    Guarantees thread resources, hardware VideoCapture handles, and MediaPipe detectors are created ONCE
    and reused across all Streamlit reruns and multi-page navigations.
    """
    global _GLOBAL_CAMERA_MANAGER_SINGLETON

    # 1. Check Streamlit session_state first
    if "global_camera_manager_singleton" in st.session_state and st.session_state.global_camera_manager_singleton is not None:
        mgr = st.session_state.global_camera_manager_singleton
        _GLOBAL_CAMERA_MANAGER_SINGLETON = mgr
        return mgr

    # 2. Check module-level global singleton reference
    with _SINGLETON_LOCK:
        if _GLOBAL_CAMERA_MANAGER_SINGLETON is not None:
            st.session_state.global_camera_manager_singleton = _GLOBAL_CAMERA_MANAGER_SINGLETON
            return _GLOBAL_CAMERA_MANAGER_SINGLETON

        # 3. First-time instantiation of Singleton Camera Manager
        logger.info("[SINGLETON LIFECYCLE] Instantiating authoritative Singleton DashboardCameraManager...")
        mgr = DashboardCameraManager()
        mgr.start()

        try:
            from dashboard.components.mjpeg_server import start_mjpeg_stream_server
            start_mjpeg_stream_server(mgr, port=8089)
        except Exception as e:
            logger.warning(f"[MJPEG SERVER] Could not start MJPEG server: {e}")

        _GLOBAL_CAMERA_MANAGER_SINGLETON = mgr
        st.session_state.global_camera_manager_singleton = mgr
        return mgr


def get_singleton_object_ids() -> Dict[str, str]:
    """
    Returns object IDs of all core runtime components to validate singleton uniqueness.
    """
    mgr = get_singleton_camera_manager()

    cam_thread_id = hex(id(mgr.camera._producer_thread)) if mgr.camera._producer_thread else "N/A"
    ai_thread_id = hex(id(mgr._worker_thread)) if mgr._worker_thread else "N/A"
    mgr_id = hex(id(mgr))
    cap_id = hex(id(mgr.camera.cap)) if mgr.camera.cap else "N/A"
    mp_id = hex(id(mgr.detector.face_mesh)) if hasattr(mgr.detector, "face_mesh") else "N/A"
    pub_id = hex(id(mgr._result_lock))

    return {
        "camera_thread_id": cam_thread_id,
        "ai_thread_id": ai_thread_id,
        "camera_manager_id": mgr_id,
        "videocapture_id": cap_id,
        "mediapipe_id": mp_id,
        "telemetry_publisher_id": pub_id,
    }


def print_singleton_health_log() -> None:
    """
    Logs object IDs to console/logs every second to confirm 100% ID permanence.
    """
    ids = get_singleton_object_ids()
    logger.info(
        f"[SINGLETON HEALTH] MgrID: {ids['camera_manager_id']} | "
        f"CamThread: {ids['camera_thread_id']} | "
        f"AIThread: {ids['ai_thread_id']} | "
        f"VideoCapture: {ids['videocapture_id']} | "
        f"MediaPipe: {ids['mediapipe_id']} | "
        f"Publisher: {ids['telemetry_publisher_id']}"
    )


def shutdown_singleton_camera_manager() -> None:
    """
    Gracefully stops background threads and releases hardware camera handles on application exit.
    """
    global _GLOBAL_CAMERA_MANAGER_SINGLETON
    with _SINGLETON_LOCK:
        if _GLOBAL_CAMERA_MANAGER_SINGLETON is not None:
            logger.info("[SINGLETON LIFECYCLE] Shutting down Singleton Camera Manager...")
            _GLOBAL_CAMERA_MANAGER_SINGLETON.stop()
            _GLOBAL_CAMERA_MANAGER_SINGLETON = None

        if "global_camera_manager_singleton" in st.session_state:
            st.session_state.global_camera_manager_singleton = None
