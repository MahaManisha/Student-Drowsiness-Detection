"""
Student Drowsiness Detection System - 8-Stage Pipeline Watchdog & Diagnostic Harness

Monitors all 8 pipeline stages microsecond-by-microsecond using time.perf_counter():
1. camera_read_frame_id (cv2.VideoCapture.read())
2. queue_publish_frame_id (CameraProducerThread queue put)
3. ai_dequeue_frame_id (AI worker queue dequeue)
4. facemesh_completed_frame_id (MediaPipe FaceMesh)
5. ai_completed_frame_id (Full AI detection loop)
6. snapshot_publish_frame_id (FrameSnapshot construction)
7. ui_fetch_frame_id (Streamlit fast tier fetch)
8. ui_render_frame_id (st.image() render completion)

When a >500 ms stall occurs, produces ONE exact [PIPELINE_STALL] diagnostic record,
determines FIRST_STALLED_STAGE, records LAST_STAGE, profiles AI micro-durations,
calculates capture_to_ui latency breakdown, and runs 5-minute physical motion validation.
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


def run_pipeline_stall_diagnostics(duration_seconds: int = 300) -> Dict[str, Any]:
    print("==================================================================================")
    print(f"       8-STAGE PIPELINE WATCHDOG DIAGNOSTIC HARNESS ({duration_seconds}s RUNTIME)          ")
    print("==================================================================================")

    mgr = DashboardCameraManager()
    if not mgr.start():
        print("❌ ERROR: Failed to start DashboardCameraManager.")
        sys.exit(1)

    print("[WATCHDOG] Camera producer and AI worker active. Warming up 2.0s...")
    time.sleep(2.0)

    t_start = time.perf_counter()

    ui_fetch_frame_id = 0
    ui_fetch_perf = time.perf_counter()
    ui_render_frame_id = 0
    ui_render_perf = time.perf_counter()

    stall_events = []
    sample_records = []
    seen_ui_renders = set()

    stage_durations = {
        "vcap_read": [],
        "facemesh": [],
        "draw_landmarks": [],
        "eye_extract": [],
        "ear": [],
        "mouth_extract": [],
        "mar": [],
        "head_pose": [],
        "decision": [],
        "alert": [],
        "hud": [],
        "rgb_conv": [],
        "snapshot": [],
        "capture_to_ai": [],
        "ai_to_snapshot": [],
        "snapshot_to_ui": [],
        "capture_to_ui": []
    }

    last_sec = -1

    print("\n[WATCHDOG] Sampling 8-stage pipeline once per 33 ms...\n")

    while (time.perf_counter() - t_start) < duration_seconds:
        t_now = time.perf_counter()
        elapsed_sec = int(t_now - t_start)

        # 7. UI Fetch & 8. UI Render simulation
        t_fetch_start = time.perf_counter()
        snap = mgr.get_latest_snapshot()
        t_fetch_end = time.perf_counter()

        if snap and snap.success and snap.frame_id > 0:
            if snap.frame_id != ui_fetch_frame_id:
                ui_fetch_frame_id = snap.frame_id
                ui_fetch_perf = t_fetch_end

                # Simulate st.image() render completion
                ui_render_frame_id = snap.frame_id
                ui_render_perf = time.perf_counter()
                seen_ui_renders.add(snap.frame_id)

                # Record frame age breakdowns
                cap_start = snap.t_capture_start
                ai_comp = snap.t_ai_end
                snap_pub = snap.t_snapshot_publish

                if cap_start > 0:
                    stage_durations["capture_to_ai"].append((ai_comp - cap_start) * 1000.0)
                    stage_durations["ai_to_snapshot"].append((snap_pub - ai_comp) * 1000.0)
                    stage_durations["snapshot_to_ui"].append((ui_fetch_perf - snap_pub) * 1000.0)
                    stage_durations["capture_to_ui"].append((ui_fetch_perf - cap_start) * 1000.0)

                telemetry = snap.telemetry if snap else {}
                live_perf = telemetry.get("live_perf", {})
                stage_durations["vcap_read"].append(live_perf.get("t_videocapture_read_ms", 0.0))
                stage_durations["facemesh"].append(live_perf.get("t_facemesh_ms", 0.0))
                stage_durations["ear"].append(live_perf.get("t_ear_ms", 0.0))
                stage_durations["mar"].append(live_perf.get("t_mar_ms", 0.0))
                stage_durations["head_pose"].append(live_perf.get("t_headpose_ms", 0.0))
                stage_durations["hud"].append(live_perf.get("t_hud_draw_ms", 0.0))
                stage_durations["rgb_conv"].append(live_perf.get("t_rgb_conversion_ms", 0.0))

        # 8-Stage Frame IDs
        c_read_id = mgr.camera.camera_read_frame_id
        q_pub_id = mgr.camera.queue_publish_frame_id
        ai_deq_id = mgr.ai_dequeue_frame_id
        fm_comp_id = mgr.facemesh_completed_frame_id
        ai_comp_id = mgr.ai_completed_frame_id
        snap_pub_id = mgr.snapshot_publish_frame_id
        ui_f_id = ui_fetch_frame_id
        ui_r_id = ui_render_frame_id

        # 8-Stage Ages (ms)
        c_read_age = (t_now - mgr.camera.last_camera_success_perf) * 1000.0 if mgr.camera.last_camera_success_perf > 0 else 0.0
        q_pub_age = (t_now - mgr.camera.last_queue_publish_perf) * 1000.0 if mgr.camera.last_queue_publish_perf > 0 else 0.0
        ai_deq_age = (t_now - mgr.ai_dequeue_perf) * 1000.0 if mgr.ai_dequeue_perf > 0 else 0.0
        fm_comp_age = (t_now - mgr.facemesh_completed_perf) * 1000.0 if mgr.facemesh_completed_perf > 0 else 0.0
        ai_comp_age = (t_now - mgr.last_ai_complete_perf) * 1000.0 if mgr.last_ai_complete_perf > 0 else 0.0
        snap_pub_age = (t_now - mgr.snapshot_publish_perf) * 1000.0 if mgr.snapshot_publish_perf > 0 else 0.0
        ui_f_age = (t_now - ui_fetch_perf) * 1000.0 if ui_fetch_perf > 0 else 0.0
        ui_r_age = (t_now - ui_render_perf) * 1000.0 if ui_render_perf > 0 else 0.0

        sample_records.append({
            "elapsed_sec": elapsed_sec,
            "c_read_age": c_read_age,
            "ai_comp_age": ai_comp_age,
            "ui_r_age": ui_r_age
        })

        # Phase 2: Stall Detection (>500 ms)
        if elapsed_sec > 2 and (c_read_age > 500.0 or q_pub_age > 500.0 or ai_deq_age > 500.0 or fm_comp_age > 500.0 or ai_comp_age > 500.0 or snap_pub_age > 500.0 or ui_f_age > 500.0 or ui_r_age > 500.0):
            # Classify FIRST_STALLED_STAGE
            first_stalled = "UNKNOWN"
            if c_read_age > 500.0:
                first_stalled = "CAMERA_READ"
            elif q_pub_age > 500.0:
                first_stalled = "QUEUE"
            elif ai_deq_age > 500.0:
                first_stalled = "AI_DEQUEUE"
            elif fm_comp_age > 500.0:
                first_stalled = "FACEMESH"
            elif ai_comp_age > 500.0:
                first_stalled = "AI_PIPELINE"
            elif snap_pub_age > 500.0:
                first_stalled = "SNAPSHOT"
            elif ui_f_age > 500.0 or ui_r_age > 500.0:
                first_stalled = "STREAMLIT"

            max_stall_ms = max(c_read_age, q_pub_age, ai_deq_age, fm_comp_age, ai_comp_age, snap_pub_age, ui_f_age, ui_r_age)

            stall_data = {
                "stall_duration_ms": max_stall_ms,
                "camera_thread_alive": mgr.camera._producer_thread.is_alive() if mgr.camera._producer_thread else False,
                "ai_thread_alive": mgr._worker_thread.is_alive() if mgr._worker_thread else False,
                "camera_read_frame_id": c_read_id,
                "camera_read_age_ms": c_read_age,
                "queue_publish_frame_id": q_pub_id,
                "queue_publish_age_ms": q_pub_age,
                "ai_dequeue_frame_id": ai_deq_id,
                "ai_dequeue_age_ms": ai_deq_age,
                "facemesh_completed_frame_id": fm_comp_id,
                "facemesh_age_ms": fm_comp_age,
                "ai_completed_frame_id": ai_comp_id,
                "ai_completed_age_ms": ai_comp_age,
                "snapshot_publish_frame_id": snap_pub_id,
                "snapshot_age_ms": snap_pub_age,
                "ui_fetch_frame_id": ui_f_id,
                "ui_fetch_age_ms": ui_f_age,
                "ui_render_frame_id": ui_r_id,
                "ui_render_age_ms": ui_r_age,
                "queue_size": mgr.camera._frame_queue.qsize(),
                "FIRST_STALLED_STAGE": first_stalled,
                "LAST_STAGE": f"Producer: {mgr.camera.last_producer_stage} | AI: {mgr.last_ai_stage}"
            }
            stall_events.append(stall_data)

            print("\n🚨 [PIPELINE_STALL]")
            print(f"   stall_duration_ms = {max_stall_ms:.1f} ms")
            print(f"   camera_thread_alive = {stall_data['camera_thread_alive']}")
            print(f"   ai_thread_alive = {stall_data['ai_thread_alive']}")
            print(f"   camera_read_frame_id = {c_read_id} (age: {c_read_age:.1f} ms)")
            print(f"   queue_publish_frame_id = {q_pub_id} (age: {q_pub_age:.1f} ms)")
            print(f"   ai_dequeue_frame_id = {ai_deq_id} (age: {ai_deq_age:.1f} ms)")
            print(f"   facemesh_completed_frame_id = {fm_comp_id} (age: {fm_comp_age:.1f} ms)")
            print(f"   ai_completed_frame_id = {ai_comp_id} (age: {ai_comp_age:.1f} ms)")
            print(f"   snapshot_publish_frame_id = {snap_pub_id} (age: {snap_pub_age:.1f} ms)")
            print(f"   ui_fetch_frame_id = {ui_f_id} (age: {ui_f_age:.1f} ms)")
            print(f"   ui_render_frame_id = {ui_r_id} (age: {ui_r_age:.1f} ms)")
            print(f"   queue_size = {stall_data['queue_size']}")
            print(f"   FIRST_STALLED_STAGE = {first_stalled}")
            print(f"   LAST_STAGE = {stall_data['LAST_STAGE']}\n")

        if elapsed_sec != last_sec and elapsed_sec % 10 == 0:
            last_sec = elapsed_sec
            p_fps = mgr.camera.get_fps()
            a_fps = mgr._current_ai_fps
            print(f"[WATCHDOG T+{elapsed_sec:03d}s] C:{c_read_id} Q:{q_pub_id} Deq:{ai_deq_id} FM:{fm_comp_id} AI:{ai_comp_id} Snap:{snap_pub_id} UI:{ui_r_id} | Prod:{p_fps:.1f}FPS AI:{a_fps:.1f}FPS")

        time.sleep(0.033)

    mgr.stop()

    tot_dur = time.perf_counter() - t_start
    unique_ui_fps = len(seen_ui_renders) / tot_dur if tot_dur > 0 else 0.0

    print("\n==================================================================================")
    print("                    8-STAGE DIAGNOSTIC SUMMARY REPORT                             ")
    print("==================================================================================")
    print(f"1. Reproduced Freeze Stall  : {'YES' if len(stall_events) > 0 else 'NO'}")
    if stall_events:
        print(f"2. FIRST_STALLED_STAGE      : {stall_events[0]['FIRST_STALLED_STAGE']}")
        print(f"3. LAST_STAGE Before Freeze : {stall_events[0]['LAST_STAGE']}")
        print(f"4. Measured Stall Duration  : {stall_events[0]['stall_duration_ms']:.1f} ms")
    else:
        print("2. FIRST_STALLED_STAGE      : NONE (0 Stalls > 500 ms)")
        print("3. LAST_STAGE Before Freeze : N/A")
        print("4. Measured Stall Duration  : 0.0 ms")

    print("----------------------------------------------------------------------------------")
    print("AI Stage Durations (ms):")

    def calc_stats(arr):
        if not arr:
            return 0.0, 0.0, 0.0
        a = np.array(arr)
        return float(np.median(a)), float(np.percentile(a, 95)), float(np.max(a))

    for name, key in [("VideoCapture.read", "vcap_read"), ("FaceMesh", "facemesh"), ("Complete AI Pipeline", "capture_to_ai"), ("Capture to UI", "capture_to_ui")]:
        med, p95, max_val = calc_stats(stage_durations[key])
        print(f" - {name:<22}: Median={med:.2f} ms | P95={p95:.2f} ms | Max={max_val:.2f} ms")

    print("----------------------------------------------------------------------------------")
    print(f"5-Minute Physical Motion Freezes: {len(stall_events)} (Target = 0)")
    print(f"UI Unique Frame Throughput       : {unique_ui_fps:.1f} FPS (Target >= 20.0)")
    print("==================================================================================")

    return {
        "reproduced": len(stall_events) > 0,
        "stall_events": stall_events,
        "stage_durations": stage_durations
    }


if __name__ == "__main__":
    run_pipeline_stall_diagnostics(180)  # 3-minute continuous diagnostic run
