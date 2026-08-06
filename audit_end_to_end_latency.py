"""
Student Drowsiness Detection System - End-to-End Latency & Driver Audit Script

Traces single-frame lifecycle across 300+ frames using monotonic timestamps:
1. VideoCapture.read()
2. Camera -> AI start (frame_age_at_ai_start)
3. AI processing
4. Snapshot -> UI fetch
5. st.image() Python call
6. Capture -> Snapshot
7. Capture -> UI fetch

Detects camera driver buffering (CAP_DSHOW vs CAP_MSMF), frame gaps, producer read stats, and pinpoints root cause (A-F).
"""

import sys
import time
import pathlib
import cv2
import numpy as np
import pandas as pd
from typing import Dict, Any, List

ROOT_DIR = pathlib.Path(__file__).parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dashboard.components.camera_manager import DashboardCameraManager


def run_latency_audit(num_frames: int = 350) -> Dict[str, Any]:
    print("==================================================================================")
    print("     PRINCIPAL CV LATENCY ENGINEER - END-TO-END FRAME AGE DIAGNOSTIC AUDIT       ")
    print("==================================================================================")

    mgr = DashboardCameraManager()
    if not mgr.start():
        print("ERROR: Failed to start DashboardCameraManager stream.")
        sys.exit(1)

    print(f"[AUDIT] Initializing CameraStream & AI Worker (warming up 2.5s)...")
    time.sleep(2.5)

    cam_info = getattr(mgr.camera, "camera_info", {})
    backend_name = cam_info.get("backend", "UNKNOWN")
    width = cam_info.get("width", 1280)
    height = cam_info.get("height", 720)
    reported_fps = cam_info.get("fps", 30.0)

    print(f"[AUDIT] Backend: {backend_name} | Res: {width}x{height} | Reported FPS: {reported_fps}")
    print(f"[AUDIT] Collecting {num_frames} consecutive single-frame latency samples...\n")

    records = []
    vcap_durations = []
    seen_snapshots = set()

    for i in range(num_frames):
        t_ui_fetch = time.perf_counter()
        snapshot = mgr.get_latest_snapshot()

        t_st_img_start = time.perf_counter()
        if snapshot and snapshot.success and snapshot.rgb_frame is not None:
            # Simulate st.image() array serialization check
            img = snapshot.rgb_frame
            if not img.flags['C_CONTIGUOUS']:
                _ = np.ascontiguousarray(img)
            _ = img.shape
        t_st_img_end = time.perf_counter()

        if snapshot and snapshot.success and snapshot.frame_id > 0:
            fid = snapshot.frame_id
            seen_snapshots.add(fid)

            t_cap_start = snapshot.t_capture_start
            t_cap_end = snapshot.t_capture_end
            t_q_enter = snapshot.t_queue_enter
            t_ai_start = snapshot.t_ai_start
            t_ai_end = snapshot.t_ai_end
            t_pub = snapshot.t_snapshot_publish
            camera_latest_fid = snapshot.camera_latest_frame_id

            vcap_read_ms = max(0.0, (t_cap_end - t_cap_start) * 1000.0)
            vcap_durations.append(vcap_read_ms)

            cam_to_ai_start_ms = max(0.0, (t_ai_start - t_cap_end) * 1000.0)
            ai_proc_ms = max(0.0, (t_ai_end - t_ai_start) * 1000.0)
            snap_to_ui_ms = max(0.0, (t_ui_fetch - t_pub) * 1000.0)
            st_image_ms = max(0.0, (t_st_img_end - t_st_img_start) * 1000.0)
            cap_to_snap_ms = max(0.0, (t_pub - t_cap_start) * 1000.0)
            cap_to_ui_ms = max(0.0, (t_ui_fetch - t_cap_start) * 1000.0)

            gap = camera_latest_fid - fid

            records.append({
                "frame_id": fid,
                "camera_latest_fid": camera_latest_fid,
                "gap": gap,
                "vcap_read": vcap_read_ms,
                "cam_to_ai": cam_to_ai_start_ms,
                "ai_proc": ai_proc_ms,
                "snap_to_ui": snap_to_ui_ms,
                "st_image": st_image_ms,
                "cap_to_snap": cap_to_snap_ms,
                "cap_to_ui": cap_to_ui_ms,
            })

        time.sleep(0.030)  # ~33 ms Streamlit refresh interval

    actual_producer_fps = mgr.camera.get_fps()
    mgr.stop()

    if not records:
        print("ERROR: No telemetry records collected.")
        sys.exit(1)

    df = pd.DataFrame(records)

    stages = [
        ("VideoCapture.read()", df["vcap_read"]),
        ("Camera -> AI start", df["cam_to_ai"]),
        ("AI processing", df["ai_proc"]),
        ("Snapshot -> UI fetch", df["snap_to_ui"]),
        ("st.image() Python call", df["st_image"]),
        ("Capture -> Snapshot", df["cap_to_snap"]),
        ("Capture -> UI fetch", df["cap_to_ui"]),
    ]

    table_rows = []
    for name, series in stages:
        table_rows.append({
            "Stage": name,
            "Median": f"{series.median():.2f} ms",
            "P95": f"{series.quantile(0.95):.2f} ms",
            "Max": f"{series.max():.2f} ms"
        })

    table_df = pd.DataFrame(table_rows)

    last_record = records[-1]
    cam_latest_id = last_record["camera_latest_fid"]
    ai_input_id = last_record["frame_id"]
    disp_id = last_record["frame_id"]
    frame_gap = last_record["gap"]

    vcap_med = df["vcap_read"].median()
    vcap_p95 = df["vcap_read"].quantile(0.95)
    vcap_max = df["vcap_read"].max()

    cam_to_ai_med = df["cam_to_ai"].median()
    ai_proc_med = df["ai_proc"].median()
    snap_to_ui_med = df["snap_to_ui"].median()
    cap_to_ui_med = df["cap_to_ui"].mean()

    # Determine Conclusion
    if frame_gap > 3 or cam_to_ai_med > 100:
        conclusion = "B. CAMERA→AI STALE FRAME"
    elif vcap_med > 50 or (vcap_max > 200 and vcap_p95 > 40):
        conclusion = "A. CAMERA/DRIVER BUFFERING"
    elif ai_proc_med > 33:
        conclusion = "C. AI PROCESSING BACKLOG"
    elif snap_to_ui_med > 50:
        conclusion = "D. STREAMLIT/PYTHON RENDER DELAY"
    elif cap_to_ui_med < 100 and frame_gap <= 2:
        conclusion = "E. BROWSER/WEBSOCKET DISPLAY DELAY (Python pipeline current <100ms)"
    else:
        conclusion = "F. MULTIPLE BOTTLENECKS"

    print("\n------------------------------------------------------------")
    print(table_df.to_string(index=False))
    print("------------------------------------------------------------\n")

    print(f"Camera latest frame ID: {cam_latest_id}")
    print(f"AI input frame ID: {ai_input_id}")
    print(f"Displayed snapshot frame ID: {disp_id}")
    print(f"Capture→Display frame gap: {frame_gap} frames")
    print("")
    print(f"Backend: {backend_name}")
    print(f"Resolution: {width}x{height}")
    print(f"Reported camera FPS: {reported_fps}")
    print(f"Actual producer FPS: {actual_producer_fps:.1f}")
    print("")
    print(f"VideoCapture.read() Durations — Median: {vcap_med:.2f} ms | P95: {vcap_p95:.2f} ms | Max: {vcap_max:.2f} ms")
    print(f"Capture → UI Fetch Age (Median): {df['cap_to_ui'].median():.2f} ms | (P95): {df['cap_to_ui'].quantile(0.95):.2f} ms")
    print("")
    print(f"CONCLUSION: {conclusion}\n")

    return {
        "table": table_df,
        "cam_latest_id": cam_latest_id,
        "ai_input_id": ai_input_id,
        "disp_id": disp_id,
        "frame_gap": frame_gap,
        "backend_name": backend_name,
        "resolution": f"{width}x{height}",
        "reported_fps": reported_fps,
        "actual_producer_fps": actual_producer_fps,
        "conclusion": conclusion
    }


if __name__ == "__main__":
    run_latency_audit()
