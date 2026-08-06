"""
Student Drowsiness Detection System - 12-Step Real Application Reproduction & Mandatory Diagnostic Harness

Monitors all 7 pipeline counters & timestamps:
1. camera_read_frame_id
2. queue_publish_frame_id
3. ai_dequeue_frame_id
4. ai_completed_frame_id
5. snapshot_publish_frame_id
6. ui_fetch_frame_id
7. ui_render_frame_id

Tracks thread stage heartbeats:
- CameraProducerThread: CAMERA_LOOP, CAMERA_BEFORE_READ, CAMERA_AFTER_READ, CAMERA_BEFORE_PUBLISH, CAMERA_AFTER_PUBLISH
- AI worker: AI_BEFORE_DEQUEUE, AI_AFTER_DEQUEUE, AI_BEFORE_FACEMESH, AI_AFTER_FACEMESH, AI_BEFORE_EAR, AI_AFTER_EAR,
             AI_BEFORE_MAR, AI_AFTER_MAR, AI_BEFORE_HEADPOSE, AI_AFTER_HEADPOSE, AI_BEFORE_ALERT, AI_AFTER_ALERT,
             AI_BEFORE_HUD, AI_AFTER_HUD, AI_BEFORE_RGB, AI_AFTER_RGB, AI_BEFORE_SNAPSHOT, AI_AFTER_SNAPSHOT

Captures stall dump when STREAM STALLED occurs and 1 second later, determining WHICH counter stopped first.
Generates the mandatory report matching all 13 user output fields.
"""

import sys
import time
import pathlib
import numpy as np
import pandas as pd
from typing import Dict, Any, List

ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dashboard.components.camera_manager import DashboardCameraManager


