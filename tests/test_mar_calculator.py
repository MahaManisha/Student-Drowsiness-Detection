"""
Unit test suite for Phase 8.1: Mouth Aspect Ratio (MAR) Calculator.

Validates that:
1. Initialization sets correct threshold configurations.
2. validate_mouth_landmarks accurately inspects types and sizes.
3. validate_mar_value detects physiological scale anomalies.
4. calculate_mar functions as a signature placeholder returning None in this phase.
5. is_mouth_open correctly compares against thresholds.
6. get_mar_metrics compiles structured validation summaries.
"""

import pytest
import numpy as np
from detection.mar_calculator import MARCalculator


class MockLandmark:
    """Mock landmark point object."""
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y


class MockLandmarkList:
    """Mock NormalizedLandmarkList container."""
    def __init__(self, points: list) -> None:
        self.landmark = [MockLandmark(x, y) for x, y in points]


def test_mar_initialization():
    """Verify class threshold configurations."""
    # Test default
    calc = MARCalculator()
    assert calc.mar_threshold == 0.60

    # Test override
    calc_override = MARCalculator(mar_threshold=0.45)
    assert calc_override.mar_threshold == 0.45


def test_validate_mouth_landmarks():
    """Verify validation boundaries and type safety checks."""
    calc = MARCalculator()

    # 1. Valid numpy coordinates (8 points)
    valid_np = np.zeros((8, 2))
    assert calc.validate_mouth_landmarks(valid_np) is True

    # 2. Valid list of tuples (8 points)
    valid_list = [(0.1 * i, 0.2 * i) for i in range(8)]
    assert calc.validate_mouth_landmarks(valid_list) is True

    # 3. Valid Mock Landmark List
    valid_mp = MockLandmarkList(valid_list)
    assert calc.validate_mouth_landmarks(valid_mp) is True

    # 4. Insufficient points count (less than 8)
    invalid_short = np.zeros((7, 2))
    assert calc.validate_mouth_landmarks(invalid_short) is False

    # 5. Invalid types
    assert calc.validate_mouth_landmarks(None) is False
    assert calc.validate_mouth_landmarks("corrupt-string") is False


def test_validate_mar_value():
    """Verify physiological range checking."""
    calc = MARCalculator()
    assert calc.validate_mar_value(0.5) is True
    assert calc.validate_mar_value(1.8) is True
    assert calc.validate_mar_value(2.5) is False  # Above default max physiological limit 2.0
    assert calc.validate_mar_value(-0.1) is False
    assert calc.validate_mar_value(None) is False


def test_calculate_mar_formula():
    """Verify that calculate_mar computes the 8-point MAR ratio accurately."""
    calc = MARCalculator()
    
    # Setup coordinates: corners at x=0 and x=10 (width=10)
    # Verticals: pair1 height=6, pair2 height=8, pair3 height=6
    mouth_points = [
        (0, 0),   # P1 (Right Corner)
        (2, 3),   # P2 (Right Superior)
        (5, 4),   # P3 (Center Superior)
        (8, 3),   # P4 (Left Superior)
        (10, 0),  # P5 (Left Corner)
        (8, -3),  # P6 (Left Inferior)
        (5, -4),  # P7 (Center Inferior)
        (2, -3),  # P8 (Right Inferior)
    ]
    # MAR = (6 + 8 + 6) / (3.0 * 10) = 20 / 30 = 0.6667
    assert calc.calculate_mar(mouth_points) == pytest.approx(0.6667, abs=1e-4)

    # Division by zero check
    zero_width = [(0, 0)] * 8
    assert calc.calculate_mar(zero_width) == 0.0

    # Validation check
    invalid_short = np.zeros((5, 2))
    assert calc.calculate_mar(invalid_short) is None


def test_is_mouth_open():
    """Verify threshold checks for mouth openness."""
    calc = MARCalculator(mar_threshold=0.50)
    assert calc.is_mouth_open(0.55) is True
    assert calc.is_mouth_open(0.45) is False
    assert calc.is_mouth_open(None) is False


def test_get_mar_metrics():
    """Verify the metrics dictionary contains the required keys and types."""
    calc = MARCalculator(mar_threshold=0.60)
    mouth_points = [
        (0, 0), (2, 3), (5, 4), (8, 3), (10, 0), (8, -3), (5, -4), (2, -3)
    ]
    
    metrics = calc.get_mar_metrics(mouth_points)
    assert isinstance(metrics, dict)
    assert "mar" in metrics
    assert "is_mouth_open" in metrics
    assert "valid" in metrics
    
    assert metrics["mar"] == pytest.approx(0.6667, abs=1e-4)
    assert metrics["is_mouth_open"] is True
    assert metrics["valid"] is True


def test_calculate_distance():
    """Verify that calculate_distance computes Euclidean distance accurately."""
    calc = MARCalculator()

    # 1. 2D Euclidean distance (3-4-5 triangle)
    p1 = (0, 0)
    p2 = (3, 4)
    assert calc.calculate_distance(p1, p2) == pytest.approx(5.0)

    # 2. 3D Euclidean distance
    p3 = (0, 0, 0)
    p4 = (1, 1, 1)
    assert calc.calculate_distance(p3, p4) == pytest.approx(np.sqrt(3))

    # 3. Invalid inputs
    assert calc.calculate_distance(None, (1, 2)) == 0.0
    assert calc.calculate_distance((1, 2), None) == 0.0
    assert calc.calculate_distance("invalid", (1, 2)) == 0.0
