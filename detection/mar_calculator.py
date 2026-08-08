"""
Student Drowsiness Detection System - Mouth Aspect Ratio (MAR) Calculator Module

This module provides the MARCalculator class, which serves as the core geometric
analysis component for computing Mouth Aspect Ratio (MAR) from 2D/3D facial landmark
coordinates. MAR is a key computer vision metric used to evaluate mouth openness,
detect yawning patterns, and identify signs of fatigue in real time.

Follows SOLID design principles:
- Single Responsibility Principle (SRP): Focuses exclusively on Mouth Aspect Ratio (MAR) interface contracts,
  landmark point set validation, threshold evaluation, and mouth state determination.
- Open/Closed Principle (OCP): Supports configurable mouth openness thresholds and extensible
  distance metrics without requiring modification of existing calculation workflows.
- Liskov Substitution Principle (LSP): Maintains strict, predictable return types and parameter
  contracts across all calculation interfaces.
- Interface Segregation Principle (ISP): Exposes granular public methods so callers consume only necessary functionality.
- Dependency Inversion Principle (DIP): Decoupled from camera hardware, GUI frameworks, and specific
  facial detector models by operating strictly on standard coordinate arrays/sequences.

Note:
This module contains the architectural skeleton, method interfaces, type contracts,
input validation logic, and logging setup for Phase 8.1.
The actual mathematical calculations (Euclidean distance, 8-point MAR ratio) will be implemented in Phase 8.2.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import sys
import pathlib

ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import config
from utils.geometry import calculate_euclidean_distance
try:
    from utils.logger import get_logger
    logger = get_logger(__name__)
except Exception:
    import logging
    logger = logging.getLogger(__name__)

# Default MAR threshold fallback from central config (yawning threshold)
DEFAULT_MAR_THRESHOLD: float = getattr(config, "MAR_THRESHOLD", 0.60)

# Standard 8-point inner lip landmark requirement for MAR calculation
STANDARD_8_POINT_MOUTH_COUNT: int = 8


class MARCalculator:
    """
    Independent calculator for computing Mouth Aspect Ratio (MAR) geometric metrics from mouth landmarks.

    The Mouth Aspect Ratio (MAR) is calculated using 8 inner lip landmark points:
    - P1 (Index 0): Right Corner of the Inner Lip
    - P2 (Index 1): Right Superior Inner Lip
    - P3 (Index 2): Center Superior Inner Lip
    - P4 (Index 3): Left Superior Inner Lip
    - P5 (Index 4): Left Corner of the Inner Lip
    - P6 (Index 5): Left Inferior Inner Lip
    - P7 (Index 6): Center Inferior Inner Lip
    - P8 (Index 7): Right Inferior Inner Lip

    Proposed MAR Formula:
        MAR = (||P2 - P8|| + ||P3 - P7|| + ||P4 - P6||) / (3.0 * ||P1 - P5||)

    Attributes:
        mar_threshold (float): Threshold value above which a mouth is classified as open.
    """

    def __init__(self, mar_threshold: Optional[float] = None) -> None:
        """
        Initializes the MARCalculator with configurable threshold parameters and tracking state.

        Args:
            mar_threshold (Optional[float]): Threshold value above which the mouth is considered open/yawning.
                Defaults to config.MAR_THRESHOLD or 0.60 if not specified.
        """
        self.mar_threshold: float = (
            float(mar_threshold) if mar_threshold is not None else DEFAULT_MAR_THRESHOLD
        )
        self.frame_counter: int = 0

        logger.info(f"MARCalculator initialized with MAR threshold: {self.mar_threshold:.3f}")

    def calculate_distance(self, p1: Any, p2: Any) -> float:
        """
        Computes the Euclidean distance between two coordinate points.

        Delegates to the shared geometry vector math utilities to preserve consistency
        and avoid duplicate implementation.

        Args:
            p1 (Any): First coordinate point (x, y) or landmark object.
            p2 (Any): Second coordinate point (x, y) or landmark object.

        Returns:
            float: Euclidean distance between the points, or 0.0 if inputs are invalid.
        """
        if p1 is None or p2 is None:
            logger.warning("Coordinate input is None for Euclidean distance computation.")
            return 0.0

        try:
            return calculate_euclidean_distance(p1, p2)
        except Exception as e:
            logger.error(f"Error calculating Euclidean distance between points: {e}")
            return 0.0

    def validate_mar_value(
        self,
        mar_value: Optional[float],
        min_valid: float = 0.0,
        max_valid: float = 2.0,
    ) -> bool:
        """
        Validates whether a calculated MAR value falls within realistic physiological bounds.

        Args:
            mar_value (Optional[float]): MAR value to validate.
            min_valid (float): Minimum valid MAR bound (default: 0.0).
            max_valid (float): Maximum valid MAR bound (default: 2.0).

        Returns:
            bool: True if value is within physiological range, False otherwise.
        """
        if mar_value is None:
            return False

        if min_valid <= mar_value <= max_valid:
            return True
        else:
            logger.warning(
                f"Abnormal MAR value detected: {mar_value:.4f} (outside expected range [{min_valid:.1f}, {max_valid:.1f}])."
            )
            return False

    def validate_mouth_landmarks(self, mouth_landmarks: Any) -> bool:
        """
        Validates whether the provided mouth landmarks structure is non-empty and contains
        at least 8 landmark points required for 8-point MAR computation.

        Args:
            mouth_landmarks (Any): Mouth landmark points (list of coordinate tuples/objects or NumPy array).

        Returns:
            bool: True if landmarks are valid and contain at least 8 points, False otherwise.
        """
        if mouth_landmarks is None:
            logger.warning("Mouth landmarks input is None.")
            return False

        try:
            if isinstance(mouth_landmarks, np.ndarray):
                point_count = mouth_landmarks.shape[0]
            elif isinstance(mouth_landmarks, (list, tuple)):
                point_count = len(mouth_landmarks)
            elif hasattr(mouth_landmarks, "landmark"):
                point_count = len(mouth_landmarks.landmark)
            else:
                logger.warning(f"Unsupported mouth landmarks type: {type(mouth_landmarks)}")
                return False

            if point_count < STANDARD_8_POINT_MOUTH_COUNT:
                logger.warning(
                    f"Insufficient mouth landmark points: received {point_count}, "
                    f"expected at least {STANDARD_8_POINT_MOUTH_COUNT}."
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating mouth landmarks: {e}")
            return False

    def calculate_mar(self, mouth_landmarks: Any) -> Optional[float]:
        """
        Computes the Mouth Aspect Ratio (MAR) for the given mouth landmarks.

        Landmark Index Mapping (8-point inner lip):
            P1 (Index 0): Right Corner of the Inner Lip
            P2 (Index 1): Right Superior Inner Lip
            P3 (Index 2): Center Superior Inner Lip
            P4 (Index 3): Left Superior Inner Lip
            P5 (Index 4): Left Corner of the Inner Lip
            P6 (Index 5): Left Inferior Inner Lip
            P7 (Index 6): Center Inferior Inner Lip
            P8 (Index 7): Right Inferior Inner Lip

        Formula:
            MAR = (||P2 - P8|| + ||P3 - P7|| + ||P4 - P6||) / (3.0 * ||P1 - P5||)

        Args:
            mouth_landmarks (Any): 8 landmark coordinates corresponding to the mouth
                (MediaPipe landmark objects, list of point tuples/lists, or NumPy array).

        Returns:
            Optional[float]: Computed Mouth Aspect Ratio (MAR) as a float, or None if validation fails.
        """
        if not self.validate_mouth_landmarks(mouth_landmarks):
            logger.warning("MAR calculation skipped due to invalid landmark input.")
            return None

        try:
            # Extract point list handling MediaPipe LandmarkList or standard sequences
            if hasattr(mouth_landmarks, "landmark"):
                pts = mouth_landmarks.landmark
            else:
                pts = mouth_landmarks

            p1, p2, p3, p4, p5, p6, p7, p8 = pts[0], pts[1], pts[2], pts[3], pts[4], pts[5], pts[6], pts[7]

            # Compute vertical distances between superior and inferior pairs
            v1 = self.calculate_distance(p2, p8)
            v2 = self.calculate_distance(p3, p7)
            v3 = self.calculate_distance(p4, p6)

            # Compute horizontal distance between mouth corners
            h = self.calculate_distance(p1, p5)

            # Division-by-zero protection
            if h <= 1e-6:
                logger.warning(
                    f"Horizontal mouth distance is near zero ({h:.6f}); division by zero prevented."
                )
                return 0.0

            # Calculate average vertical-to-horizontal aspect ratio
            mar = (v1 + v2 + v3) / (3.0 * h)
            logger.debug(f"Computed mouth MAR: {mar:.4f} (v1={v1:.2f}, v2={v2:.2f}, v3={v3:.2f}, h={h:.2f})")
            return float(mar)

        except Exception as e:
            logger.error(f"Error calculating mouth MAR: {e}")
            return None

    def is_mouth_open(self, mar_value: Optional[float], threshold: Optional[float] = None) -> bool:
        """
        Determines whether the mouth is open based on whether the MAR value is above a specified threshold.

        Args:
            mar_value (Optional[float]): Calculated MAR value to test.
            threshold (Optional[float]): Optional threshold override. If None, uses self.mar_threshold.

        Returns:
            bool: True if mar_value is greater than the threshold (mouth open), False otherwise.
        """
        if mar_value is None:
            return False

        eval_threshold = threshold if threshold is not None else self.mar_threshold
        return mar_value > eval_threshold

    def get_mar_metrics(self, mouth_landmarks: Any) -> Dict[str, Any]:
        """
        Generates a summary dictionary containing the MAR value, mouth openness status flag,
        and validation flag.

        Args:
            mouth_landmarks (Any): Landmark points for the mouth.

        Returns:
            Dict[str, Any]: Structured dictionary with key metrics:
                - "mar": Optional[float] (always None in Phase 8.1)
                - "is_mouth_open": bool (always False in Phase 8.1 since MAR is None)
                - "valid": bool
        """
        mar_val = self.calculate_mar(mouth_landmarks)
        is_open = self.is_mouth_open(mar_val)
        is_valid = self.validate_mouth_landmarks(mouth_landmarks)

        return {
            "mar": mar_val,
            "is_mouth_open": is_open,
            "valid": is_valid,
        }
