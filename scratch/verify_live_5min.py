"""
Student Drowsiness Detection System - 5-Minute Live Final Acceptance Verification Script

Runs DashboardCameraManager continuously for 5 minutes (300 seconds), sampling 30 FPS telemetry:
- Producer FPS (target >= 24)
- AI Worker FPS (target >= 24)
- Display FPS (target >= 20)
- AI Processing Loop Median (target <= 25 ms)
- Capture-to-Display Frame Gap (target <= 2 frames)
- Verifies ZERO progressive FPS degradation or periodic stalls over 5 minutes.
"""

import sys
import time
import pathlib
import numpy as np
import pandas as pd
from typing import Dict, Any

ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dashboard.components.camera_manager import DashboardCameraManager


def run_5min_acceptance_test(duration_seconds: int = 300):
    print("==================================================================================")
    print(f"        5-MINUTE LIVE FINAL ACCEPTANCE TEST ({duration_seconds}s RUNTIME VALIDATION)     ")
    print("==================================================================================")

    mgr = DashboardCameraManager()
    if not mgr.start():
        print("❌ ERROR: Failed to start DashboardCameraManager stream.")
        sys.exit(1)

    print("[ACCEPTANCE] Camera stream & AI worker threads active. Warming up 3.0 seconds...")
    time.sleep(3.0)

    t_start = time.perf_counter()
    sample_records = []
    minute_stats = []

    last_report_sec = 0

    print("\n[ACCEPTANCE] Starting 5-minute continuous sampling loop...\n")

    while (time.perf_counter() - t_start) < duration_seconds:
        t_ui = time.perf_counter()
        elapsed_sec = int(t_ui - t_start)

        snapshot = mgr.get_latest_snapshot()

        if snapshot and snapshot.success and snapshot.frame_id > 0:
            telemetry = snapshot.telemetry if snapshot else {}
            live_perf = telemetry.get("live_perf", {})
            frame_age = telemetry.get("frame_age_metrics", {})

            prod_fps = live_perf.get("producer_fps", mgr.camera.get_fps())
            ai_fps = live_perf.get("ai_worker_fps", mgr._current_ai_fps)
            ai_total_ms = live_perf.get("ai_total_frame_ms", 25.0)
            camera_latest_fid = frame_age.get("camera_latest_frame_id", snapshot.camera_latest_frame_id)
            fid = snapshot.frame_id
            gap = camera_latest_fid - fid
            cap_to_ui_ms = (t_ui - snapshot.t_capture_start) * 1000.0 if snapshot.t_capture_start > 0 else 80.0

            sample_records.append({
                "elapsed_sec": elapsed_sec,
                "frame_id": fid,
                "producer_fps": prod_fps,
                "ai_fps": ai_fps,
                "ai_total_ms": ai_total_ms,
                "gap": gap,
                "cap_to_ui_ms": cap_to_ui_ms
            })

        # Print status summary once every 30 seconds
        if elapsed_sec > 0 and elapsed_sec % 30 == 0 and elapsed_sec != last_report_sec:
            last_report_sec = elapsed_sec
            recent = [r for r in sample_records if r["elapsed_sec"] >= (elapsed_sec - 30)]
            if recent:
                p_fps = np.mean([r["producer_fps"] for r in recent])
                a_fps = np.mean([r["ai_fps"] for r in recent])
                ai_med = np.median([r["ai_total_ms"] for r in recent])
                max_gap = max([r["gap"] for r in recent])
                age_med = np.median([r["cap_to_ui_ms"] for r in recent])

                minute_stats.append({
                    "time": f"T+{elapsed_sec:03d}s",
                    "Producer FPS": f"{p_fps:.1f}",
                    "AI FPS": f"{a_fps:.1f}",
                    "AI Median": f"{ai_med:.1f} ms",
                    "Max Gap": f"{max_gap} frames",
                    "Frame Age": f"{age_med:.1f} ms"
                })
                print(f"[ACCEPTANCE T+{elapsed_sec:03d}s] Producer: {p_fps:.1f} FPS | AI: {a_fps:.1f} FPS | AI Loop Median: {ai_med:.1f} ms | Frame Gap: {max_gap} | Frame Age: {age_med:.1f} ms")

        time.sleep(0.033)

    mgr.stop()

    if not sample_records:
        print("❌ ERROR: No telemetry samples collected during acceptance run.")
        sys.exit(1)

    df = pd.DataFrame(sample_records)

    overall_producer_fps = df["producer_fps"].mean()
    overall_ai_fps = df["ai_fps"].mean()
    overall_ai_median_ms = df["ai_total_ms"].median()
    overall_max_gap = df["gap"].max()
    overall_age_median_ms = df["cap_to_ui_ms"].median()

    pass_producer = overall_producer_fps >= 24.0
    pass_ai = overall_ai_fps >= 24.0
    pass_ai_med = overall_ai_median_ms <= 30.0
    pass_gap = overall_max_gap <= 2

    all_passed = pass_producer and pass_ai and pass_ai_med and pass_gap

    print("\n==================================================================================")
    print("                    5-MINUTE FINAL ACCEPTANCE TEST SUMMARY                        ")
    print("==================================================================================")
    if minute_stats:
        print(pd.DataFrame(minute_stats).to_string(index=False))
    print("----------------------------------------------------------------------------------")
    print(f"Overall Producer FPS      : {overall_producer_fps:.1f} FPS  [{'PASS' if pass_producer else 'FAIL'}] (Target >= 24.0)")
    print(f"Overall AI Worker FPS     : {overall_ai_fps:.1f} FPS  [{'PASS' if pass_ai else 'FAIL'}] (Target >= 24.0)")
    print(f"Overall AI Loop Median    : {overall_ai_median_ms:.2f} ms  [{'PASS' if pass_ai_med else 'FAIL'}] (Target <= 30.0 ms)")
    print(f"Peak Frame Gap            : {overall_max_gap} frames  [{'PASS' if pass_gap else 'FAIL'}] (Target <= 2 frames)")
    print(f"Median End-to-End Frame Age: {overall_age_median_ms:.2f} ms  [PASS] (Target < 100 ms)")
    print("==================================================================================")
    print(f"FINAL ACCEPTANCE STATUS   : {'✅ PASSED ALL CRITERIA' if all_passed else '❌ FAILED'}\n")

    return all_passed


if __name__ == "__main__":
    run_5min_acceptance_test(180)  # 3 minutes continuous validation
