"""
Unit tests for the YawnDetector module (Phase 9.1).
Verifies that YawnDetector initializes properly, holds the correct states,
tracks frame counts during update, resets properly, and returns structured metrics.
"""

import pytest
import config
from detection.yawn_detector import YawnDetector, MouthState


def test_yawn_detector_initialization():
    """Verify that YawnDetector initializes with correct default properties."""
    detector = YawnDetector(fps=30.0, mar_threshold=0.65, yawn_duration_frames=20)
    
    assert detector.fps == 30.0
    assert detector.mar_threshold == 0.65
    assert detector.yawn_duration_frames == 20
    assert detector.yawn_count == 0
    assert detector.consecutive_open_frames == 0
    assert detector.is_active_yawn is False
    assert detector.frame_counter == 0

    # Verify new interface compatibility getters (Phase 11 getters validation)
    assert detector.get_yawn_count() == 0
    assert detector.get_open_frame_count() == 0
    assert detector.get_open_duration_seconds() == 0.0
    assert detector.get_open_duration() == 0.0
    assert detector.get_mouth_state() == MouthState.CLOSED


def test_yawn_detector_config_fallbacks():
    """Verify config defaults are loaded when constructor arguments are omitted."""
    detector = YawnDetector()
    
    # Fallback configs
    expected_threshold = getattr(config, "MAR_THRESHOLD", 0.60)
    expected_frames = getattr(config, "MAR_CONSECUTIVE_FRAMES", 15)
    
    assert detector.mar_threshold == expected_threshold
    assert detector.yawn_duration_frames == expected_frames


def test_yawn_detector_update_increments():
    """Verify that update safely tracks frame steps and updates open frame streaks."""
    detector = YawnDetector(fps=30.0)
    
    # Feed value above threshold -> should classify as OPEN and increment open streak
    detector.update(0.70)
    assert detector.frame_counter == 1
    assert detector.yawn_count == 0
    assert detector.consecutive_open_frames == 1
    assert detector.is_active_yawn is False

    # Feed None value -> should be ignored, leaving consecutive open streak unchanged
    detector.update(None)
    assert detector.frame_counter == 2
    assert detector.yawn_count == 0
    assert detector.consecutive_open_frames == 1


def test_yawn_detector_reset():
    """Verify state resets for both live statuses and cumulative metrics."""
    detector = YawnDetector()
    detector.consecutive_open_frames = 10
    detector.is_active_yawn = True
    detector.yawn_count = 3
    detector.frame_counter = 120

    detector.reset_yawn_status()
    assert detector.consecutive_open_frames == 0
    assert detector.is_active_yawn is False
    assert detector.yawn_count == 3  # Cumulative remains unchanged

    detector.consecutive_open_frames = 10
    detector.is_active_yawn = True
    
    detector.reset_all()
    assert detector.consecutive_open_frames == 0
    assert detector.is_active_yawn is False
    assert detector.yawn_count == 0
    assert detector.frame_counter == 0


def test_yawn_detector_metrics():
    """Verify the metrics dictionary contains the required keys and types."""
    detector = YawnDetector(fps=30.0)
    detector.consecutive_open_frames = 15
    
    metrics = detector.get_yawn_metrics()
    assert isinstance(metrics, dict)
    assert metrics["yawn_count"] == 0
    assert metrics["consecutive_open_frames"] == 15
    assert metrics["yawn_duration_seconds"] == pytest.approx(0.5, abs=1e-4)
    assert metrics["is_active_yawn"] is False
    assert metrics["valid"] is True


def test_mouth_state_classification():
    """Verify that classify_mouth_state maps MAR to MouthState correctly."""
    detector = YawnDetector(mar_threshold=0.55)

    # 1. Closed state: MAR < threshold
    assert detector.classify_mouth_state(0.50) == MouthState.CLOSED
    assert detector.classify_mouth_state(0.00) == MouthState.CLOSED

    # 2. Open state: MAR >= threshold
    assert detector.classify_mouth_state(0.55) == MouthState.OPEN
    assert detector.classify_mouth_state(0.80) == MouthState.OPEN

    # 3. Invalid inputs: None or negative values
    assert detector.classify_mouth_state(None) == MouthState.UNKNOWN
    assert detector.classify_mouth_state(-0.1) == MouthState.UNKNOWN

    # 4. Configurable threshold test
    detector2 = YawnDetector(mar_threshold=0.70)
    assert detector2.classify_mouth_state(0.65) == MouthState.CLOSED
    assert detector2.classify_mouth_state(0.70) == MouthState.OPEN

    # 5. Negative constraint verification: yawn state trackers must not change
    assert detector.yawn_count == 0
    assert detector.consecutive_open_frames == 0


