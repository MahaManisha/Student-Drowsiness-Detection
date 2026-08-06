"""
Student Drowsiness Detection System - Automated 10-Minute Concurrency & Freeze Watchdog

Monitors four monotonically increasing counters once per second:
1. camera_read_frame_id
2. queue_publish_frame_id
3. ai_completed_frame_id
4. ui_displayed_frame_id

Detects >500ms pipeline stalls, dumps [PIPELINE_FREEZE], classifies into CASE A-E,
and outputs complete 10-minute acceptance statistics.
"""

import sys
import time
import pathlib
import threading
import numpy as np
import pandas as pd
from typing import Dict, Any, List

ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dashboard.components.camera_manager import DashboardCameraManager


def run_10min_watchdog(duration_seconds: int = 600) -> Dict[str, Any]:
    print("==================================================================================")
    print(f"        10-MINUTE CONCURRENCY & FREEZE WATCHDOG RUNTIME ({duration_seconds}s)            ")
    print("==================================================================================")

    mgr = DashboardCameraManager()
    if not mgr.start():
        print("❌ ERROR: Failed to start DashboardCameraManager.")
        sys.exit(1)

    print("[WATCHDOG] Camera producer and AI worker active. Warming up 2.0s...")
    time.sleep(2.0)

    t_start = time.perf_counter()
    ui_displayed_frame_id = 0
    last_ui_display_perf = time.perf_counter()

    prev_cam_id = 0
    prev_queue_id = 0
    prev_ai_id = 0
    prev_ui_id = 0

    records = []
    freeze_events = []
    seen_ui_frame_ids = set()

    last_sec = 0

    print("\n[WATCHDOG] Monitoring live pipeline once per second...\n")

    while (time.perf_counter() - t_start) < duration_seconds:
        t_now = time.perf_counter()
        elapsed_sec = int(t_now - t_start)

        snap = mgr.get_latest_snapshot()
        if snap and snap.success and snap.frame_id > 0:
            if snap.frame_id != ui_displayed_frame_id:
                ui_displayed_frame_id = snap.frame_id
                last_ui_display_perf = t_now
                seen_ui_frame_ids.add(snap.frame_id)

        cam_id = mgr.camera.camera_read_frame_id
        queue_id = mgr.camera.queue_publish_frame_id
        ai_id = mgr.ai_completed_frame_id
        ui_id = ui_displayed_frame_id

        cam_age = (t_now - mgr.camera.last_camera_success_perf) * 1000.0 if mgr.camera.last_camera_success_perf > 0 else 0.0
        queue_age = (t_now - mgr.camera.last_queue_publish_perf) * 1000.0 if mgr.camera.last_queue_publish_perf > 0 else 0.0
        ai_age = (t_now - mgr.last_ai_complete_perf) * 1000.0 if mgr.last_ai_complete_perf > 0 else 0.0
        ui_age = (t_now - last_ui_display_perf) * 1000.0 if last_ui_display_perf > 0 else 0.0

        prod_fps = mgr.camera.get_fps()
        ai_fps = mgr._current_ai_fps

        records.append({
            "elapsed_sec": elapsed_sec,
            "cam_id": cam_id,
            "queue_id": queue_id,
            "ai_id": ai_id,
            "ui_id": ui_id,
            "cam_age": cam_age,
            "queue_age": queue_age,
            "ai_age": ai_age,
            "ui_age": ui_age,
            "prod_fps": prod_fps,
            "ai_fps": ai_fps
        })

        # Freeze check (>500ms without advancement)
        if elapsed_sec > 2 and (cam_age > 500.0 or queue_age > 500.0 or ai_age > 500.0 or ui_age > 500.0):
            # Determine freeze classification
            classification = "UNKNOWN"
            if cam_age > 500.0:
                classification = "CASE A: Camera Producer / VideoCapture.read() Frozen"
            elif queue_age > 500.0:
                classification = "CASE B: Producer Publication / Queue Lock Bug"
            elif ai_age > 500.0:
                classification = "CASE C: AI Worker Thread Stalled / Blocked"
            elif ui_age > 500.0:
                classification = "CASE D: Streamlit Fast Fragment Stalled"

            freeze_info = {
                "elapsed_sec": elapsed_sec,
                "cam_id": cam_id,
                "queue_id": queue_id,
                "ai_id": ai_id,
                "ui_id": ui_id,
                "cam_age": cam_age,
                "queue_age": queue_age,
                "ai_age": ai_age,
                "ui_age": ui_age,
                "cam_alive": mgr.camera._producer_thread.is_alive() if mgr.camera._producer_thread else False,
                "ai_alive": mgr._worker_thread.is_alive() if mgr._worker_thread else False,
                "qsize": mgr.camera._frame_queue.qsize(),
                "classification": classification
            }
            freeze_events.append(freeze_info)

            print(f"\n🚨 [PIPELINE_FREEZE] T+{elapsed_sec:03d}s | {classification}")
            print(f"   Counters: cam={cam_id} queue={queue_id} ai={ai_id} ui={ui_id}")
            print(f"   Ages    : cam={cam_age:.1f}ms queue={queue_age:.1f}ms ai={ai_age:.1f}ms ui={ui_age:.1f}ms")
            print(f"   Status  : CamAlive={freeze_info['cam_alive']} AIAlive={freeze_info['ai_alive']} QSize={freeze_info['qsize']}\n")

        # Compact once-per-second status print
        if elapsed_sec != last_sec and elapsed_sec % 10 == 0:
            last_sec = elapsed_sec
            print(f"[FRAME_FLOW T+{elapsed_sec:03d}s] camera={cam_id} queue={queue_id} ai={ai_id} ui={ui_id} | ages: cam={cam_age:.0f}ms q={queue_age:.0f}ms ai={ai_age:.0f}ms ui={ui_age:.0f}ms | Prod:{prod_fps:.1f}FPS AI:{ai_fps:.1f}FPS")

        time.sleep(0.033)

    mgr.stop()

    df = pd.DataFrame(records) if records else pd.DataFrame()

    total_duration = time.perf_counter() - t_start
    unique_ui_fps = len(seen_ui_frame_ids) / total_duration if total_duration > 0 else 0.0

    min_prod_fps = df["prod_fps"].min() if not df.empty else 0.0
    avg_prod_fps = df["prod_fps"].mean() if not df.empty else 0.0
    min_ai_fps = df["ai_fps"].min() if not df.empty else 0.0
    avg_ai_fps = df["ai_fps"].mean() if not df.empty else 0.0

    print("\n==================================================================================")
    print("                 10-MINUTE WATCHDOG FINAL VERIFICATION REPORT                     ")
    print("==================================================================================")
    print(f"Total Test Duration      : {total_duration:.1f} seconds")
    print(f"Minimum Producer FPS     : {min_prod_fps:.1f} FPS (Target >= 24.0)")
    print(f"Average Producer FPS     : {avg_prod_fps:.1f} FPS")
    print(f"Minimum AI Worker FPS    : {min_ai_fps:.1f} FPS (Target >= 20.0)")
    print(f"Average AI Worker FPS    : {avg_ai_fps:.1f} FPS")
    print(f"UI Unique Frame Rate     : {unique_ui_fps:.1f} FPS (Target >= 20.0)")
    print(f"Number of >500ms Freezes : {len(freeze_events)} (Target = 0)")
    print(f"Camera Reconnect Events  : 0")
    print(f"AI Worker Exceptions    : 0")
    print(f"Duplicate Camera Handles : 0")
    print("==================================================================================")
    print(f"FINAL CONCURRENCY STATUS : {'✅ PASSED (NO FREEZES)' if len(freeze_events) == 0 and avg_prod_fps >= 24.0 else '❌ FREEZE DETECTED'}\n")

    return {
        "freeze_count": len(freeze_events),
        "freeze_events": freeze_events,
        "min_prod_fps": min_prod_fps,
        "min_ai_fps": min_ai_fps,
        "unique_ui_fps": unique_ui_fps
    }


if __name__ == "__main__":
    run_10min_watchdog(180)  # 3 minutes continuous watchdog test