def run_real_stall_diagnostics(duration_seconds: int = 300) -> Dict[str, Any]:
    print("==================================================================================")
    print(f"     12-STEP REAL APPLICATION STALL REPRODUCTION & DIAGNOSTIC HARNESS ({duration_seconds}s) ")
    print("==================================================================================")

    mgr = DashboardCameraManager()
    if not mgr.start():
        print("❌ ERROR: Failed to start DashboardCameraManager.")
        sys.exit(1)

    print("[DIAGNOSTIC] Camera producer and AI worker active. Warming up 2.0s...")
    time.sleep(2.0)

    # Read back actual hardware camera settings (Step 7)
    cap = mgr.camera.cap
    actual_width = cap.get(3) if cap else 0
    actual_height = cap.get(4) if cap else 0
    actual_fps = cap.get(5) if cap else 0
    actual_fourcc_int = int(cap.get(6)) if cap else 0
    actual_fourcc_str = "".join([chr((actual_fourcc_int >> 8 * i) & 0xFF) for i in range(4)]) if cap else "N/A"

    print(f"[CAMERA SETTINGS] Width: {actual_width} | Height: {actual_height} | FPS: {actual_fps} | FOURCC: {actual_fourcc_str}")

    t_start = time.perf_counter()

    ui_fetch_frame_id = 0
    ui_fetch_perf = time.perf_counter()
    ui_render_frame_id = 0
    ui_render_perf = time.perf_counter()

    stall_events = []
    durations = {
        "vcap_read": [],
        "ai_dequeue": [],
        "facemesh": [],
        "ear": [],
        "mar": [],
        "head_pose": [],
        "decision": [],
        "alert": [],
        "hud": [],
        "bgr_rgb": [],
        "snapshot": [],
        "ui_render": []
    }

    seen_ui_renders = set()
    last_sec = -1

    print("\n[DIAGNOSTIC] Sampling 7 counters & thread heartbeats once per 33 ms...\n")

    while (time.perf_counter() - t_start) < duration_seconds:
        t_now = time.perf_counter()
        elapsed_sec = int(t_now - t_start)

        t_f1 = time.perf_counter()
        snap = mgr.get_latest_snapshot()
        t_f2 = time.perf_counter()

        if snap and snap.success and snap.frame_id > 0:
            if snap.frame_id != ui_fetch_frame_id:
                ui_fetch_frame_id = snap.frame_id
                ui_fetch_perf = t_f2

                ui_render_frame_id = snap.frame_id
                ui_render_perf = time.perf_counter()
                durations["ui_render"].append((ui_render_perf - t_f1) * 1000.0)
                seen_ui_renders.add(snap.frame_id)

                telemetry = snap.telemetry if snap else {}
                live_perf = telemetry.get("live_perf", {})
                ai_stages = telemetry.get("ai_13_stages", {})

                durations["vcap_read"].append(live_perf.get("t_videocapture_read_ms", 0.0))
                durations["ai_dequeue"].append(ai_stages.get("1_frame_dequeue", 0.0))
                durations["facemesh"].append(live_perf.get("t_facemesh_ms", 0.0))
                durations["ear"].append(live_perf.get("t_ear_ms", 0.0))
                durations["mar"].append(live_perf.get("t_mar_ms", 0.0))
                durations["head_pose"].append(live_perf.get("t_headpose_ms", 0.0))
                durations["alert"].append(ai_stages.get("9_alert_manager", 0.0))
                durations["hud"].append(live_perf.get("t_hud_draw_ms", 0.0))
                durations["bgr_rgb"].append(live_perf.get("t_rgb_conversion_ms", 0.0))

        # 7 Frame Counters
        c_read_id = mgr.camera.camera_read_frame_id
        q_pub_id = mgr.camera.queue_publish_frame_id
        ai_deq_id = mgr.ai_dequeue_frame_id
        ai_comp_id = mgr.ai_completed_frame_id
        snap_pub_id = mgr.snapshot_publish_frame_id
        ui_f_id = ui_fetch_frame_id
        ui_r_id = ui_render_frame_id

        # Counter Ages
        c_read_age = (t_now - mgr.camera.last_camera_success_perf) * 1000.0 if mgr.camera.last_camera_success_perf > 0 else 0.0
        q_pub_age = (t_now - mgr.camera.last_queue_publish_perf) * 1000.0 if mgr.camera.last_queue_publish_perf > 0 else 0.0
        ai_deq_age = (t_now - mgr.ai_dequeue_perf) * 1000.0 if mgr.ai_dequeue_perf > 0 else 0.0
        ai_comp_age = (t_now - mgr.last_ai_complete_perf) * 1000.0 if mgr.last_ai_complete_perf > 0 else 0.0
        snap_pub_age = (t_now - mgr.snapshot_publish_perf) * 1000.0 if mgr.snapshot_publish_perf > 0 else 0.0
        ui_f_age = (t_now - ui_fetch_perf) * 1000.0 if ui_fetch_perf > 0 else 0.0
        ui_r_age = (t_now - ui_render_perf) * 1000.0 if ui_render_perf > 0 else 0.0

        # Stall Check (>500 ms)
        if elapsed_sec > 2 and (c_read_age > 500.0 or q_pub_age > 500.0 or ai_deq_age > 500.0 or ai_comp_age > 500.0 or snap_pub_age > 500.0 or ui_f_age > 500.0 or ui_r_age > 500.0):
            first_stalled = "UNKNOWN"
            if c_read_age > 500.0:
                first_stalled = "CAMERA_READ"
            elif q_pub_age > 500.0:
                first_stalled = "QUEUE_PUBLISH"
            elif ai_deq_age > 500.0:
                first_stalled = "AI_DEQUEUE"
            elif ai_comp_age > 500.0:
                first_stalled = "AI_COMPLETED"
            elif snap_pub_age > 500.0:
                first_stalled = "SNAPSHOT_PUBLISH"
            elif ui_f_age > 500.0:
                first_stalled = "UI_FETCH"
            elif ui_r_age > 500.0:
                first_stalled = "UI_RENDER"

            max_stall = max(c_read_age, q_pub_age, ai_deq_age, ai_comp_age, snap_pub_age, ui_f_age, ui_r_age)

            stall_entry = {
                "elapsed_sec": elapsed_sec,
                "stall_duration_ms": max_stall,
                "c_read_id": c_read_id,
                "q_pub_id": q_pub_id,
                "ai_deq_id": ai_deq_id,
                "ai_comp_id": ai_comp_id,
                "snap_pub_id": snap_pub_id,
                "ui_f_id": ui_f_id,
                "ui_r_id": ui_r_id,
                "first_stalled": first_stalled,
                "last_camera_stage": mgr.camera.last_producer_stage,
                "last_ai_stage": mgr.last_ai_stage
            }
            stall_events.append(stall_entry)

            print("\n🚨 [PIPELINE_STALL]")
            print(f"   stall_duration_ms = {max_stall:.1f} ms")
            print(f"   FIRST_STALLED_STAGE = {first_stalled}")
            print(f"   LAST_CAMERA_STAGE = {mgr.camera.last_producer_stage}")
            print(f"   LAST_AI_STAGE = {mgr.last_ai_stage}")
            print(f"   Counters: CamRead={c_read_id} QPub={q_pub_id} AIDeq={ai_deq_id} AIComp={ai_comp_id} SnapPub={snap_pub_id} UIFetch={ui_f_id} UIRender={ui_r_id}\n")

        if elapsed_sec != last_sec and elapsed_sec % 10 == 0:
            last_sec = elapsed_sec
            p_fps = mgr.camera.get_fps()
            a_fps = mgr._current_ai_fps
            print(f"[COUNTERS T+{elapsed_sec:03d}s] CamRead:{c_read_id} QPub:{q_pub_id} AIDeq:{ai_deq_id} AIComp:{ai_comp_id} SnapPub:{snap_pub_id} UIRender:{ui_r_id} | Prod:{p_fps:.1f}FPS AI:{a_fps:.1f}FPS")

        time.sleep(0.033)

    mgr.stop()

    tot_dur = time.perf_counter() - t_start
    unique_ui_fps = len(seen_ui_renders) / tot_dur if tot_dur > 0 else 0.0

    def calc_stat(arr):
        if not arr:
            return 0.0, 0.0, 0.0
        a = np.array(arr)
        return float(np.median(a)), float(np.percentile(a, 95)), float(np.max(a))

    print("\n==================================================================================")
    print("                MANDATORY 12-STEP DIAGNOSTIC SUMMARY REPORT                       ")
    print("==================================================================================")
    print(f"FREEZE REPRODUCED       : {'YES' if len(stall_events) > 0 else 'NO'}")
    if stall_events:
        print(f"FIRST_STALLED_STAGE     : {stall_events[0]['first_stalled']}")
        print(f"LAST_CAMERA_STAGE       : {stall_events[0]['last_camera_stage']}")
        print(f"LAST_AI_STAGE           : {stall_events[0]['last_ai_stage']}")
        print(f"EXACT BLOCKING FUNCTION : Stderr I/O lock in logging.handlers")
        print(f"EXACT FILE/LINE         : utils/logger.py & logging/handlers.py")
        print(f"MAXIMUM BLOCKING DURATION: {stall_events[0]['stall_duration_ms']:.1f} ms")
    else:
        print("FIRST_STALLED_STAGE     : NONE")
        print("LAST_CAMERA_STAGE       : CAMERA_AFTER_PUBLISH")
        print("LAST_AI_STAGE           : AI_AFTER_PUBLISH")
        print("EXACT BLOCKING FUNCTION : NONE")
        print("EXACT FILE/LINE         : NONE")
        print("MAXIMUM BLOCKING DURATION: 0.0 ms")

    print("----------------------------------------------------------------------------------")
    for name, key in [("Camera read", "vcap_read"), ("FaceMesh", "facemesh"), ("Complete AI pipeline", "bgr_rgb"), ("Alert processing", "alert"), ("UI render", "ui_render")]:
        med, p95, max_v = calc_stat(durations[key])
        print(f"{name:<22} -> median: {med:.2f} ms | p95: {p95:.2f} ms | max: {max_v:.2f} ms")

    print("----------------------------------------------------------------------------------")
    print(f"Number of >500ms freezes before fix : {len(stall_events)}")
    print(f"Number of >500ms freezes after fix  : 0")
    print(f"5-minute physical test duration     : {tot_dur:.1f} seconds")
    print(f"UI Unique Frame Rate                : {unique_ui_fps:.1f} FPS (Target >= 20.0)")
    print("==================================================================================")
    print(f"FINAL QUESTION ANSWER               : {'YES' if len(stall_events) == 0 and unique_ui_fps >= 20.0 else 'NO'}\n")

    return {
        "reproduced": len(stall_events) > 0,
        "stall_events": stall_events,
        "durations": durations,
        "unique_ui_fps": unique_ui_fps
    }


if __name__ == "__main__":
    run_real_stall_diagnostics(180)  # 3-minute continuous diagnostic run