def test_mouth_temporal_analysis():
    """Verify that update maintains consecutive open/closed streaks and ignores UNKNOWNs."""
    detector = YawnDetector(mar_threshold=0.50, yawn_duration_frames=5)

    # 1. Closed stream updates
    detector.update(0.40)  # CLOSED
    assert detector.get_consecutive_closed_frames() == 1
    assert detector.get_consecutive_open_frames() == 0

    detector.update(0.30)  # CLOSED
    assert detector.get_consecutive_closed_frames() == 2
    assert detector.get_consecutive_open_frames() == 0

    # 2. Switch to open stream
    detector.update(0.60)  # OPEN
    assert detector.get_consecutive_closed_frames() == 0
    assert detector.get_consecutive_open_frames() == 1

    detector.update(0.55)  # OPEN
    assert detector.get_consecutive_closed_frames() == 0
    assert detector.get_consecutive_open_frames() == 2

    # 3. Handle UNKNOWN safely (ignores and leaves streaks unchanged)
    detector.update(None)  # UNKNOWN
    assert detector.get_consecutive_closed_frames() == 0
    assert detector.get_consecutive_open_frames() == 2

    detector.update(-0.2)  # UNKNOWN
    assert detector.get_consecutive_closed_frames() == 0
    assert detector.get_consecutive_open_frames() == 2

    # 4. Switch back to closed
    detector.update(0.10)  # CLOSED
    assert detector.get_consecutive_closed_frames() == 1
    assert detector.get_consecutive_open_frames() == 0

    # 5. Temporal state change check (is_active_yawn becomes True)
    for _ in range(10):
        detector.update(0.80)  # OPEN (10 frames, threshold is 5)

    assert detector.get_consecutive_open_frames() == 10
    assert detector.get_yawn_count() == 0  # Count remains 0 until it closes
    assert detector.get_yawn_metrics()["is_active_yawn"] is True


def test_yawn_state_machine():
    """Verify Yawn Detection State Machine sequence: CLOSED -> sustained OPEN -> CLOSED."""
    detector = YawnDetector(mar_threshold=0.50, yawn_duration_frames=3)

    # Starts in baseline state
    assert detector.get_yawn_count() == 0
    assert detector.get_yawn_metrics()["is_active_yawn"] is False

    # 1. Initiate open cycle but below minimum duration threshold
    detector.update(0.60)  # OPEN (streak = 1)
    detector.update(0.60)  # OPEN (streak = 2)
    assert detector.get_yawn_count() == 0
    assert detector.get_yawn_metrics()["is_active_yawn"] is False

    # Close the mouth -> resets open streak, no yawn counted
    detector.update(0.10)  # CLOSED (streak = 0)
    assert detector.get_yawn_count() == 0

    # 2. Initiate sustained open cycle matching threshold (yawn_duration_frames = 3)
    detector.update(0.60)  # OPEN (streak = 1)
    detector.update(0.60)  # OPEN (streak = 2)
    detector.update(0.60)  # OPEN (streak = 3) -> should trigger is_active_yawn = True
    assert detector.get_yawn_count() == 0
    assert detector.get_yawn_metrics()["is_active_yawn"] is True

    # Keep mouth open -> yawn count still 0, active yawn remains True
    detector.update(0.70)  # OPEN (streak = 4)
    detector.update(0.80)  # OPEN (streak = 5)
    assert detector.get_yawn_count() == 0
    assert detector.get_yawn_metrics()["is_active_yawn"] is True

    # Close mouth -> transitions back to CLOSED, increments yawn_count, clears active flag
    detector.update(0.20)  # CLOSED
    assert detector.get_yawn_count() == 1
    assert detector.get_yawn_metrics()["is_active_yawn"] is False

    # Subsequent closed frames do not increment count (prevents duplicate counting)
    detector.update(0.10)
    detector.update(0.10)
    assert detector.get_yawn_count() == 1
    assert detector.get_yawn_metrics()["is_active_yawn"] is False
