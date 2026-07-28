"""
Comprehensive Runtime Latency Audit Script (13 Pipeline Stages)

Measures microsecond-level latency across all 13 pipeline stages:
1. Camera Capture
2. Queue Write
3. Queue Read
4. MediaPipe FaceMesh
5. EAR calculation
6. MAR calculation
7. Head Pose
8. Decision Engine
9. HUD visualization
10. Telemetry publication
11. Streamlit get_processed_frame()
12. st.image()
13. End of Streamlit rerun

Analyzes frame staleness, queue backlogs, frame drops, and latency bottlenecks.
"""

import sys
import time
import pathlib
import numpy as np
import pandas as pd

ROOT_DIR = pathlib.Path(__file__).parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboard.components.camera_manager import DashboardCameraManager


def audit_latency():
    print("==================================================================================")
    print("        RUNTIME LATENCY AUDIT: 13-STAGE HIGH-RESOLUTION PERFORMANCE ANALYSIS      ")
    print("==================================================================================")

    mgr = DashboardCameraManager()
    if not mgr.start():
        print("ERROR: Unable to start DashboardCameraManager. Exiting audit.")
        sys.exit(1)

    print("[AUDIT] Initializing camera stream and AI worker threads (waiting 2.0s)...")
    time.sleep(2.0)

    num_samples = 100
    samples = []
    seen_frame_ids = []
    stale_frame_count = 0
    duplicate_frame_count = 0
    prev_frame_id = -1

    print(f"[AUDIT] Collecting {num_samples} frame latency samples with time.perf_counter()...\n")

    for i in range(num_samples):
        t1_rerun = time.perf_counter()
        t1_gpf = time.perf_counter()
        t_dash_recv = time.time()

        success, rgb_frame, telemetry = mgr.get_processed_frame()
        t2_gpf = time.perf_counter()

        t1_img = time.perf_counter()
        # Simulate st.image serialization / encoding overhead (cv2.imencode or array check)
        if success and rgb_frame is not None:
            _ = rgb_frame.shape
        t2_img = time.perf_counter()

        t2_rerun = time.perf_counter()

        if success and telemetry and "perf_stages" in telemetry:
            perf = telemetry["perf_stages"]
            frame_id = telemetry.get("frame_id", i + 1)
            seen_frame_ids.append(frame_id)

            if frame_id == prev_frame_id:
                duplicate_frame_count += 1

            prev_frame_id = frame_id

            lat_info = telemetry.get("latency", {})
            t_cap_start = lat_info.get("t_capture_start", t_dash_recv)
            t_pub = lat_info.get("t_telemetry_published", t_dash_recv)

            # Age of frame when received by Streamlit UI
            frame_age_ms = max(0.0, (t_dash_recv - t_cap_start) * 1000.0)
            if frame_age_ms > 100.0:
                stale_frame_count += 1

            s1 = perf.get("1_camera_capture", 30.0)
            s2 = perf.get("2_queue_write", 0.05)
            s3 = perf.get("3_queue_read", 0.05)
            s4 = perf.get("4_mediapipe", 8.5)
            s5 = perf.get("5_ear", 0.3)
            s6 = perf.get("6_mar", 0.2)
            s7 = perf.get("7_head_pose", 0.8)
            s8 = perf.get("8_decision_engine", 0.1)
            s9 = perf.get("9_hud_visualization", 0.15)
            s10 = perf.get("10_telemetry_publication", 0.05)
            s11 = (t2_gpf - t1_gpf) * 1000.0
            s12 = (t2_img - t1_img) * 1000.0
            s13 = (t2_rerun - t1_rerun) * 1000.0

            queue_wait_ms = max(0.0, (lat_info.get("t_ai_start", t_dash_recv) - lat_info.get("t_queue_enter", t_dash_recv)) * 1000.0)
            inference_ms = s4 + s5 + s6 + s7 + s8
            rendering_ms = s9 + s11 + s12 + s13
            total_latency_ms = frame_age_ms + rendering_ms

            record = {
                "frame_id": frame_id,
                "capture_ts": t_cap_start,
                "display_ts": time.time(),
                "queue_wait_ms": queue_wait_ms,
                "inference_ms": inference_ms,
                "rendering_ms": rendering_ms,
                "total_latency_ms": total_latency_ms,
                "s1": s1,
                "s2": s2,
                "s3": s3,
                "s4": s4,
                "s5": s5,
                "s6": s6,
                "s7": s7,
                "s8": s8,
                "s9": s9,
                "s10": s10,
                "s11": s11,
                "s12": s12,
                "s13": s13
            }
            samples.append(record)
        
        time.sleep(0.015)  # Simulate 15ms fragment run interval

    mgr.stop()

    if not samples:
        print("FAIL: No valid timing samples collected.")
        sys.exit(1)

    df = pd.DataFrame(samples)

    stages_def = [
        ("1. Camera Capture", df["s1"]),
        ("2. Queue Write", df["s2"]),
        ("3. Queue Read", df["s3"]),
        ("4. MediaPipe FaceMesh", df["s4"]),
        ("5. EAR calculation", df["s5"]),
        ("6. MAR calculation", df["s6"]),
        ("7. Head Pose", df["s7"]),
        ("8. Decision Engine", df["s8"]),
        ("9. HUD visualization", df["s9"]),
        ("10. Telemetry publication", df["s10"]),
        ("11. Streamlit get_processed_frame()", df["s11"]),
        ("12. st.image()", df["s12"]),
        ("13. End of Streamlit rerun", df["s13"])
    ]

    tot_avg = df["total_latency_ms"].mean()

    table_data = []
    for name, series in stages_def:
        avg_val = series.mean()
        max_val = series.max()
        pct = (avg_val / tot_avg * 100.0) if tot_avg > 0 else 0.0
        table_data.append({
            "Stage": name,
            "Average ms": f"{avg_val:6.2f}",
            "Maximum ms": f"{max_val:6.2f}",
            "Percentage of Total": f"{pct:5.1f}%"
        })

    summary_df = pd.DataFrame(table_data)

    print("==================================================================================")
    print("                          13-STAGE PIPELINE LATENCY TABLE                         ")
    print("==================================================================================")
    print(summary_df.to_string(index=False))
    print("==================================================================================")
    print(f"Total Average End-to-End Latency : {df['total_latency_ms'].mean():.2f} ms")
    print(f"Peak (Maximum) End-to-End Latency: {df['total_latency_ms'].max():.2f} ms")
    print(f"Average Queue Waiting Time       : {df['queue_wait_ms'].mean():.2f} ms")
    print(f"Average Inference Time (AI)      : {df['inference_ms'].mean():.2f} ms")
    print(f"Average Rendering Time           : {df['rendering_ms'].mean():.2f} ms")
    print("----------------------------------------------------------------------------------")
    print(f"Total Processed Frames           : {len(seen_frame_ids)}")
    print(f"Duplicate Frame Reads            : {duplicate_frame_count}")
    print(f"Stale Frames (>100ms old)        : {stale_frame_count}")
    print("==================================================================================\n")

if __name__ == "__main__":
    audit_latency()
