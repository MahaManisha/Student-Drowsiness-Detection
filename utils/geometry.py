"""
Student Drowsiness Detection System - Geometry & Vector Math Utilities

This module provides high-performance, reusable geometric and vector math calculation
functions for processing 2D and 3D facial landmarks.

It is designed to be shared across all vision detection modules, including:
- Eye Aspect Ratio (EAR) calculation (Phase 4)
- Mouth Aspect Ratio (MAR) calculation for yawning detection (Phase 5)
- Head Pose Estimation (Pitch/Yaw/Roll angle calculations) (Phase 6)
"""

from typing import Any, Optional, Tuple
import math
import sys
import pathlib
import numpy as np

ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from utils.logger import get_logger
    logger = get_logger(__name__)
except Exception:
    import logging
    logger = logging.getLogger(__name__)


def _extract_point_coordinates(point: Any) -> Optional[Tuple[float, float, Optional[float]]]:
    """
    Internal helper function to parse and extract (x, y) or (x, y, z) float coordinates
    from diverse point formats (tuples, lists, NumPy arrays, or MediaPipe landmark objects).

    Args:
        point (Any): Point coordinate input.

    Returns:
        Optional[Tuple[float, float, Optional[float]]]: Extracted (x, y, z) coordinate tuple,
            where z is float or None. Returns None if parsing fails or input is invalid.
    """
    if point is None:
        return None

    try:
        # MediaPipe landmark object or custom object with .x and .y attributes
        if hasattr(point, "x") and hasattr(point, "y"):
            x_val = float(point.x)
            y_val = float(point.y)
            z_val = float(point.z) if hasattr(point, "z") and point.z is not None else None
            return x_val, y_val, z_val

        # Sequence types: list, tuple, or NumPy array
        if isinstance(point, (list, tuple, np.ndarray)):
            if len(point) < 2:
                logger.warning(f"Point coordinate sequence contains fewer than 2 elements: {point}")
                return None
            x_val = float(point[0])
            y_val = float(point[1])
            z_val = float(point[2]) if len(point) >= 3 else None
            return x_val, y_val, z_val

        logger.warning(f"Unsupported point coordinate type: {type(point)}")
        return None

    except (ValueError, TypeError, IndexError) as e:
        logger.warning(f"Failed to extract numerical coordinates from point {point}: {e}")
        return None


def calculate_euclidean_distance(p1: Any, p2: Any) -> float:
    """
    Calculates the Euclidean distance between two 2D or 3D spatial points.

    Supports diverse coordinate formats:
    - 2D/3D tuple or list: (x, y) or (x, y, z)
    - NumPy array: np.array([x, y]) or np.array([x, y, z])
    - MediaPipe landmark object with x, y, (z) attributes

    Formulas:
        2D Distance = sqrt((x2 - x1)^2 + (y2 - y1)^2)
        3D Distance = sqrt((x2 - x1)^2 + (y2 - y1)^2 + (z2 - z1)^2)

    Args:
        p1 (Any): First coordinate point.
        p2 (Any): Second coordinate point.

    Returns:
        float: Calculated Euclidean distance as a floating-point value.
            Returns 0.0 if input validation fails or coordinates are invalid.
    """
    coords1 = _extract_point_coordinates(p1)
    coords2 = _extract_point_coordinates(p2)

    if coords1 is None or coords2 is None:
        logger.warning(f"Invalid point inputs for Euclidean distance computation: p1={p1}, p2={p2}")
        return 0.0

    x1, y1, z1 = coords1
    x2, y2, z2 = coords2

    dx = x2 - x1
    dy = y2 - y1

    # 3D Euclidean distance if z coordinates are present for both points
    if z1 is not None and z2 is not None:
        dz = z2 - z1
        distance = math.sqrt(dx * dx + dy * dy + dz * dz)
    else:
        # 2D Euclidean distance
        distance = math.hypot(dx, dy)

    return float(distance)
