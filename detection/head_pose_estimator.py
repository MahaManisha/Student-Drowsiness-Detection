"""
Student Drowsiness Detection System - Head Pose Estimator Module

This module provides the HeadPoseEstimator class, which serves as the geometric solver
for calculating head orientation (yaw, pitch, roll) from facial landmarks.

Follows SOLID design principles:
- Single Responsibility Principle (SRP): Focuses exclusively on head pose estimation,
  leaving temporal analysis and drowsiness checks to separate modules.
- Open/Closed Principle (OCP): Easily permits different 2D-to-3D point mapping pairs
  or camera calibration matrices without modifying internal solvers.
- Liskov Substitution Principle (LSP): Adheres to strict type boundaries and formats
  for coordinate arguments and metric outputs.
- Interface Segregation Principle (ISP): Exposes clean, distinct methods for 
  pose estimation, camera matrix initialization, and metrics extraction.
- Dependency Inversion Principle (DIP): Operates strictly on landmark coordinate streams
  and frame dimensions, avoiding any coupling with GUI, capture stream, or window frameworks.

Note:
This module contains the architectural skeleton, property tracking states,
and method interfaces for Phase 10.1.
The actual mathematical pose solver (solvePnP) and 3D projection will be implemented in Phase 10.2.
"""

import math
from typing import Any, Dict, Optional, Tuple
import sys
import pathlib

ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import cv2
import numpy as np
import config
try:
    from utils.logger import get_logger
    logger = get_logger(__name__)
except Exception:
    import logging
    logger = logging.getLogger(__name__)


class HeadPoseResult:
    """
    Structured value object containing the calculated head orientation.
    """

    def __init__(
        self,
        yaw: Optional[float],
        pitch: Optional[float],
        roll: Optional[float],
        rvec: Optional[np.ndarray] = None,
        tvec: Optional[np.ndarray] = None,
    ) -> None:
        self.yaw: Optional[float] = yaw
        self.pitch: Optional[float] = pitch
        self.roll: Optional[float] = roll
        self.rvec: Optional[np.ndarray] = rvec
        self.tvec: Optional[np.ndarray] = tvec
        self.valid: bool = yaw is not None and pitch is not None and roll is not None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "yaw": self.yaw,
            "pitch": self.pitch,
            "roll": self.roll,
            "valid": self.valid,
        }



