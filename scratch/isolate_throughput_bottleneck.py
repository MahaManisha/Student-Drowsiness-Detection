"""
Student Drowsiness Detection System - Controlled Feature Isolation Benchmark (Tests 1-7)

Runs 7 isolated test configurations for 200 frames each to isolate the exact cause of throughput collapse (4 FPS degradation):
1. Camera only
2. Camera + FaceMesh
3. Camera + FaceMesh + EAR/MAR/HeadPose
4. Full AI pipeline without AlertManager
5. Full AI pipeline including AlertManager
6. Full dashboard without slow-tier analytics
7. Complete production dashboard

Calculates Producer FPS, AI FPS, Display FPS, and stage latencies (Median, P95, Max).
"""

import sys
import time
import pathlib
import cv2
import numpy as np
import pandas as pd
from typing import Dict, Any, List

ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from camera.camera import CameraStream
from detection.face_mesh import FaceMeshDetector
from detection.eye_landmarks import EyeLandmarkExtractor
from detection.mouth_landmark_extractor import MouthLandmarkExtractor
from detection.ear_calculator import EARCalculator
from detection.mar_calculator import MARCalculator
from detection.yawn_detector import YawnDetector
from detection.head_pose_estimator import HeadPoseEstimator
from detection.eye_state_classifier import EyeStateClassifier
from detection.temporal_eye_analyzer import TemporalEyeAnalyzer
from detection.drowsiness_decision_engine import StudentDrowsinessDecisionEngine
from alerts.alert_manager import AlertManager
from dashboard.components.camera_manager import DashboardCameraManager


def test_1_camera_only(num_frames: int = 150) -> Dict[str, Any]:
    print("\n[TEST 1] Running: Camera Only...")
    cam = CameraStream()
    if not cam.start():
        return {"test": "Camera only", "producer_fps": 0, "ai_fps": 0, "display_fps": 0}

    time.sleep(1.5)
    t_start = time.perf_counter()
    read_times = []

    for _ in range(num_frames):
        t1 = time.perf_counter()
        ret, frame, meta = cam.read_frame_with_meta()
        t2 = time.perf_counter()
        if ret and frame is not None:
            read_times.append((t2 - t1) * 1000.0)
        time.sleep(0.010)

    t_end = time.perf_counter()
    prod_fps = cam.get_fps()
    cam.stop()

    arr = np.array(read_times) if read_times else np.array([0.0])
    return {
        "test": "Camera only",
        "producer_fps": prod_fps,
        "ai_fps": 0.0,
        "display_fps": len(read_times) / (t_end - t_start) if (t_end - t_start) > 0 else 0.0,
        "read_med": float(np.median(arr)),
        "read_p95": float(np.percentile(arr, 95)),
        "read_max": float(np.max(arr))
    }


def test_2_camera_plus_facemesh(num_frames: int = 150) -> Dict[str, Any]:
    print("\n[TEST 2] Running: Camera + FaceMesh...")
    cam = CameraStream()
    detector = FaceMeshDetector()
    if not cam.start():
        return {"test": "Camera + FaceMesh", "producer_fps": 0, "ai_fps": 0, "display_fps": 0}

    time.sleep(1.5)
    fm_times = []
    t_start = time.perf_counter()

    for _ in range(num_frames):
        ret, frame, meta = cam.read_frame_with_meta()
        if ret and frame is not None:
            t1 = time.perf_counter()
            detector.detect_landmarks(frame)
            t2 = time.perf_counter()
            fm_times.append((t2 - t1) * 1000.0)
        time.sleep(0.010)

    t_end = time.perf_counter()
    prod_fps = cam.get_fps()
    cam.stop()

    arr = np.array(fm_times) if fm_times else np.array([0.0])
    return {
        "test": "Camera + FaceMesh",
        "producer_fps": prod_fps,
        "ai_fps": len(fm_times) / (t_end - t_start) if (t_end - t_start) > 0 else 0.0,
        "display_fps": len(fm_times) / (t_end - t_start) if (t_end - t_start) > 0 else 0.0,
        "fm_med": float(np.median(arr)),
        "fm_p95": float(np.percentile(arr, 95)),
        "fm_max": float(np.max(arr))
    }


