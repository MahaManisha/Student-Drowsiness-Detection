import sys
import pathlib
ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import numpy as np
import cv2
import mediapipe as mp

print("=== Testing MediaPipe Import & Solutions API Availability ===")
print("MediaPipe version:", getattr(mp, "__version__", "unknown"))
print("hasattr(mp, 'solutions'):", hasattr(mp, "solutions"))

solutions = getattr(mp, "solutions", None)
if solutions is None:
    try:
        import mediapipe.python.solutions as solutions
        print("Imported mediapipe.python.solutions directly!")
    except Exception as e:
        print("Failed to import mediapipe.python.solutions directly:", e)

if solutions is not None:
    print("hasattr(solutions, 'face_mesh'):", hasattr(solutions, "face_mesh"))
    if hasattr(solutions, "face_mesh"):
        face_mesh = solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.3,
            min_tracking_confidence=0.3
        )
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        rgb = cv2.cvtColor(dummy_frame, cv2.COLOR_BGR2RGB)
        res = face_mesh.process(rgb)
        print("FaceMesh process ran successfully! Result multi_face_landmarks:", res.multi_face_landmarks)
        face_mesh.close()
