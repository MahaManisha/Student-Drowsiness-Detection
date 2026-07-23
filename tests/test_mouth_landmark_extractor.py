"""
Unit test suite for Phase 7.1: Mouth Landmark Extractor.

Validates that:
1. Initialization sets correct defaults and custom index maps.
2. validate_landmarks verifies MediaPipe objects, lists, tuples, and NumPy arrays.
3. extract_inner_lip and extract_outer_lip isolate indices correctly.
4. to_pixel_coordinates performs scaling or returns absolute points safely.
5. draw_mouth_landmarks executes rendering without crashes.
"""

import pytest
import numpy as np
from detection.mouth_landmark_extractor import MouthLandmarkExtractor


class MockLandmark:
    """Mock MediaPipe Landmark object containing x and y coordinates."""
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y


class MockNormalizedLandmarkList:
    """Mock MediaPipe NormalizedLandmarkList containing a list of landmarks."""
    def __init__(self, coordinates: list) -> None:
        self.landmark = [MockLandmark(x, y) for x, y in coordinates]


def test_extractor_initialization():
    """Verify default and custom initialization values."""
    # Test default
    extractor = MouthLandmarkExtractor()
    assert len(extractor.inner_lip_indices) == 8
    assert len(extractor.outer_lip_indices) == 8
    assert extractor.inner_lip_indices[0] == 78
    assert extractor.outer_lip_indices[0] == 61

    # Test custom
    extractor_custom = MouthLandmarkExtractor(inner_lip_indices=[1, 2, 3], outer_lip_indices=[4, 5])
    assert extractor_custom.inner_lip_indices == [1, 2, 3]
    assert extractor_custom.outer_lip_indices == [4, 5]


def test_validate_landmarks():
    """Verify landmarks structures and types are validated accurately."""
    extractor = MouthLandmarkExtractor(inner_lip_indices=[0, 1], outer_lip_indices=[2, 3])

    # 1. Valid MediaPipe object structure (4 landmarks)
    coord_list = [(0.1, 0.2), (0.3, 0.4), (0.5, 0.6), (0.7, 0.8)]
    mp_landmarks = MockNormalizedLandmarkList(coord_list)
    assert extractor.validate_landmarks(mp_landmarks) is True

    # 2. Valid NumPy array
    np_landmarks = np.array(coord_list)
    assert extractor.validate_landmarks(np_landmarks) is True

    # 3. Valid List/Tuple list
    assert extractor.validate_landmarks(coord_list) is True

    # 4. None validation
    assert extractor.validate_landmarks(None) is False

    # 5. Unsupported type
    assert extractor.validate_landmarks("invalid-string") is False

    # 6. Insufficient count (requires at least max index + 1 = 4 points)
    insufficient_mp = MockNormalizedLandmarkList([(0.1, 0.2), (0.3, 0.4), (0.5, 0.6)])
    assert extractor.validate_landmarks(insufficient_mp) is False


def test_extract_boundaries():
    """Verify correct subset extraction for inner and outer lip boundaries."""
    extractor = MouthLandmarkExtractor(inner_lip_indices=[0, 2], outer_lip_indices=[1, 3])
    coord_list = [(0.1, 0.2), (0.3, 0.4), (0.5, 0.6), (0.7, 0.8)]
    
    # Extract from list
    inner_extracted = extractor.extract_inner_lip(coord_list)
    outer_extracted = extractor.extract_outer_lip(coord_list)
    assert inner_extracted == [coord_list[0], coord_list[2]]
    assert outer_extracted == [coord_list[1], coord_list[3]]

    # Extract from MediaPipe mock
    mp_landmarks = MockNormalizedLandmarkList(coord_list)
    inner_mp = extractor.extract_inner_lip(mp_landmarks)
    assert len(inner_mp) == 2
    assert inner_mp[0].x == 0.1
    assert inner_mp[1].x == 0.5


def test_to_pixel_coordinates():
    """Verify coordinate scaling to absolute image coordinates."""
    extractor = MouthLandmarkExtractor()
    normalized_list = [(0.1, 0.2), (0.5, 0.6)]
    frame_shape = (480, 640)  # Height, Width

    # Scale normalized coordinates
    pixels = extractor.to_pixel_coordinates(normalized_list, frame_shape)
    assert isinstance(pixels, np.ndarray)
    # 0.1 * 640 = 64, 0.2 * 480 = 96
    # 0.5 * 640 = 320, 0.6 * 480 = 288
    assert pixels[0][0] == 64
    assert pixels[0][1] == 96
    assert pixels[1][0] == 320
    assert pixels[1][1] == 288

    # Safe validation checks
    assert extractor.to_pixel_coordinates(None, frame_shape) is None
    assert extractor.to_pixel_coordinates(normalized_list, (0, 640)) is None


def test_draw_landmarks():
    """Verify rendering executes cleanly without throwing crashes."""
    extractor = MouthLandmarkExtractor()
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    inner_points = [(64, 96), (320, 288)]
    outer_points = [(100, 150)]

    # Draw on frame
    output_frame = extractor.draw_mouth_landmarks(frame, inner_points, outer_points)
    assert output_frame.shape == (480, 640, 3)
