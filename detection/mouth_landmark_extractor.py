"""
Student Drowsiness Detection System - Mouth Landmark Extraction Module

This module provides the MouthLandmarkExtractor class, which is responsible for
isolating, validating, and extracting mouth-specific landmark coordinates from
facial landmark datasets (e.g., MediaPipe Face Mesh outputs).

Follows SOLID design principles:
- Single Responsibility Principle (SRP): Isolates mouth landmark processing from face mesh detection and MAR calculations.
- Open/Closed Principle (OCP): Configurable landmark index maps for flexible face mesh models.
- Dependency Inversion Principle (DIP): Operates independently of specific camera or detector implementations.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import cv2
import numpy as np

import config
from utils.logger import get_logger

logger = get_logger(__name__)

# ==============================================================================
# MEDIAPIPE FACE MESH MOUTH LANDMARK INDICES (8-POINT MAR STANDARD)
# ==============================================================================
# The standard 8-point inner lip landmark subset is selected for Mouth Aspect Ratio (MAR)
# computation. The inner lip coordinates are preferred over outer lips because they represent 
# the actual aperture of the mouth opening, making them highly sensitive to yawning and 
# decoupled from lip thickness or facial expression shifts (like smiling/frowning).
#
# Formula for future MAR calculation:
# MAR = (||P81 - P178|| + ||P13 - P14|| + ||P311 - P402||) / (3.0 * ||P78 - P308||)
#
# Horizontal Component (Denominator):
# - P78 (Index 78)  : Right Corner of the Inner Lip (viewer's left)
# - P308 (Index 308): Left Corner of the Inner Lip (viewer's right)
# Together, they establish the width of the mouth opening (||P78 - P308||).
#
# Vertical Components (Numerator):
# Right Vertical Pair:
# - P81 (Index 81)  : Right Superior Inner Lip point
# - P178 (Index 178): Right Inferior Inner Lip point
# Measures right mouth opening height (||P81 - P178||).
#
# Center Vertical Pair:
# - P13 (Index 13)  : Center Superior Inner Lip point
# - P14 (Index 14)  : Center Inferior Inner Lip point
# Measures center mouth opening height (||P13 - P14||).
#
# Left Vertical Pair:
# - P311 (Index 311): Left Superior Inner Lip point
# - P402 (Index 402): Left Inferior Inner Lip point
# Measures left mouth opening height (||P311 - P402||).
#
# Using three vertical pairs instead of one ensures that asymmetrical mouth movements 
# (e.g. talking, smirking, or head tilt distortion) are averaged out, providing a stable 
# yawn signature.
MOUTH_INNER_LIP_INDICES: List[int] = getattr(
    config, "MOUTH_INNER_LIP_INDICES", [78, 81, 13, 311, 308, 402, 14, 178]
)

# Standard 8-point outer lip boundary landmarks for visual alignment/overlay drawing only
MOUTH_OUTER_LIP_INDICES: List[int] = getattr(
    config, "MOUTH_OUTER_LIP_INDICES", [61, 37, 0, 267, 291, 321, 17, 91]
)


class MouthLandmarkExtractor:
    """
    Independent extractor for isolating and formatting inner and outer mouth landmark coordinates.

    This class is designed to process general face landmark coordinates (e.g., MediaPipe 468/478
    3D mesh outputs or custom landmark arrays) and extract subset landmark points corresponding
    to the lips for Mouth Aspect Ratio (MAR) and yawn tracking in future milestones.
    """

    def __init__(
        self,
        inner_lip_indices: Optional[List[int]] = None,
        outer_lip_indices: Optional[List[int]] = None,
    ) -> None:
        """
        Initializes the MouthLandmarkExtractor with configurable landmark indices.

        Args:
            inner_lip_indices (Optional[List[int]]): List of landmark indices corresponding to the inner lip.
                Defaults to MediaPipe standard 8-point inner lip indices.
            outer_lip_indices (Optional[List[int]]): List of landmark indices corresponding to the outer lip.
                Defaults to MediaPipe standard 8-point outer lip indices.
        """
        self.inner_lip_indices: List[int] = (
            list(inner_lip_indices) if inner_lip_indices is not None else MOUTH_INNER_LIP_INDICES
        )
        self.outer_lip_indices: List[int] = (
            list(outer_lip_indices) if outer_lip_indices is not None else MOUTH_OUTER_LIP_INDICES
        )

        logger.info(
            f"MouthLandmarkExtractor initialized with {len(self.inner_lip_indices)} inner lip indices "
            f"and {len(self.outer_lip_indices)} outer lip indices."
        )

    def validate_landmarks(self, landmarks: Any) -> bool:
        """
        Validates whether the provided facial landmarks object is structurally valid and contains
        sufficient data points for mouth landmark extraction.

        Args:
            landmarks (Any): Facial landmark collection to validate. Can be a MediaPipe
                NormalizedLandmarkList, a list/tuple of coordinates, or a NumPy coordinate array.

        Returns:
            bool: True if landmarks are valid and non-empty, False otherwise.
        """
        if landmarks is None:
            logger.warning("Landmarks object is None.")
            return False

        try:
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

            max_required_index = max(self.inner_lip_indices + self.outer_lip_indices)
            if count <= max_required_index:
                logger.warning(
                    f"Landmarks count ({count}) is insufficient for max required mouth index ({max_required_index})."
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating landmarks: {e}")
            return False

    def _extract_single_boundary(self, landmarks: Any, indices: List[int]) -> Optional[Any]:
        """
        Internal helper to isolate landmark points for a single lip boundary given target indices.

        Args:
            landmarks (Any): Facial landmark collection.
            indices (List[int]): Predefined index mapping for the target boundary.

        Returns:
            Optional[Any]: Extracted mouth landmarks matching input element structure,
                or None if extraction fails.
        """
        if not self.validate_landmarks(landmarks):
            return None

        try:
            if hasattr(landmarks, "landmark"):
                return [landmarks.landmark[i] for i in indices]
            elif isinstance(landmarks, np.ndarray):
                return landmarks[indices]
            elif isinstance(landmarks, (list, tuple)):
                return [landmarks[i] for i in indices]
            else:
                return None
        except Exception as e:
            logger.error(f"Error extracting mouth landmarks for indices {indices}: {e}")
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

            if isinstance(landmarks, (list, tuple)):
                coords = []
                for lm in landmarks:
                    if hasattr(lm, "x") and hasattr(lm, "y"):
                        x_val, y_val = lm.x, lm.y
                    elif isinstance(lm, (list, tuple, np.ndarray)) and len(lm) >= 2:
                        x_val, y_val = lm[0], lm[1]
                    else:
                        logger.warning(f"Unrecognized landmark item format: {lm}")
                        return None

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

            elif isinstance(landmarks, np.ndarray):
                if landmarks.size == 0 or landmarks.ndim != 2 or landmarks.shape[1] < 2:
                    logger.warning(f"Invalid NumPy landmarks shape for pixel conversion: {landmarks.shape}")
                    return None

                if np.issubdtype(landmarks.dtype, np.floating) and np.max(landmarks[:, :2]) <= 1.0:
                    px_x = np.round(landmarks[:, 0] * w).astype(np.int32)
                    px_y = np.round(landmarks[:, 1] * h).astype(np.int32)
                    return np.column_stack((px_x, px_y))
                else:
                    return np.round(landmarks[:, :2]).astype(np.int32)

            else:
                logger.warning(f"Unsupported landmark container type for pixel conversion: {type(landmarks)}")
                return None

        except Exception as e:
            logger.error(f"Error converting landmarks to pixel coordinates: {e}")
            return None

    def extract_inner_lip(
        self,
        landmarks: Any,
        frame_shape: Optional[Tuple[int, ...]] = None,
    ) -> Optional[Union[List[Any], np.ndarray]]:
        """
        Extracts landmark points for the inner lip from full facial landmarks.

        Args:
            landmarks (Any): Facial landmark collection.
            frame_shape (Optional[Tuple[int, ...]]): Optional frame shape tuple (height, width).
                If provided, converts normalized coordinates into integer pixel coordinates.

        Returns:
            Optional[Union[List[Any], np.ndarray]]: Extracted inner lip landmarks.
        """
        logger.debug("Extracting inner lip landmarks.")
        raw_lip = self._extract_single_boundary(landmarks, self.inner_lip_indices)
        if raw_lip is None:
            return None

        if frame_shape is not None:
            return self.to_pixel_coordinates(raw_lip, frame_shape)
        return raw_lip

    def extract_outer_lip(
        self,
        landmarks: Any,
        frame_shape: Optional[Tuple[int, ...]] = None,
    ) -> Optional[Union[List[Any], np.ndarray]]:
        """
        Extracts landmark points for the outer lip from full facial landmarks.

        Args:
            landmarks (Any): Facial landmark collection.
            frame_shape (Optional[Tuple[int, ...]]): Optional frame shape tuple (height, width).
                If provided, converts normalized coordinates into integer pixel coordinates.

        Returns:
            Optional[Union[List[Any], np.ndarray]]: Extracted outer lip landmarks.
        """
        logger.debug("Extracting outer lip landmarks.")
        raw_lip = self._extract_single_boundary(landmarks, self.outer_lip_indices)
        if raw_lip is None:
            return None

        if frame_shape is not None:
            return self.to_pixel_coordinates(raw_lip, frame_shape)
        return raw_lip

    def extract_mouth_landmarks(
        self,
        landmarks: Any,
        frame_shape: Optional[Tuple[int, ...]] = None,
    ) -> Tuple[Optional[Union[List[Any], np.ndarray]], Optional[Union[List[Any], np.ndarray]]]:
        """
        Extracts landmark points for both inner and outer lip boundaries from full facial landmarks.

        Args:
            landmarks (Any): Facial landmark collection.
            frame_shape (Optional[Tuple[int, ...]]): Optional frame shape tuple.

        Returns:
            Tuple[Optional[Union[List[Any], np.ndarray]], Optional[Union[List[Any], np.ndarray]]]: A tuple
                of (inner_lip_landmarks, outer_lip_landmarks).
        """
        logger.debug("Extracting inner and outer lip landmarks separately.")
        inner_lip = self.extract_inner_lip(landmarks, frame_shape)
        outer_lip = self.extract_outer_lip(landmarks, frame_shape)
        return inner_lip, outer_lip

    def draw_mouth_landmarks(
        self,
        frame: np.ndarray,
        inner_lip: Optional[Any],
        outer_lip: Optional[Any],
        color: Tuple[int, int, int] = (255, 0, 255),
        radius: int = 2,
        thickness: int = -1,
    ) -> np.ndarray:
        """
        Renders mouth landmark points onto the frame as circles for visual verification.

        Args:
            frame (np.ndarray): Input BGR image frame.
            inner_lip (Optional[Any]): Extracted inner lip landmarks.
            outer_lip (Optional[Any]): Extracted outer lip landmarks.
            color (Tuple[int, int, int]): BGR color tuple for rendering dots (default: Magenta (255, 0, 255)).
            radius (int): Circle radius in pixels.
            thickness (int): Circle outline thickness (-1 for solid filled circle).

        Returns:
            np.ndarray: Image frame with rendered mouth landmark dots.
        """
        if frame is None or frame.size == 0:
            return frame

        try:
            h, w = frame.shape[:2]
            for lip_points in (inner_lip, outer_lip):
                if lip_points is None:
                    continue

                if isinstance(lip_points, (list, tuple, np.ndarray)):
                    for pt in lip_points:
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
            logger.error(f"Error rendering mouth landmarks: {e}")

        return frame
