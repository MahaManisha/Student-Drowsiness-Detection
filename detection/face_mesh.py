"""
Student Drowsiness Detection System - MediaPipe Face Mesh Module

This module provides a modular FaceMeshDetector class to detect facial structures,
extract 3D facial landmark coordinates (in pixel-space), and render MediaPipe's
landmark mesh grid onto video frames using MediaPipe's classic Solutions API.
"""

import cv2
import numpy as np
import mediapipe as mp
from typing import Optional, List, Tuple, Dict, Any

import sys
import pathlib

ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from utils.logger import get_logger
    logger = get_logger(__name__)
except Exception:
    import logging
    logger = logging.getLogger(__name__)

# MediaPipe Face Mesh Landmark Indices for Key Facial Features
RIGHT_EYE_LANDMARKS = [33, 160, 158, 133, 153, 144]
LEFT_EYE_LANDMARKS = [362, 385, 387, 263, 373, 380]
OUTER_LIPS_LANDMARKS = [61, 291, 0, 17, 84, 181, 314, 405]
INNER_LIPS_LANDMARKS = [78, 308, 13, 14, 82, 312, 87, 317]


class FaceMeshDetector:
    """
    Modular MediaPipe Face Mesh detector using classic MediaPipe solutions.face_mesh pipeline.
    Extracts 468 (or 478 refined) 3D landmark coordinates and renders mesh grid overlays.
    """

    def __init__(
        self,
        static_image_mode: bool = False,
        max_num_faces: int = 1,
        refine_landmarks: bool = True,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ) -> None:
        """
        Initializes the MediaPipe Face Mesh pipeline using classic Solutions API.

        Args:
            static_image_mode (bool): If True, treats input images as static photos.
            max_num_faces (int): Maximum number of faces to detect per frame.
            refine_landmarks (bool): If True, enables iris landmarks (478 total points).
            min_detection_confidence (float): Minimum confidence threshold for face detection.
            min_tracking_confidence (float): Minimum confidence threshold for landmark tracking.
        """
        self.static_image_mode = static_image_mode
        self.max_num_faces = max_num_faces
        self.refine_landmarks = refine_landmarks
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence

        logger.info("Initializing MediaPipe Face Mesh...")
        solutions = getattr(mp, "solutions", None)
        if solutions is None:
            try:
                import mediapipe.python.solutions as solutions
            except ImportError:
                solutions = None

        if solutions is not None and hasattr(solutions, "face_mesh"):
            self.mp_face_mesh = solutions.face_mesh
            self.mp_drawing = solutions.drawing_utils
            self.mp_drawing_styles = solutions.drawing_styles

            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=self.static_image_mode,
                max_num_faces=self.max_num_faces,
                refine_landmarks=self.refine_landmarks,
                min_detection_confidence=self.min_detection_confidence,
                min_tracking_confidence=self.min_tracking_confidence,
            )
            self._using_tasks = False
            logger.info("MediaPipe Face Mesh Detector (Solutions API) initialized successfully.")
        else:
            logger.info("Solutions API not available. Initializing MediaPipe Face Mesh via Tasks API...")
            self._init_tasks_api()

    def _init_tasks_api(self) -> None:
        """Initializes or re-instantiates MediaPipe FaceLandmarker Tasks API context."""
        import os
        from mediapipe.tasks.python import vision
        from mediapipe.tasks import python as mp_python

        model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "face_landmarker.task")
        if not os.path.exists(model_path):
            import urllib.request
            url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
            urllib.request.urlretrieve(url, model_path)

        base_options = mp_python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_faces=self.max_num_faces,
            min_face_detection_confidence=self.min_detection_confidence,
            min_face_presence_confidence=self.min_tracking_confidence,
        )
        self.landmarker = vision.FaceLandmarker.create_from_options(options)
        self.mp_drawing = vision.drawing_utils
        self.mp_drawing_styles = vision.drawing_styles
        self._using_tasks = True
        logger.info("MediaPipe Face Mesh Detector (Tasks API) initialized successfully.")

    def detect_landmarks(
        self, frame: np.ndarray
    ) -> Tuple[bool, List[List[Tuple[int, int, float]]], Optional[Any]]:
        """
        Processes a BGR image frame to detect faces and extract facial landmark coordinates.

        Args:
            frame (np.ndarray): BGR image frame captured from camera.

        Returns:
            Tuple[bool, List[List[Tuple[int, int, float]]], Optional[Any]]:
                - bool: True if at least one face was detected, False otherwise.
                - List[List[Tuple[int, int, float]]]: List of faces, where each face is a list
                  of (x_pixel, y_pixel, z_depth) landmark coordinate tuples.
                - Optional[Any]: Raw MediaPipe face_landmarks protobuf for single-pass drawing.
        """
        if frame is None or frame.size == 0:
            return False, [], None

        try:
            h, w, _ = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            if not getattr(self, "_using_tasks", False):
                results = self.face_mesh.process(rgb_frame)
                if not results.multi_face_landmarks:
                    return False, [], None

                all_faces_landmarks: List[List[Tuple[int, int, float]]] = []
                for face_landmarks in results.multi_face_landmarks:
                    face_coords: List[Tuple[int, int, float]] = []
                    for lm in face_landmarks.landmark:
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        face_coords.append((cx, cy, lm.z))
                    all_faces_landmarks.append(face_coords)

                return True, all_faces_landmarks, results.multi_face_landmarks[0]
            else:
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                try:
                    res = self.landmarker.detect(mp_image)
                except Exception as ex:
                    ex_str = str(ex).lower()
                    if "shutdown" in ex_str or "schedule" in ex_str or "executor" in ex_str or "futures" in ex_str:
                        logger.warning("Thread pool executor reset detected. Re-initializing Tasks API...")
                        try:
                            self._init_tasks_api()
                            res = self.landmarker.detect(mp_image)
                        except Exception as ex2:
                            logger.error(f"Retry Tasks API detect failed: {ex2}")
                            return False, [], None
                    else:
                        logger.error(f"MediaPipe Tasks API detect exception: {ex}")
                        return False, [], None

                if not res.face_landmarks:
                    return False, [], None

                all_faces_landmarks: List[List[Tuple[int, int, float]]] = []
                for face_landmarks in res.face_landmarks:
                    face_coords: List[Tuple[int, int, float]] = []
                    for lm in face_landmarks:
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        face_coords.append((cx, cy, lm.z))
                    all_faces_landmarks.append(face_coords)

                class FaceLandmarksWrapper:
                    def __init__(self, landmarks):
                        self.landmark = landmarks

                return True, all_faces_landmarks, FaceLandmarksWrapper(res.face_landmarks[0])

        except Exception as e:
            logger.error(f"Error processing frame in FaceMeshDetector: {e}")
            return False, [], None

    def draw_landmarks(
        self,
        frame: np.ndarray,
        face_landmarks_proto: Optional[Any] = None,
        draw_tessellation: bool = True,
        draw_contours: bool = True,
        draw_irises: bool = True,
    ) -> np.ndarray:
        """
        Renders MediaPipe's facial mesh connections and landmark points onto the frame.

        Args:
            frame (np.ndarray): Input BGR image frame.
            face_landmarks_proto (Optional[Any]): Pre-computed MediaPipe face landmarks protobuf or wrapper.
            draw_tessellation (bool): Render full facial mesh grid.
            draw_contours (bool): Highlight eye, lip, and face oval contours.
            draw_irises (bool): Render iris landmark circles.

        Returns:
            np.ndarray: Image frame with drawn facial mesh overlays.
        """
        if frame is None or frame.size == 0:
            return frame

        try:
            if not getattr(self, "_using_tasks", False):
                proto_to_draw = face_landmarks_proto
                if proto_to_draw is None:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = self.face_mesh.process(rgb_frame)
                    if results.multi_face_landmarks:
                        proto_to_draw = results.multi_face_landmarks[0]

                if proto_to_draw is not None:
                    if draw_tessellation:
                        self.mp_drawing.draw_landmarks(
                            image=frame,
                            landmark_list=proto_to_draw,
                            connections=self.mp_face_mesh.FACEMESH_TESSELATION,
                            landmark_drawing_spec=None,
                            connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_tesselation_style(),
                        )
                    if draw_contours:
                        self.mp_drawing.draw_landmarks(
                            image=frame,
                            landmark_list=proto_to_draw,
                            connections=self.mp_face_mesh.FACEMESH_CONTOURS,
                            landmark_drawing_spec=None,
                            connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_contours_style(),
                        )
                    if draw_irises and self.refine_landmarks:
                        self.mp_drawing.draw_landmarks(
                            image=frame,
                            landmark_list=proto_to_draw,
                            connections=self.mp_face_mesh.FACEMESH_IRISES,
                            landmark_drawing_spec=None,
                            connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_iris_connections_style(),
                        )
            else:
                from mediapipe.tasks.python.vision import FaceLandmarksConnections
                lm_list = getattr(face_landmarks_proto, "landmark", None)
                if lm_list is not None:
                    if draw_tessellation:
                        self.mp_drawing.draw_landmarks(
                            image=frame,
                            landmark_list=lm_list,
                            connections=FaceLandmarksConnections.FACE_LANDMARKS_TESSELATION,
                            landmark_drawing_spec=None,
                            connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_tesselation_style(),
                        )
                    if draw_contours:
                        self.mp_drawing.draw_landmarks(
                            image=frame,
                            landmark_list=lm_list,
                            connections=FaceLandmarksConnections.FACE_LANDMARKS_CONTOURS,
                            landmark_drawing_spec=None,
                            connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_contours_style(),
                        )
                    if draw_irises and self.refine_landmarks:
                        self.mp_drawing.draw_landmarks(
                            image=frame,
                            landmark_list=lm_list,
                            connections=FaceLandmarksConnections.FACE_LANDMARKS_LEFT_IRIS,
                            landmark_drawing_spec=None,
                            connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_iris_connections_style(),
                        )
                        self.mp_drawing.draw_landmarks(
                            image=frame,
                            landmark_list=lm_list,
                            connections=FaceLandmarksConnections.FACE_LANDMARKS_RIGHT_IRIS,
                            landmark_drawing_spec=None,
                            connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_iris_connections_style(),
                        )

            return frame

        except Exception as e:
            logger.error(f"Error drawing face mesh landmarks: {e}")
            return frame

    def close(self) -> None:
        """Releases MediaPipe Face Mesh resources cleanly."""
        logger.info("Closing MediaPipe Face Mesh detector...")
        if hasattr(self, "face_mesh") and self.face_mesh:
            self.face_mesh.close()
        if hasattr(self, "landmarker") and self.landmarker:
            self.landmarker.close()


# Runnable standalone test script combining CameraStream + FaceMeshDetector
if __name__ == "__main__":
    from camera.camera import CameraStream

    print("=== Testing MediaPipe Face Mesh Detector Module ===")
    detector = FaceMeshDetector()
    camera = CameraStream()

    if camera.start():
        print("Press 'q' in the window to quit...")
        try:
            while True:
                ret, frame = camera.read_frame()
                if not ret or frame is None:
                    break

                # Detect face and landmarks
                has_face, landmarks = detector.detect_landmarks(frame)

                # Draw face mesh grid on frame
                if has_face:
                    frame = detector.draw_landmarks(frame)
                    num_points = len(landmarks[0]) if landmarks else 0
                    cv2.putText(
                        frame,
                        f"Face Detected! ({num_points} landmarks)",
                        (10, 70),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2,
                    )
                else:
                    cv2.putText(
                        frame,
                        "Searching for Face...",
                        (10, 70),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 0, 255),
                        2,
                    )

                # Show FPS overlay
                frame = camera.draw_fps_overlay(frame)

                # Render preview
                cv2.imshow("MediaPipe Face Mesh Integration Test", frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

        finally:
            detector.close()
            camera.stop()
            cv2.destroyAllWindows()
            print("Test finished cleanly.")
