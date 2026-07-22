"""
Student Drowsiness Detection System - Eye Aspect Ratio (EAR) Calculator Module

This module provides the EARCalculator class, which serves as the core geometric
analysis component for computing Eye Aspect Ratio (EAR) from 2D/3D facial landmark
coordinates. EAR is a key computer vision metric used to evaluate eye openness,
detect blinking patterns, and identify signs of ocular fatigue and drowsiness in real time.

Follows SOLID design principles:
- Single Responsibility Principle (SRP): Focuses exclusively on Eye Aspect Ratio (EAR) computation,
  landmark point set validation, threshold evaluation, and eye state determination.
- Open/Closed Principle (OCP): Supports configurable eye closure thresholds and extensible
  distance metrics without requiring modification of existing calculation workflows.
- Liskov Substitution Principle (LSP): Maintains strict, predictable return types and parameter
  contracts across all calculation interfaces (single-eye, dual-eye, and metric summaries).
- Interface Segregation Principle (ISP): Exposes granular public methods (e.g., calculate_single_eye_ear,
  calculate_avg_ear, is_eye_closed, get_ear_metrics) so callers consume only necessary functionality.
- Dependency Inversion Principle (DIP): Decoupled from camera hardware, GUI frameworks, and specific
  facial detector models by operating strictly on standard coordinate arrays/sequences.

Note:
This module contains the architectural skeleton, method interfaces, type contracts,
input validation logic, and logging setup for Phase 4.1.
The actual mathematical calculations (Euclidean distance, 6-point EAR ratio) will be implemented in Phase 4.2.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

import config
from utils.geometry import calculate_euclidean_distance
from utils.logger import get_logger

logger = get_logger(__name__)

# Default EAR threshold fallback from central config
DEFAULT_EAR_THRESHOLD: float = getattr(config, "EAR_THRESHOLD", 0.25)

# Standard 6-point eye landmark requirement for EAR calculation
STANDARD_6_POINT_EYE_COUNT: int = 6


class EARCalculator:
    """
    Independent calculator for computing Eye Aspect Ratio (EAR) geometric metrics from eye landmarks.

    The Eye Aspect Ratio (EAR) is calculated using 6 perimeter landmark points per eye:
    - P1 (Outer Canthus / Corner)
    - P2 (Superior Eyelid Point 1)
    - P3 (Superior Eyelid Point 2)
    - P4 (Inner Canthus / Corner)
    - P5 (Inferior Eyelid Point 2)
    - P6 (Inferior Eyelid Point 1)

    Standard EAR Formula:
        EAR = (||P2 - P6|| + ||P3 - P5||) / (2.0 * ||P1 - P4||)

    Attributes:
        ear_threshold (float): Threshold value below which an eye is classified as closed.
    """

    def __init__(self, ear_threshold: Optional[float] = None) -> None:
        """
        Initializes the EARCalculator with configurable threshold parameters.

        Args:
            ear_threshold (Optional[float]): Threshold value below which the eye is considered closed.
                Defaults to config.EAR_THRESHOLD or 0.25 if not specified.
        """
        self.ear_threshold: float = (
            float(ear_threshold) if ear_threshold is not None else DEFAULT_EAR_THRESHOLD
        )
        logger.info(f"EARCalculator initialized with EAR threshold: {self.ear_threshold:.3f}")

    def validate_eye_landmarks(self, eye_landmarks: Any) -> bool:
        """
        Validates whether the provided eye landmarks structure is non-empty and contains
        at least 6 landmark points required for 6-point EAR computation.

        Args:
            eye_landmarks (Any): Eye landmark points (list of coordinate tuples/objects or NumPy array).

        Returns:
            bool: True if landmarks are valid and contain at least 6 points, False otherwise.
        """
        if eye_landmarks is None:
            logger.warning("Eye landmarks input is None.")
            return False

        try:
            if isinstance(eye_landmarks, np.ndarray):
                point_count = eye_landmarks.shape[0]
            elif isinstance(eye_landmarks, (list, tuple)):
                point_count = len(eye_landmarks)
            elif hasattr(eye_landmarks, "landmark"):
                point_count = len(eye_landmarks.landmark)
            else:
                logger.warning(f"Unsupported eye landmarks type: {type(eye_landmarks)}")
                return False

            if point_count < STANDARD_6_POINT_EYE_COUNT:
                logger.warning(
                    f"Insufficient eye landmark points: received {point_count}, "
                    f"expected at least {STANDARD_6_POINT_EYE_COUNT}."
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating eye landmarks: {e}")
            return False

    def calculate_euclidean_distance(self, p1: Any, p2: Any) -> float:
        """
        Calculates the Euclidean distance between two 2D or 3D spatial points.

        Delegates to the shared utils.geometry distance calculation utility.

        Args:
            p1 (Any): First landmark point coordinate (x, y) or (x, y, z) or landmark object.
            p2 (Any): Second landmark point coordinate (x, y) or (x, y, z) or landmark object.

        Returns:
            float: Calculated Euclidean distance as a float.
        """
        return calculate_euclidean_distance(p1, p2)


    def calculate_single_eye_ear(self, eye_landmarks: Any) -> Optional[float]:
        """
        Computes the Eye Aspect Ratio (EAR) for a single eye given 6 perimeter landmark points
        using the standard Soukupová & Čech (2016) formula.

        Landmark Index Mapping (6-point perimeter):
            P1 (Index 0): Outer/Inner Canthus (Corner 1)
            P2 (Index 1): Superior Eyelid Point 1 (Top-Right)
            P3 (Index 2): Superior Eyelid Point 2 (Top-Left)
            P4 (Index 3): Inner/Outer Canthus (Corner 2)
            P5 (Index 4): Inferior Eyelid Point 2 (Bottom-Left)
            P6 (Index 5): Inferior Eyelid Point 1 (Bottom-Right)

        Formula:
            EAR = (||P2 - P6|| + ||P3 - P5||) / (2.0 * ||P1 - P4||)

        Args:
            eye_landmarks (Any): 6 landmark coordinates corresponding to one eye
                (MediaPipe landmark objects, list of point tuples/lists, or NumPy array).

        Returns:
            Optional[float]: Computed Eye Aspect Ratio (EAR) as a float, or None if validation fails.
        """
        if not self.validate_eye_landmarks(eye_landmarks):
            logger.warning("Single eye EAR calculation skipped due to invalid landmark input.")
            return None

        try:
            # Extract point list handling MediaPipe LandmarkList or standard sequences
            if hasattr(eye_landmarks, "landmark"):
                pts = eye_landmarks.landmark
            else:
                pts = eye_landmarks

            p1, p2, p3, p4, p5, p6 = pts[0], pts[1], pts[2], pts[3], pts[4], pts[5]

            # Compute vertical distances between eyelid pairs
            v1 = self.calculate_euclidean_distance(p2, p6)
            v2 = self.calculate_euclidean_distance(p3, p5)

            # Compute horizontal distance between eye corners
            h = self.calculate_euclidean_distance(p1, p4)

            # Division-by-zero protection
            if h <= 1e-6:
                logger.warning(
                    f"Horizontal eye distance is near zero ({h:.6f}); division by zero prevented."
                )
                return 0.0

            # Calculate standard Soukupová & Čech EAR
            ear = (v1 + v2) / (2.0 * h)
            logger.debug(f"Computed single eye EAR: {ear:.4f} (v1={v1:.2f}, v2={v2:.2f}, h={h:.2f})")
            return float(ear)

        except Exception as e:
            logger.error(f"Error calculating single eye EAR: {e}")
            return None

    def calculate_ear(
        self,
        right_eye_landmarks: Any,
        left_eye_landmarks: Any,
    ) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """
        Computes EAR values for both right and left eyes, as well as their combined average.

        Args:
            right_eye_landmarks (Any): Landmark points for the right eye.
            left_eye_landmarks (Any): Landmark points for the left eye.

        Returns:
            Tuple[Optional[float], Optional[float], Optional[float]]:
                A tuple of (right_ear, left_ear, avg_ear). Elements are None if extraction/validation fails.
        """
        right_ear = self.calculate_single_eye_ear(right_eye_landmarks)
        left_ear = self.calculate_single_eye_ear(left_eye_landmarks)
        avg_ear = self.calculate_avg_ear(right_ear, left_ear)

        return right_ear, left_ear, avg_ear


    def calculate_avg_ear(
        self,
        right_ear: Optional[float],
        left_ear: Optional[float],
    ) -> Optional[float]:
        """
        Computes the arithmetic average of right and left Eye Aspect Ratios.

        Args:
            right_ear (Optional[float]): EAR value for the right eye.
            left_ear (Optional[float]): EAR value for the left eye.

        Returns:
            Optional[float]: Average EAR value, or individual EAR if only one eye is valid, or None if both are None.
        """
        if right_ear is not None and left_ear is not None:
            return (right_ear + left_ear) / 2.0
        elif right_ear is not None:
            return right_ear
        elif left_ear is not None:
            return left_ear
        else:
            return None

    def is_eye_closed(
        self,
        ear_value: Optional[float],
        threshold: Optional[float] = None,
    ) -> bool:
        """
        Determines whether an eye is closed based on whether the EAR value is below a specified threshold.

        Args:
            ear_value (Optional[float]): Calculated EAR value to test.
            threshold (Optional[float]): Optional threshold override. If None, uses self.ear_threshold.

        Returns:
            bool: True if ear_value is less than the threshold (eye closed), False otherwise.
        """
        if ear_value is None:
            return False

        eval_threshold = threshold if threshold is not None else self.ear_threshold
        return ear_value < eval_threshold

    def get_ear_metrics(
        self,
        right_eye_landmarks: Any,
        left_eye_landmarks: Any,
    ) -> Dict[str, Any]:
        """
        Generates a comprehensive summary dictionary containing individual and average EAR values,
        eye closure status flags, and frame-level metrics.

        Args:
            right_eye_landmarks (Any): Landmark points for the right eye.
            left_eye_landmarks (Any): Landmark points for the left eye.

        Returns:
            Dict[str, Any]: Structured dictionary with the following key metrics:
                - "right_ear": Optional[float]
                - "left_ear": Optional[float]
                - "avg_ear": Optional[float]
                - "is_right_closed": bool
                - "is_left_closed": bool
                - "is_both_closed": bool
                - "valid": bool
        """
        right_ear, left_ear, avg_ear = self.calculate_ear(
            right_eye_landmarks, left_eye_landmarks
        )

        is_right_closed = self.is_eye_closed(right_ear)
        is_left_closed = self.is_eye_closed(left_ear)
        is_both_closed = is_right_closed and is_left_closed
        is_valid = right_ear is not None or left_ear is not None

        return {
            "right_ear": right_ear,
            "left_ear": left_ear,
            "avg_ear": avg_ear,
            "is_right_closed": is_right_closed,
            "is_left_closed": is_left_closed,
            "is_both_closed": is_both_closed,
            "valid": is_valid,
        }
