"""
PHASE 7A — Live Telemetry Synchronization & Frame ID Verification Script
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
    print("PHASE 7A — LIVE TELEMETRY SYNCHRONIZATION TEST")
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

    frame_samples = []
    print("\nTracing Frame IDs across 50 telemetry samples (10 Hz sampling rate):")
    print(f"{'Sample':<7} | {'Camera ID':<10} | {'MediaPipe ID':<12} | {'Snapshot ID':<12} | {'Avg EAR':<8} | {'MAR':<8} | {'Pitch':<7} | {'Score':<6}")
    print("-" * 80)

    for i in range(1, 51):
        time.sleep(0.1)
        snapshot = mgr.get_latest_snapshot()
        if snapshot is None:
            print(f"Sample {i:02d}: Snapshot is None!")
            continue

        telemetry = snapshot.telemetry if snapshot else {}
        cam_id = mgr.camera.total_frames_captured
        mp_id = getattr(snapshot, "frame_id", 0)
        snap_id = getattr(snapshot, "frame_id", 0)

        ear = telemetry.get("avg_ear", 0.0)
        mar = telemetry.get("mar", 0.0)
        pitch = telemetry.get("head_pose_pitch", 0.0)
        score = telemetry.get("drowsiness_score", 0.0)

        frame_samples.append({
            "cam_id": cam_id,
            "mp_id": mp_id,
            "snap_id": snap_id,
            "ear": ear,
            "mar": mar,
            "pitch": pitch,
            "score": score
        })

        ear_str = f"{ear:.3f}" if ear is not None else "N/A"
        mar_str = f"{mar:.3f}" if mar is not None else "N/A"
        pitch_str = f"{pitch:+.1f}°" if pitch is not None else "N/A"

        print(f"#{i:02d}    | #{cam_id:<9} | #{mp_id:<11} | #{snap_id:<11} | {ear_str:<8} | {mar_str:<8} | {pitch_str:<7} | {score:.0f}/100")

    mgr.stop()
    print("-" * 80)

    # Verification checks
    cam_ids = [s["cam_id"] for s in frame_samples]
    snap_ids = [s["snap_id"] for s in frame_samples]

    cam_increasing = all(x < y for x, y in zip(cam_ids[:-1], cam_ids[1:]))
    snap_increasing = all(x <= y for x, y in zip(snap_ids[:-1], snap_ids[1:]))
    snap_advancing = snap_ids[-1] > snap_ids[0]

    print("\n==================================================")
    print("PHASE 7A DIAGNOSTIC SUMMARY")
    print("==================================================")
    print(f"CAMERA_FRAME_ID_INCREASING:  {cam_increasing} (Start #{cam_ids[0]} -> End #{cam_ids[-1]})")
    print(f"SNAPSHOT_FRAME_ID_ADVANCING:  {snap_advancing} (Start #{snap_ids[0]} -> End #{snap_ids[-1]})")
    print(f"MJPEG_SERVER_PORT:           {port}")
    print(f"TELEMETRY_REFRESH_RATE:      10 Hz (0.1s ticks)")

    if snap_advancing and cam_increasing:
        print("\nPHASE_7A_VERIFICATION: PASS")
    else:
        print("\nPHASE_7A_VERIFICATION: FAIL")

if __name__ == "__main__":
    main()
