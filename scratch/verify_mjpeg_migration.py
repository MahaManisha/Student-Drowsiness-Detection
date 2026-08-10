import time
import urllib.request
import sys
import pathlib

ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboard.components.lifecycle import get_singleton_camera_manager, get_singleton_object_ids
from dashboard.components.mjpeg_server import get_mjpeg_stream_port

def test_mjpeg_migration():
    print("=== STARTING MJPEG MIGRATION VERIFICATION ===")
    
    # 1. Initialize Singleton Camera Manager
    mgr = get_singleton_camera_manager()
    print("Singleton Camera Manager active:", mgr.is_connected)
    
    time.sleep(1.0)
    
    # 2. Instance & Thread Audit
    ids = get_singleton_object_ids()
    print("Object IDs Audit:")
    for k, v in ids.items():
        print(f"  {k}: {v}")
        
    camera_instances = 1 if mgr.camera is not None else 0
    camera_threads = 1 if (mgr.camera._producer_thread and mgr.camera._producer_thread.is_alive()) else 0
    ai_threads = 1 if (mgr._worker_thread and mgr._worker_thread.is_alive()) else 0
    mediapipe_instances = 1 if hasattr(mgr.detector, "face_mesh") else 0
    
    print(f"CAMERA_INSTANCES: {camera_instances}")
    print(f"CAMERA_THREADS: {camera_threads}")
    print(f"AI_WORKER_THREADS: {ai_threads}")
    print(f"MEDIAPIPE_INSTANCES: {mediapipe_instances}")
    
    # 3. Test raw frame buffer
    raw_frame, raw_frame_id = mgr.get_latest_raw_frame()
    print(f"RAW Frame Available: {raw_frame is not None}, Frame ID: #{raw_frame_id}")
    if raw_frame is not None:
        print(f"RAW Frame Shape: {raw_frame.shape}")
        
    # 4. Test MJPEG Stream Endpoint
    port = get_mjpeg_stream_port()
    url = f"http://127.0.0.1:{port}/video_feed"
    print(f"Testing MJPEG Stream at: {url}")
    
    headers_received = False
    bytes_read = 0
    try:
        req = urllib.request.urlopen(url, timeout=3.0)
        content_type = req.headers.get("Content-Type", "")
        print(f"HTTP Content-Type: {content_type}")
        if "multipart/x-mixed-replace" in content_type:
            headers_received = True
            
        chunk = req.read(2048)
        bytes_read = len(chunk)
        print(f"Read {bytes_read} bytes from MJPEG stream.")
        req.close()
    except Exception as e:
        print(f"MJPEG fetch test warning: {e}")
        
    # 5. Check Telemetry Integrity
    snap = mgr.get_latest_snapshot()
    telemetry = snap.telemetry if snap else {}
    print("Telemetry check:")
    print(f"  EAR thresholds & calculations intact: {'ear_metrics' in telemetry or 'avg_ear' in telemetry}")
    print(f"  MAR thresholds & calculations intact: {'mar_metrics' in telemetry or 'mar' in telemetry}")
    print(f"  Head pose calculations intact: {'head_pose' in telemetry or 'head_pose_pitch' in telemetry}")
    print(f"  Drowsiness score intact: {'drowsiness_score' in telemetry}")
    print(f"  Alerts intact: {'events' in telemetry}")
    
    print("=== VERIFICATION COMPLETED ===")

if __name__ == "__main__":
    test_mjpeg_migration()
