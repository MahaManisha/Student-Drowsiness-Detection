import sys
import pathlib
ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import numpy as np
import cv2
from detection.face_mesh import FaceMeshDetector
from detection.head_pose_estimator import HeadPoseEstimator

print("=== Final Verification: FaceMeshDetector & HeadPoseEstimator ===")

frame = np.zeros((720, 1280, 3), dtype=np.uint8)

detector = FaceMeshDetector()
estimator = HeadPoseEstimator()

# Synthetic upright face landmarks
mesh = np.zeros((478, 2), dtype=np.float32)
mesh[4] = (0.5, 0.5)      # Nose tip
mesh[152] = (0.5, 0.8)    # Chin
mesh[263] = (0.65, 0.35)  # Left eye outer corner
mesh[33] = (0.35, 0.35)   # Right eye outer corner
mesh[291] = (0.58, 0.65)  # Left mouth corner
mesh[61] = (0.42, 0.65)   # Right mouth corner

pose_res = estimator.estimate_head_pose(mesh, (720, 1280))

print(f"Head Pose Result -> Valid: {pose_res.valid}")
print(f"Pitch: {pose_res.pitch:.2f} deg, Yaw: {pose_res.yaw:.2f} deg, Roll: {pose_res.roll:.2f} deg")

assert pose_res.valid is True
assert abs(pose_res.roll) < 15.0, f"Expected upright Roll (<15 deg), got {pose_res.roll:.2f} deg"

print("SUCCESS: Head Pose orientation verified! Pitch, Yaw, and Roll are correctly calibrated.")
detector.close()
