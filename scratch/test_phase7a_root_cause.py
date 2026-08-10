"""
PHASE 7A — Root Cause Verification & Continuous Telemetry/Video Test Script
"""

import sys
import time
import pathlib

ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboard.components.camera_manager import DashboardCameraManager
from dashboard.components.mjpeg_server import start_mjpeg_stream_server

def main():
    print("=" * 70)
    print("PHASE 7A — CONTINUOUS VIDEO & TELEMETRY ADVANCEMENT AUDIT")
    print("=" * 70)

    mgr = DashboardCameraManager()
    started = mgr.start()
    if not started:
        print("ERROR: Failed to start DashboardCameraManager")
        sys.exit(1)

    port = start_mjpeg_stream_server(mgr, port=8089)
    print(f"MJPEG server running on port {port}")

    print("Warming up camera & AI worker loop (2 seconds)...")
    time.sleep(2.0)

    samples = []
    print("\nTracing 30 samples at 0.1s intervals (10 Hz telemetry tier):")
    print(f"{'Sample':<7} | {'Cam ID':<8} | {'Raw ID':<8} | {'MP ID':<8} | {'Snap ID':<8} | {'EAR':<6} | {'MAR':<6} | {'Pitch':<7} | {'Backlog':<7}")
    print("-" * 85)

    for i in range(1, 31):
        time.sleep(0.1)
        snap = mgr.get_latest_snapshot()
        raw_frame, raw_id = mgr.get_latest_raw_frame()
        cam_id = mgr.camera.total_frames_captured
        mp_id = getattr(snap, "frame_id", 0) if snap else 0
        snap_id = getattr(snap, "frame_id", 0) if snap else 0

        telemetry = snap.telemetry if snap else {}
        ear = telemetry.get("avg_ear")
        mar = telemetry.get("mar")
        pitch = telemetry.get("head_pose_pitch")

        backlog = cam_id - snap_id if cam_id and snap_id else 0

        samples.append({
            "cam_id": cam_id,
            "raw_id": raw_id,
            "mp_id": mp_id,
            "snap_id": snap_id,
            "backlog": backlog
        })

        ear_str = f"{ear:.3f}" if ear is not None else "N/A"
        mar_str = f"{mar:.3f}" if mar is not None else "N/A"
        pitch_str = f"{pitch:+.1f}°" if pitch is not None else "N/A"

        print(f"#{i:02d}    | #{cam_id:<7} | #{raw_id:<7} | #{mp_id:<7} | #{snap_id:<7} | {ear_str:<6} | {mar_str:<6} | {pitch_str:<7} | {backlog:<7}")

    mgr.stop()
    print("-" * 85)

    cam_ids = [s["cam_id"] for s in samples]
    raw_ids = [s["raw_id"] for s in samples]
    mp_ids = [s["mp_id"] for s in samples]
    snap_ids = [s["snap_id"] for s in samples]
    backlogs = [s["backlog"] for s in samples]

    cam_advancing = cam_ids[-1] > cam_ids[0]
    raw_advancing = raw_ids[-1] > raw_ids[0]
    mp_advancing = mp_ids[-1] > mp_ids[0]
    snap_advancing = snap_ids[-1] > snap_ids[0]
    max_backlog = max(backlogs)

    print("\n==================================================")
    print("PHASE 7A ROOT-CAUSE AUDIT RESULTS")
    print("==================================================")
    print(f"CAMERA_FRAME_ID_ADVANCING:   {cam_advancing} (#{cam_ids[0]} -> #{cam_ids[-1]})")
    print(f"LATEST_RAW_FRAME_ID_ADVANCING: {raw_advancing} (#{raw_ids[0]} -> #{raw_ids[-1]})")
    print(f"MEDIAPIPE_FRAME_ID_ADVANCING: {mp_advancing} (#{mp_ids[0]} -> #{mp_ids[-1]})")
    print(f"SNAPSHOT_FRAME_ID_ADVANCING:  {snap_advancing} (#{snap_ids[0]} -> #{snap_ids[-1]})")
    print(f"MAXIMUM_FRAME_BACKLOG:        {max_backlog} frames (Target: < 3 frames)")

    if cam_advancing and raw_advancing and mp_advancing and snap_advancing and max_backlog <= 3:
        print("\nPHASE_7A_VERIFICATION: PASS")
    else:
        print("\nPHASE_7A_VERIFICATION: FAIL")

if __name__ == "__main__":
    main()