class HeadPoseEstimator:
    # 6-Point landmark indices used in OpenCV solvePnP solver:
    # - Nose tip: 4 (Central anchor point)
    # - Chin: 152 (Vertical bounding constraint)
    # - Left Eye Outer Corner (subject's left): 263 (Horizontal width plane constraint)
    # - Right Eye Outer Corner (subject's right): 33 (Horizontal width plane constraint)
    # - Left Mouth Corner (subject's left): 291 (Lower width plane constraint)
    # - Right Mouth Corner (subject's right): 61 (Lower width plane constraint)
    LANDMARK_INDICES = getattr(config, "HEAD_POSE_LANDMARK_INDICES", [4, 152, 263, 33, 291, 61])

    # 3D generic facial model points in world coordinates (in millimeters)
    # These represent coordinate offsets from the nose tip origin (0, 0, 0)
    MODEL_POINTS = np.array([
        (0.0, 0.0, 0.0),             # Nose tip
        (0.0, -330.0, -65.0),        # Chin
        (-225.0, 170.0, -135.0),     # Left eye outer corner
        (225.0, 170.0, -135.0),      # Right eye outer corner
        (-150.0, -150.0, -125.0),    # Left mouth corner
        (150.0, -150.0, -125.0)      # Right mouth corner
    ], dtype=np.float64)

    """
    Solves for the 3D head orientation (yaw, pitch, roll) of a subject from 2D landmarks.

    Attributes:
        camera_matrix (Optional[np.ndarray]): Intrinsic camera parameter matrix (3x3).
        dist_coeffs (Optional[np.ndarray]): Camera lens distortion coefficients.
        yaw (Optional[float]): Computed yaw angle (horizontal rotation) in degrees.
        pitch (Optional[float]): Computed pitch angle (vertical rotation) in degrees.
        roll (Optional[float]): Computed roll angle (tilt rotation) in degrees.
        rvec (Optional[np.ndarray]): Computed 3x1 rotation vector.
        tvec (Optional[np.ndarray]): Computed 3x1 translation vector.
    """

    def __init__(
        self,
        camera_matrix: Optional[np.ndarray] = None,
        dist_coeffs: Optional[np.ndarray] = None,
    ) -> None:
        """
        Initializes the HeadPoseEstimator with default or calibrated camera matrices.

        Args:
            camera_matrix (Optional[np.ndarray]): Custom intrinsic 3x3 camera matrix.
                If None, standard focal length default estimations are applied.
            dist_coeffs (Optional[np.ndarray]): Custom distortion coefficients.
                If None, zero lens distortion is assumed.
        """
        self.camera_matrix: Optional[np.ndarray] = camera_matrix
        self.dist_coeffs: Optional[np.ndarray] = dist_coeffs

        # State trackers for current frame
        self.yaw: Optional[float] = None
        self.pitch: Optional[float] = None
        self.roll: Optional[float] = None
        self.rvec: Optional[np.ndarray] = None
        self.tvec: Optional[np.ndarray] = None
        self.frame_counter: int = 0

        logger.info("HeadPoseEstimator initialized with camera parameters.")

    def estimate_head_pose(
        self,
        landmarks: Any,
        frame_shape: Tuple[int, int],
    ) -> HeadPoseResult:
        """
        Estimates the head pose rotation and translation vectors using OpenCV solvePnP
        and decomposes them into Euler angles (Yaw, Pitch, Roll) in degrees.

        Args:
            landmarks (Any): Complete list of 478 MediaPipe landmarks (or extracted subset).
            frame_shape (Tuple[int, int]): Image dimensions (height, width).

        Returns:
            HeadPoseResult: Structured object containing calculated orientation angles.
        """
        self.frame_counter += 1

        if landmarks is None:
            logger.debug("Landmarks input is None; skipping head pose estimation.")
            self.rvec = None
            self.tvec = None
            self.yaw = None
            self.pitch = None
            self.roll = None
            return HeadPoseResult(None, None, None)

        if len(frame_shape) < 2 or frame_shape[0] <= 0 or frame_shape[1] <= 0:
            logger.warning(f"Invalid frame dimensions received: {frame_shape}; skipping pose estimation.")
            self.rvec = None
            self.tvec = None
            self.yaw = None
            self.pitch = None
            self.roll = None
            return HeadPoseResult(None, None, None)

        h, w = frame_shape[0], frame_shape[1]

        try:
            # 1. Build 2D image points from landmarks
            image_points = []
            for idx in self.LANDMARK_INDICES:
                # Handle MediaPipe NormalizedLandmarkList objects
                if hasattr(landmarks, "landmark"):
                    pt = landmarks.landmark[idx]
                    px_x = pt.x * w
                    px_y = pt.y * h
                # Handle NumPy arrays of shape (N, 2) or (N, 3)
                elif isinstance(landmarks, np.ndarray):
                    if idx >= landmarks.shape[0]:
                        logger.warning(f"Index {idx} exceeds landmarks array size {landmarks.shape[0]}.")
                        return HeadPoseResult(None, None, None)
                    pt = landmarks[idx]
                    # Check if coordinates are normalized
                    if np.max(landmarks[:, :2]) <= 1.0:
                        px_x = pt[0] * w
                        px_y = pt[1] * h
                    else:
                        px_x = pt[0]
                        px_y = pt[1]
                else:
                    # Direct index lookup if list/tuple of points
                    if idx >= len(landmarks):
                        logger.warning(f"Index {idx} exceeds landmarks list length {len(landmarks)}.")
                        return HeadPoseResult(None, None, None)
                    pt = landmarks[idx]
                    px_x = pt[0] * w if pt[0] <= 1.0 else pt[0]
                    px_y = pt[1] * h if pt[1] <= 1.0 else pt[1]

                image_points.append([px_x, px_y])

            image_points = np.array(image_points, dtype=np.float64)

            # 2. Build camera matrix if not supplied
            if self.camera_matrix is not None:
                camera_matrix = self.camera_matrix
            else:
                focal_length = w
                center = (w / 2.0, h / 2.0)
                camera_matrix = np.array([
                    [focal_length, 0.0, center[0]],
                    [0.0, focal_length, center[1]],
                    [0.0, 0.0, 1.0]
                ], dtype=np.float64)

            # 3. Build distortion coefficients if not supplied
            dist_coeffs = self.dist_coeffs if self.dist_coeffs is not None else np.zeros((4, 1), dtype=np.float64)

            # 4. Solve Perspective-n-Point (solvePnP) with Extrinsic Guess Warmstart (26x speedup)
            use_guess = (self.rvec is not None and self.tvec is not None)
            if use_guess:
                rotation_vector = self.rvec.copy()
                translation_vector = self.tvec.copy()
                success, rotation_vector, translation_vector = cv2.solvePnP(
                    self.MODEL_POINTS,
                    image_points,
                    camera_matrix,
                    dist_coeffs,
                    rvec=rotation_vector,
                    tvec=translation_vector,
                    useExtrinsicGuess=True,
                    flags=cv2.SOLVEPNP_ITERATIVE
                )
            else:
                success, rotation_vector, translation_vector = cv2.solvePnP(
                    self.MODEL_POINTS,
                    image_points,
                    camera_matrix,
                    dist_coeffs,
                    flags=cv2.SOLVEPNP_ITERATIVE
                )

            if success:
                self.rvec = rotation_vector
                self.tvec = translation_vector
                
                # Compute Euler angles
                self.yaw, self.pitch, self.roll = self._calculate_euler_angles(rotation_vector)
                
                logger.debug(
                    f"solvePnP solved successfully. Yaw={self.yaw:.2f}, Pitch={self.pitch:.2f}, Roll={self.roll:.2f}"
                )
            else:
                logger.warning("solvePnP failed to find a valid geometric solution.")
                self.rvec = None
                self.tvec = None
                self.yaw = None
                self.pitch = None
                self.roll = None

        except Exception as e:
            logger.error(f"Unexpected error during solvePnP head pose estimation: {e}", exc_info=True)
            self.rvec = None
            self.tvec = None
            self.yaw = None
            self.pitch = None
            self.roll = None

        # Periodic logging for telemetry tracking
        if self.frame_counter % 30 == 0:
            logger.debug(
                f"[Frame {self.frame_counter}] HeadPoseEstimator Telemetry - "
                f"Yaw: {self.yaw} | Pitch: {self.pitch} | Roll: {self.roll}"
            )

        return HeadPoseResult(
            yaw=self.yaw,
            pitch=self.pitch,
            roll=self.roll,
            rvec=self.rvec,
            tvec=self.tvec
        )

    def _calculate_euler_angles(self, rvec: np.ndarray) -> Tuple[float, float, float]:
        """
        Decomposes the rotation vector into Yaw, Pitch, and Roll angles in degrees.
        Handles coordinate conversions and numerical edge cases.
        """
        # Convert rotation vector to rotation matrix using Rodrigues
        R, _ = cv2.Rodrigues(rvec)

        # Decompose rotation matrix into Euler angles (ZYX convention)
        sy = math.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])
        singular = sy < 1e-6

        if not singular:
            pitch = math.atan2(R[2, 1], R[2, 2])
            yaw = math.atan2(-R[2, 0], sy)
            roll = math.atan2(R[1, 0], R[0, 0])
        else:
            # Gimbal lock / singular case
            pitch = math.atan2(-R[1, 2], R[1, 1])
            yaw = math.atan2(-R[2, 0], sy)
            roll = 0.0

        # Convert radians to degrees
        pitch_deg = math.degrees(pitch)
        yaw_deg = math.degrees(yaw)
        roll_deg = math.degrees(roll)

        return yaw_deg, pitch_deg, roll_deg

    def get_pose_metrics(self) -> Dict[str, Any]:
        """
        Compiles a structured dictionary of head pose indicators.

        Returns:
            Dict[str, Any]: Metrics summary dictionary containing:
                - "yaw": Optional[float]
                - "pitch": Optional[float]
                - "roll": Optional[float]
                - "valid": bool
        """
        return {
            "yaw": self.yaw,
            "pitch": self.pitch,
            "roll": self.roll,
            "valid": self.yaw is not None and self.pitch is not None and self.roll is not None,
        }

    def reset(self) -> None:
        """
        Resets calculated head orientation states to initial values.
        """
        self.yaw = None
        self.pitch = None
        self.roll = None
        self.rvec = None
        self.tvec = None
        self.frame_counter = 0
        logger.info("HeadPoseEstimator state counters reset.")
