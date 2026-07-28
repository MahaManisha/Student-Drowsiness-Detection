"""
Latency Stage Verification Script
Measures and validates camera-to-dashboard latency across all 8 pipeline stages.
"""

import time
import cv2
import sys
import pathlib
import numpy as np

# Ensure root directory is on sys.path
ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboard.components.camera_manager import DashboardCameraManager

def run_latency_measurement():
    print("======================================================================")
    print("      REAL-TIME VIDEO PIPELINE STAGE-BY-STAGE LATENCY MEASUREMENT      ")
    print("======================================================================")

    mgr = DashboardCameraManager()
    if not mgr.start():
        print("ERROR: Could not start DashboardCameraManager. Exiting.")
        sys.exit(1)

    print("Waiting 1.5 seconds for camera hardware & AI worker initialization...")
    time.sleep(1.5)

    num_samples = 50
    records = []

    print(f"Collecting {num_samples} frame telemetry timing samples...")

    for i in range(num_samples):
        t_dash_recv = time.time()
        success, frame, telemetry = mgr.get_processed_frame()
        t_render_complete = time.time()

        if success and telemetry and "latency" in telemetry:
            lat = telemetry["latency"]
            t_cap_start = lat["t_capture_start"]
            t_cap_end = lat["t_capture_end"]
            t_pub = lat["t_telemetry_published"]

            cam_buf_ms = lat["camera_buffer_delay_ms"]
            queue_ms = lat["queue_delay_ms"]
            ai_ms = lat["ai_processing_delay_ms"]
            mp_ms = lat["mediapipe_delay_ms"]
            ear_mar_ms = lat["ear_mar_delay_ms"]
            telemetry_ms = max(0.0, (t_dash_recv - t_pub) * 1000.0)
            render_ms = max(0.0, (t_render_complete - t_dash_recv) * 1000.0)
            total_e2e_ms = max(0.0, (t_render_complete - t_cap_start) * 1000.0)

            record = {
                "frame": i + 1,
                "cam_buf": cam_buf_ms,
                "queue": queue_ms,
                "ai": ai_ms,
                "mediapipe": mp_ms,
                "ear_mar": ear_mar_ms,
                "telemetry": telemetry_ms,
                "render": render_ms,
                "total_e2e": total_e2e_ms
            }
            records.append(record)

            print(
                f"Sample #{i+1:02d} | "
                f"CamBuf: {cam_buf_ms:5.2f}ms | "
                f"Queue: {queue_ms:5.2f}ms | "
                f"AI: {ai_ms:5.2f}ms (MP: {mp_ms:5.2f}ms | EAR/MAR: {ear_mar_ms:5.2f}ms) | "
                f"Telem: {telemetry_ms:5.2f}ms | "
                f"Render: {render_ms:5.2f}ms | "
                f"TOTAL E2E: {total_e2e_ms:5.2f}ms"
            )
        else:
            print(f"Sample #{i+1:02d} | No frame received yet.")

        time.sleep(0.033)

    mgr.stop()

    if not records:
        print("FAIL: No valid records captured.")
        sys.exit(1)

    avg_cam_buf = np.mean([r["cam_buf"] for r in records])
    avg_queue = np.mean([r["queue"] for r in records])
    avg_ai = np.mean([r["ai"] for r in records])
    avg_mp = np.mean([r["mediapipe"] for r in records])
    avg_ear_mar = np.mean([r["ear_mar"] for r in records])
    avg_telem = np.mean([r["telemetry"] for r in records])
    avg_render = np.mean([r["render"] for r in records])
    avg_total = np.mean([r["total_e2e"] for r in records])
    max_total = np.max([r["total_e2e"] for r in records])

    print("\n======================================================================")
    print("                    FINAL STAGE-BY-STAGE SUMMARY                      ")
    print("======================================================================")
    print(f"1. Camera Buffer Delay       : {avg_cam_buf:6.2f} ms")
    print(f"2. Queue Delay               : {avg_queue:6.2f} ms")
    print(f"3. AI Processing Delay       : {avg_ai:6.2f} ms")
    print(f"   |- MediaPipe Complete     : {avg_mp:6.2f} ms")
    print(f"   +- EAR / MAR Complete     : {avg_ear_mar:6.2f} ms")
    print(f"4. Telemetry Delay           : {avg_telem:6.2f} ms")
    print(f"5. Dashboard Rendering Delay : {avg_render:6.2f} ms")
    print("----------------------------------------------------------------------")
    print(f"TOTAL AVERAGE END-TO-END LATENCY : {avg_total:6.2f} ms")
    print(f"PEAK (MAX) END-TO-END LATENCY    : {max_total:6.2f} ms")
    print("======================================================================")

    if avg_total < 100.0:
        print(f"SUCCESS: Total latency ({avg_total:.2f} ms) is STRICTLY BELOW target threshold of 100 ms!")
    else:
        print(f"FAILURE: Total latency ({avg_total:.2f} ms) exceeds 100 ms target threshold!")

if __name__ == "__main__":
    run_latency_measurement()
