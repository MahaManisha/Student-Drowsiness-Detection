"""
Student Drowsiness Detection System - MediaPipe Face Mesh Module

This module provides a modular FaceMeshDetector class to detect facial structures,
extract 3D facial landmark coordinates (in pixel-space), and render MediaPipe's
landmark mesh grid onto video frames.
"""

import cv2
import numpy as np
import mediapipe as mp
from typing import Optional, List, Tuple, Dict, Any

from utils.logger import get_logger

logger = get_logger(__name__)


# MediaPipe Face Mesh Landmark Indices for Key Facial Features
# (Exported as reference constants for future EAR / MAR calculation modules)
RIGHT_EYE_LANDMARKS = [33, 160, 158, 133, 153, 144]
LEFT_EYE_LANDMARKS = [362, 385, 387, 263, 373, 380]
OUTER_LIPS_LANDMARKS = [61, 291, 0, 17, 84, 181, 314, 405]
INNER_LIPS_LANDMARKS = [78, 308, 13, 14, 82, 312, 87, 317]


class FaceMeshDetector:
    """
    Modular MediaPipe Face Mesh detector for extracting 468 (or 478 refined) facial landmarks.
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
        Initializes the MediaPipe Face Mesh solution pipeline.

        Args:
            static_image_mode (bool): If True, treats input images as static photos rather than video stream.
            max_num_faces (int): Maximum number of faces to detect per frame.
            refine_landmarks (bool): If True, enables iris landmarks (478 total points).
            min_detection_confidence (float): Minimum confidence threshold for face detection [0.0, 1.0].
            min_tracking_confidence (float): Minimum confidence threshold for landmark tracking [0.0, 1.0].
        """
        self.static_image_mode = static_image_mode
        self.max_num_faces = max_num_faces
        self.refine_landmarks = refine_landmarks
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence

        # Initialize MediaPipe solutions
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=self.static_image_mode,
            max_num_faces=self.max_num_faces,
            refine_landmarks=self.refine_landmarks,
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence,
        )
        logger.info("MediaPipe Face Mesh Detector initialized successfully.")

    def detect_landmarks(
        self, frame: np.ndarray
    ) -> Tuple[bool, List[List[Tuple[int, int, float]]]]:
        """
        Processes a BGR image frame to detect faces and extract facial landmark coordinates.

        Args:
            frame (np.ndarray): BGR image frame captured from camera.

        Returns:
            Tuple[bool, List[List[Tuple[int, int, float]]]]:
                - bool: True if at least one face was detected, False otherwise.
                - List[List[Tuple[int, int, float]]]: List of faces, where each face is a list
                  of (x_pixel, y_pixel, z_depth) landmark coordinate tuples.
        """
        if frame is None or frame.size == 0:
            return False, []

        try:
            h, w, _ = frame.shape
            # MediaPipe requires RGB format
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_frame)

            if not results.multi_face_landmarks:
                return False, []

            all_faces_landmarks: List[List[Tuple[int, int, float]]] = []

            for face_landmarks in results.multi_face_landmarks:
                face_coords: List[Tuple[int, int, float]] = []
                for lm in face_landmarks.landmark:
                    # Convert normalized float coordinates [0.0, 1.0] to pixel integer coordinates
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    face_coords.append((cx, cy, lm.z))
                all_faces_landmarks.append(face_coords)

            return True, all_faces_landmarks

        except Exception as e:
            logger.error(f"Error processing frame in FaceMeshDetector: {e}")
            return False, []

    def draw_landmarks(
        self,
        frame: np.ndarray,
        draw_tessellation: bool = True,
        draw_contours: bool = True,
        draw_irises: bool = True,
    ) -> np.ndarray:
        """
        Renders MediaPipe's facial mesh connections and landmark points onto the frame.

        Args:
            frame (np.ndarray): Input BGR image frame.
            draw_tessellation (bool): Render full facial mesh grid.
            draw_contours (bool): Highlight eye, lip, and face oval contours.
            draw_irises (bool): Render iris landmark circles if refine_landmarks is True.

        Returns:
            np.ndarray: Image frame with drawn facial mesh overlays.
        """
        if frame is None or frame.size == 0:
            return frame

        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_frame)

            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    # 1. Draw Mesh Tessellation
                    if draw_tessellation:
                        self.mp_drawing.draw_landmarks(
                            image=frame,
                            landmark_list=face_landmarks,
                            connections=self.mp_face_mesh.FACEMESH_TESSELLATION,
                            landmark_drawing_spec=None,
                            connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_tessellation_style(),
                        )

                    # 2. Draw Eye, Lip & Face Contours
                    if draw_contours:
                        self.mp_drawing.draw_landmarks(
                            image=frame,
                            landmark_list=face_landmarks,
                            connections=self.mp_face_mesh.FACEMESH_CONTOURS,
                            landmark_drawing_spec=None,
                            connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_contours_style(),
                        )

                    # 3. Draw Iris Landmarking (if enabled)
                    if draw_irises and self.refine_landmarks:
                        self.mp_drawing.draw_landmarks(
                            image=frame,
                            landmark_list=face_landmarks,
                            connections=self.mp_face_mesh.FACEMESH_IRISES,
                            landmark_drawing_spec=None,
                            connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_iris_connections_style(),
                        )

            return frame

        except Exception as e:
            logger.error(f"Error drawing face mesh landmarks: {e}")
            return frame

    def close(self) -> None:
        """
        Releases MediaPipe Face Mesh resources cleanly.
        """
        if hasattr(self, "face_mesh") and self.face_mesh:
            logger.info("Closing MediaPipe Face Mesh detector...")
            self.face_mesh.close()


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
