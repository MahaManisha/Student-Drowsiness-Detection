"""
Student Drowsiness Detection System - Eye Landmark Extraction Module

This module provides the EyeLandmarkExtractor class, which is responsible for
isolating, validating, and extracting eye-specific landmark coordinates from
facial landmark datasets (e.g., MediaPipe Face Mesh outputs).

Follows SOLID design principles:
- Single Responsibility Principle (SRP): Isolates eye landmark processing from face mesh detection and EAR calculations.
- Open/Closed Principle (OCP): Configurable landmark index maps for flexible face mesh models.
- Dependency Inversion Principle (DIP): Operates independently of specific camera or detector implementations.

Note:
This module contains the architectural skeleton and interface specification for Phase 3.1.
Landmark extraction logic will be implemented in Phase 3.2.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import cv2
import numpy as np

import config
from utils.logger import get_logger

logger = get_logger(__name__)

# ==============================================================================
# MEDIAPIPE FACE MESH EYE LANDMARK INDICES (6-POINT EAR STANDARD)
# ==============================================================================
# Standard 6-point perimeter landmark points for Eye Aspect Ratio (EAR) computation:
# Formula: EAR = (||P2 - P6|| + ||P3 - P5||) / (2 * ||P1 - P4||)

# ------------------------------------------------------------------------------
# Right Eye Landmark Indices (Subject's Right Eye / Viewer's Left):
# P1 (Index 33)  : Lateral Canthus (Outer Corner)
# P2 (Index 160) : Superior Eyelid Point 1 (Top-Right Vertical Landmark)
# P3 (Index 158) : Superior Eyelid Point 2 (Top-Left Vertical Landmark)
# P4 (Index 133) : Medial Canthus (Inner Corner)
# P5 (Index 153) : Inferior Eyelid Point 2 (Bottom-Left Vertical Landmark)
# P6 (Index 144) : Inferior Eyelid Point 1 (Bottom-Right Vertical Landmark)
# ------------------------------------------------------------------------------
RIGHT_EYE_LANDMARK_INDICES: List[int] = getattr(
    config, "RIGHT_EYE_LANDMARK_INDICES", [33, 160, 158, 133, 153, 144]
)

# ------------------------------------------------------------------------------
# Left Eye Landmark Indices (Subject's Left Eye / Viewer's Right):
# P1 (Index 362) : Medial Canthus (Inner Corner)
# P2 (Index 385) : Superior Eyelid Point 1 (Top-Right Vertical Landmark)
# P3 (Index 387) : Superior Eyelid Point 2 (Top-Left Vertical Landmark)
# P4 (Index 263) : Lateral Canthus (Outer Corner)
# P5 (Index 373) : Inferior Eyelid Point 2 (Bottom-Left Vertical Landmark)
# P6 (Index 380) : Inferior Eyelid Point 1 (Bottom-Right Vertical Landmark)
# ------------------------------------------------------------------------------
LEFT_EYE_LANDMARK_INDICES: List[int] = getattr(
    config, "LEFT_EYE_LANDMARK_INDICES", [362, 385, 387, 263, 373, 380]
)

# Aliases for backwards compatibility & modular defaults
DEFAULT_RIGHT_EYE_INDICES: List[int] = RIGHT_EYE_LANDMARK_INDICES
DEFAULT_LEFT_EYE_INDICES: List[int] = LEFT_EYE_LANDMARK_INDICES


class EyeLandmarkExtractor:
    """
    Independent extractor for isolating and formatting left and right eye landmark coordinates.

    This class is designed to process general face landmark coordinates (e.g., MediaPipe 468/478
    3D mesh outputs or custom landmark arrays) and extract subset landmark points corresponding
    to the eyes for Eye Aspect Ratio (EAR) and eye state calculations.
    """

    def __init__(
        self,
        right_eye_indices: Optional[List[int]] = None,
        left_eye_indices: Optional[List[int]] = None,
    ) -> None:
        """
        Initializes the EyeLandmarkExtractor with configurable landmark indices.

        Args:
            right_eye_indices (Optional[List[int]]): List of landmark indices corresponding to the right eye.
                Defaults to MediaPipe standard 6-point right eye indices.
            left_eye_indices (Optional[List[int]]): List of landmark indices corresponding to the left eye.
                Defaults to MediaPipe standard 6-point left eye indices.
        """
        self.right_eye_indices: List[int] = (
            list(right_eye_indices) if right_eye_indices is not None else DEFAULT_RIGHT_EYE_INDICES
        )
        self.left_eye_indices: List[int] = (
            list(left_eye_indices) if left_eye_indices is not None else DEFAULT_LEFT_EYE_INDICES
        )

        logger.info(
            f"EyeLandmarkExtractor initialized with {len(self.right_eye_indices)} right eye indices "
            f"and {len(self.left_eye_indices)} left eye indices."
        )

    def validate_landmarks(self, landmarks: Any) -> bool:
        """
        Validates whether the provided facial landmarks object is structurally valid and contains
        sufficient data points for eye landmark extraction.

        Args:
            landmarks (Any): Facial landmark collection to validate. Can be a MediaPipe
                NormalizedLandmarkList (or object with .landmark attribute), a list/tuple of
                landmarks/coordinates, or a NumPy coordinate array.

        Returns:
            bool: True if landmarks are valid and non-empty, False otherwise.
        """
        if landmarks is None:
            logger.warning("Landmarks object is None.")
            return False

        try:
            # Handle MediaPipe NormalizedLandmarkList object
            if hasattr(landmarks, "landmark"):
                items = landmarks.landmark
                count = len(items)
            elif isinstance(landmarks, np.ndarray):
                count = landmarks.shape[0]
            elif isinstance(landmarks, (list, tuple)):
                count = len(landmarks)
            else:
                logger.warning(f"Unsupported landmarks object type: {type(landmarks)}")
                return False

            if count == 0:
                logger.warning("Landmarks collection is empty.")
                return False

            max_required_index = max(self.right_eye_indices + self.left_eye_indices)
            if count <= max_required_index:
                logger.warning(
                    f"Landmarks count ({count}) is insufficient for max required eye index ({max_required_index})."
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating landmarks: {e}")
            return False

    def _extract_single_eye(self, landmarks: Any, indices: List[int]) -> Optional[Any]:
        """
        Internal helper to isolate landmark points for a single eye given a list of target indices.

        Args:
            landmarks (Any): Facial landmark collection.
            indices (List[int]): Predefined index mapping for the target eye.

        Returns:
            Optional[Any]: Extracted eye landmarks matching input element structure,
                or None if extraction fails.
        """
        if not self.validate_landmarks(landmarks):
            return None

        try:
            # MediaPipe NormalizedLandmarkList (Solutions API / Tasks API)
            if hasattr(landmarks, "landmark"):
                return [landmarks.landmark[i] for i in indices]
            # NumPy coordinate matrix
            elif isinstance(landmarks, np.ndarray):
                return landmarks[indices]
            # List or tuple format
            elif isinstance(landmarks, (list, tuple)):
                return [landmarks[i] for i in indices]
            else:
                return None
        except Exception as e:
            logger.error(f"Error extracting eye landmarks for indices {indices}: {e}")
            return None

    def to_pixel_coordinates(
        self,
        landmarks: Any,
        frame_shape: Tuple[int, ...],
    ) -> Optional[np.ndarray]:
        """
        Converts normalized facial landmark coordinates ([0.0, 1.0]) into absolute integer pixel coordinates.

        Args:
            landmarks (Any): Landmark collection (MediaPipe landmark objects, list of tuples, or NumPy array).
            frame_shape (Tuple[int, ...]): Image frame shape tuple (height, width) or (height, width, channels).

        Returns:
            Optional[np.ndarray]: NumPy array of shape (N, 2) containing integer pixel coordinates [[x_px, y_px], ...],
                or None if conversion fails or inputs are invalid.
        """
        if landmarks is None or frame_shape is None:
            logger.warning("Landmarks or frame_shape is None for pixel coordinate conversion.")
            return None

        try:
            if len(frame_shape) < 2 or frame_shape[0] <= 0 or frame_shape[1] <= 0:
                logger.warning(f"Invalid frame_shape dimensions: {frame_shape}")
                return None

            h, w = int(frame_shape[0]), int(frame_shape[1])

            # Handle MediaPipe landmark objects or list/tuple sequences
            if isinstance(landmarks, (list, tuple)):
                coords = []
                for lm in landmarks:
                    if hasattr(lm, "x") and hasattr(lm, "y"):
                        # MediaPipe NormalizedLandmark object
                        x_val, y_val = lm.x, lm.y
                    elif isinstance(lm, (list, tuple, np.ndarray)) and len(lm) >= 2:
                        x_val, y_val = lm[0], lm[1]
                    else:
                        logger.warning(f"Unrecognized landmark item format: {lm}")
                        return None

                    # If normalized float [0.0, 1.0], scale by frame dimensions; if already pixel integer, preserve
                    if isinstance(x_val, (float, np.floating)) and 0.0 <= x_val <= 1.0:
                        x_px = int(round(x_val * w))
                    else:
                        x_px = int(round(x_val))

                    if isinstance(y_val, (float, np.floating)) and 0.0 <= y_val <= 1.0:
                        y_px = int(round(y_val * h))
                    else:
                        y_px = int(round(y_val))

                    coords.append([x_px, y_px])
                return np.array(coords, dtype=np.int32)

            # Handle NumPy array format
            elif isinstance(landmarks, np.ndarray):
                if landmarks.size == 0 or landmarks.ndim != 2 or landmarks.shape[1] < 2:
                    logger.warning(f"Invalid NumPy landmarks shape for pixel conversion: {landmarks.shape}")
                    return None

                # Check if coordinates are normalized floats
                if np.issubdtype(landmarks.dtype, np.floating) and np.max(landmarks[:, :2]) <= 1.0:
                    px_x = np.round(landmarks[:, 0] * w).astype(np.int32)
                    px_y = np.round(landmarks[:, 1] * h).astype(np.int32)
                    return np.column_stack((px_x, px_y))
                else:
                    # Already pixel coordinates
                    return np.round(landmarks[:, :2]).astype(np.int32)

            else:
                logger.warning(f"Unsupported landmark container type for pixel conversion: {type(landmarks)}")
                return None

        except Exception as e:
            logger.error(f"Error converting landmarks to pixel coordinates: {e}")
            return None

    def extract_right_eye(
        self,
        landmarks: Any,
        frame_shape: Optional[Tuple[int, ...]] = None,
    ) -> Optional[Union[List[Any], np.ndarray]]:
        """
        Extracts landmark points for the right eye from full facial landmarks.

        Args:
            landmarks (Any): Facial landmark collection (MediaPipe landmark list, NumPy array, or tuple list).
            frame_shape (Optional[Tuple[int, ...]]): Optional frame shape tuple (height, width).
                If provided, converts normalized coordinates into integer pixel coordinates (N, 2).

        Returns:
            Optional[Union[List[Any], np.ndarray]]: Extracted right eye landmarks. If frame_shape is provided,
                returns NumPy array of integer pixel coordinates [[x_px, y_px], ...].
        """
        logger.debug("Extracting right eye landmarks.")
        raw_eye = self._extract_single_eye(landmarks, self.right_eye_indices)
        if raw_eye is None:
            return None

        if frame_shape is not None:
            return self.to_pixel_coordinates(raw_eye, frame_shape)
        return raw_eye

    def extract_left_eye(
        self,
        landmarks: Any,
        frame_shape: Optional[Tuple[int, ...]] = None,
    ) -> Optional[Union[List[Any], np.ndarray]]:
        """
        Extracts landmark points for the left eye from full facial landmarks.

        Args:
            landmarks (Any): Facial landmark collection (MediaPipe landmark list, NumPy array, or tuple list).
            frame_shape (Optional[Tuple[int, ...]]): Optional frame shape tuple (height, width).
                If provided, converts normalized coordinates into integer pixel coordinates (N, 2).

        Returns:
            Optional[Union[List[Any], np.ndarray]]: Extracted left eye landmarks. If frame_shape is provided,
                returns NumPy array of integer pixel coordinates [[x_px, y_px], ...].
        """
        logger.debug("Extracting left eye landmarks.")
        raw_eye = self._extract_single_eye(landmarks, self.left_eye_indices)
        if raw_eye is None:
            return None

        if frame_shape is not None:
            return self.to_pixel_coordinates(raw_eye, frame_shape)
        return raw_eye

    def extract_eye_landmarks(
        self,
        landmarks: Any,
        frame_shape: Optional[Tuple[int, ...]] = None,
    ) -> Tuple[Optional[Union[List[Any], np.ndarray]], Optional[Union[List[Any], np.ndarray]]]:
        """
        Extracts landmark points for both right and left eyes separately from full facial landmarks.

        Args:
            landmarks (Any): Facial landmark collection (MediaPipe landmark list, NumPy array, or tuple list).
            frame_shape (Optional[Tuple[int, ...]]): Optional frame shape tuple (height, width).
                If provided, converts normalized coordinates into integer pixel coordinates (N, 2).

        Returns:
            Tuple[Optional[Union[List[Any], np.ndarray]], Optional[Union[List[Any], np.ndarray]]]: A tuple
                of (right_eye_landmarks, left_eye_landmarks).
        """
        logger.debug("Extracting right and left eye landmarks separately.")
        right_eye = self.extract_right_eye(landmarks, frame_shape)
        left_eye = self.extract_left_eye(landmarks, frame_shape)
        return right_eye, left_eye

    def draw_eye_landmarks(
        self,
        frame: np.ndarray,
        right_eye: Optional[Any],
        left_eye: Optional[Any],
        color: Tuple[int, int, int] = (0, 255, 255),
        radius: int = 3,
        thickness: int = -1,
    ) -> np.ndarray:
        """
        Renders eye landmark points onto the frame as circles for visual verification.

        Args:
            frame (np.ndarray): Input BGR image frame.
            right_eye (Optional[Any]): Extracted right eye landmarks (NumPy array or list of point tuples).
            left_eye (Optional[Any]): Extracted left eye landmarks (NumPy array or list of point tuples).
            color (Tuple[int, int, int]): BGR color tuple for rendering dots (default: Cyan (0, 255, 255)).
            radius (int): Circle radius in pixels.
            thickness (int): Circle outline thickness (-1 for solid filled circle).

        Returns:
            np.ndarray: Image frame with rendered eye landmark dots.
        """
        if frame is None or frame.size == 0:
            return frame

        try:
            h, w = frame.shape[:2]
            for eye_points in (right_eye, left_eye):
                if eye_points is None:
                    continue

                # Ensure pixel coordinates
                if isinstance(eye_points, (list, tuple, np.ndarray)):
                    for pt in eye_points:
                        if hasattr(pt, "x") and hasattr(pt, "y"):
                            x_px = int(round(pt.x * w)) if 0.0 <= pt.x <= 1.0 else int(round(pt.x))
                            y_px = int(round(pt.y * h)) if 0.0 <= pt.y <= 1.0 else int(round(pt.y))
                        elif isinstance(pt, (list, tuple, np.ndarray)) and len(pt) >= 2:
                            x_val, y_val = pt[0], pt[1]
                            x_px = int(round(x_val * w)) if isinstance(x_val, (float, np.floating)) and 0.0 <= x_val <= 1.0 else int(round(x_val))
                            y_px = int(round(y_val * h)) if isinstance(y_val, (float, np.floating)) and 0.0 <= y_val <= 1.0 else int(round(y_val))
                        else:
                            continue

                        cv2.circle(frame, (x_px, y_px), radius, color, thickness)

        except Exception as e:
            logger.error(f"Error rendering eye landmarks: {e}")

        return frame
