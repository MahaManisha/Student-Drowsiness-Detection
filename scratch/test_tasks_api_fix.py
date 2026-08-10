import sys
import pathlib
ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import os
import cv2
import numpy as np
import threading
import time
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks import python as mp_python

print("=== Testing MediaPipe Tasks API Thread Stability ===")

model_path = os.path.join(ROOT_DIR, "face_landmarker.task")
if not os.path.exists(model_path):
    print("face_landmarker.task model path:", model_path, "Exists:", os.path.exists(model_path))

base_options = mp_python.BaseOptions(model_asset_path=model_path)
options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.IMAGE,
    num_faces=1,
    min_face_detection_confidence=0.3,
    min_face_presence_confidence=0.3,
)

landmarker = vision.FaceLandmarker.create_from_options(options)

dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
rgb = cv2.cvtColor(dummy_frame, cv2.COLOR_BGR2RGB)
mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

lock = threading.Lock()

def worker():
    for i in range(100):
        with lock:
            res = landmarker.detect(mp_image)
        time.sleep(0.01)

t1 = threading.Thread(target=worker)
t2 = threading.Thread(target=worker)
t1.start()
t2.start()
t1.join()
t2.join()

print("MediaPipe Tasks API thread test completed 200 frame detections successfully!")
landmarker.close()
