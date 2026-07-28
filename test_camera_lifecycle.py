"""
Camera Lifecycle Audit & DirectShow Lock Verification Script
"""

import time
import cv2
from camera.camera import CameraStream

def test_camera():
    print("--- TEST 1: Calling is_available() then immediate start() ---")
    cam1 = CameraStream()
    avail = cam1.is_available()
    print(f"is_available() returned: {avail}")
    started1 = cam1.start()
    print(f"cam1.start() returned: {started1}")
    cam1.stop()

    time.sleep(1.0)

    print("\n--- TEST 2: Direct start() without is_available() ---")
    cam2 = CameraStream()
    started2 = cam2.start()
    print(f"cam2.start() returned: {started2}")
    if started2:
        ret, frame = cam2.read_frame()
        print(f"read_frame() returned success={ret}, frame_shape={frame.shape if frame is not None else None}")
    cam2.stop()

if __name__ == "__main__":
    test_camera()