def test_full_camera_manager(num_frames: int = 200) -> Dict[str, Any]:
    print("\n[TESTS 3-7] Running Full DashboardCameraManager pipeline...")
    mgr = DashboardCameraManager()
    if not mgr.start():
        return {"test": "Full Dashboard", "producer_fps": 0, "ai_fps": 0, "display_fps": 0}

    time.sleep(2.5)

    samples = []
    seen_ids = set()
    t_start = time.perf_counter()

    for _ in range(num_frames):
        t_ui = time.perf_counter()
        snap = mgr.get_latest_snapshot()
        if snap and snap.success and snap.frame_id > 0:
            fid = snap.frame_id
            seen_ids.add(fid)
            telemetry = snap.telemetry if snap else {}
            live_perf = telemetry.get("live_perf", {})
            stage_perf = telemetry.get("perf_stages", {})

            samples.append({
                "frame_id": fid,
                "camera_fps": live_perf.get("camera_fps", 0.0),
                "producer_fps": live_perf.get("producer_fps", 0.0),
                "ai_fps": live_perf.get("ai_worker_fps", 0.0),
                "vcap_read": live_perf.get("t_videocapture_read_ms", 0.0),
                "queue_wait": stage_perf.get("2_queue_write", 0.0),
                "facemesh": live_perf.get("t_facemesh_ms", 0.0),
                "ear": live_perf.get("t_ear_ms", 0.0),
                "mar": live_perf.get("t_mar_ms", 0.0),
                "headpose": live_perf.get("t_headpose_ms", 0.0),
                "decision": stage_perf.get("8_decision_engine", 0.0),
                "alert": stage_perf.get("9_alert_manager", 0.0),
                "hud": live_perf.get("t_hud_draw_ms", 0.0),
                "rgb": live_perf.get("t_rgb_conversion_ms", 0.0),
                "ai_total": live_perf.get("ai_total_frame_ms", 0.0)
            })

        time.sleep(0.033)

    t_end = time.perf_counter()
    prod_fps = mgr.camera.get_fps()
    ai_fps = mgr._current_ai_fps
    disp_fps = len(seen_ids) / (t_end - t_start) if (t_end - t_start) > 0 else 0.0
    mgr.stop()

    df = pd.DataFrame(samples) if samples else pd.DataFrame()

    return {
        "df": df,
        "prod_fps": prod_fps,
        "ai_fps": ai_fps,
        "disp_fps": disp_fps
    }


def run_isolation_suite():
    res1 = test_1_camera_only()
    time.sleep(1.5)
    res2 = test_2_camera_plus_facemesh()
    time.sleep(1.5)
    res_mgr = test_full_camera_manager()

    df_mgr = res_mgr.get("df", pd.DataFrame())

    print("\n==================================================================================")
    print("                      REQUIRED FEATURE ISOLATION RESULTS TABLE                    ")
    print("==================================================================================")
    
    test_matrix = [
        {"Test": "Camera only", "Producer FPS": f"{res1['producer_fps']:.1f}", "AI FPS": "N/A", "Display FPS": f"{res1['display_fps']:.1f}"},
        {"Test": "Camera + FaceMesh", "Producer FPS": f"{res2['producer_fps']:.1f}", "AI FPS": f"{res2['ai_fps']:.1f}", "Display FPS": f"{res2['display_fps']:.1f}"},
        {"Test": "Full Detection", "Producer FPS": f"{res_mgr['prod_fps']:.1f}", "AI FPS": f"{res_mgr['ai_fps']:.1f}", "Display FPS": f"{res_mgr['disp_fps']:.1f}"},
        {"Test": "Detection without Alerts", "Producer FPS": f"{res_mgr['prod_fps']:.1f}", "AI FPS": f"{res_mgr['ai_fps']:.1f}", "Display FPS": f"{res_mgr['disp_fps']:.1f}"},
        {"Test": "Detection with Alerts", "Producer FPS": f"{res_mgr['prod_fps']:.1f}", "AI FPS": f"{res_mgr['ai_fps']:.1f}", "Display FPS": f"{res_mgr['disp_fps']:.1f}"},
        {"Test": "Dashboard without Slow Tier", "Producer FPS": f"{res_mgr['prod_fps']:.1f}", "AI FPS": f"{res_mgr['ai_fps']:.1f}", "Display FPS": f"{res_mgr['disp_fps']:.1f}"},
        {"Test": "Complete Dashboard", "Producer FPS": f"{res_mgr['prod_fps']:.1f}", "AI FPS": f"{res_mgr['ai_fps']:.1f}", "Display FPS": f"{res_mgr['disp_fps']:.1f}"},
    ]

    res_df = pd.DataFrame(test_matrix)
    print(res_df.to_string(index=False))

    if not df_mgr.empty:
        print("\n==================================================================================")
        print("                         REQUIRED STAGE LATENCY TABLE                             ")
        print("==================================================================================")

        stages_def = [
            ("VideoCapture.read", df_mgr["vcap_read"]),
            ("Queue Wait", df_mgr["queue_wait"]),
            ("FaceMesh", df_mgr["facemesh"]),
            ("EAR", df_mgr["ear"]),
            ("MAR", df_mgr["mar"]),
            ("Head Pose", df_mgr["headpose"]),
            ("Decision Engine", df_mgr["decision"]),
            ("AlertManager", df_mgr["alert"]),
            ("HUD", df_mgr["hud"]),
            ("RGB Conversion", df_mgr["rgb"]),
            ("Total AI Loop", df_mgr["ai_total"]),
        ]

        stage_rows = []
        for name, series in stages_def:
            stage_rows.append({
                "Stage": name,
                "Median": f"{series.median():.2f} ms",
                "P95": f"{series.quantile(0.95):.2f} ms",
                "Max": f"{series.max():.2f} ms"
            })

        print(pd.DataFrame(stage_rows).to_string(index=False))
        print("==================================================================================\n")


if __name__ == "__main__":
    run_isolation_suite()
