"""
Unit test suite for Phase 6.1: Temporal Eye Analyzer.

Validates that:
1. Initialization sets correct initial empty states and parameters.
2. Frame updates correctly record stats, timestamps, and indexes.
3. Consecutive closed/open streak counters behave correctly.
4. UNKNOWN states reset streaks correctly.
5. Max window size parameter limits history buffer (sliding window).
6. Rolling average EAR, EAR variance, and closure percentage are computed correctly.
7. Reset/clear logic wipes history and streaks.
8. Input validation safely handles unexpected types and out-of-bounds metrics.
"""

import pytest
import time
from detection.eye_state_classifier import EyeState
from detection.temporal_eye_analyzer import TemporalEyeAnalyzer, EyeTemporalRecord


def test_analyzer_initialization():
    """Verify default and customized initialization values."""
    # Test default window size
    analyzer = TemporalEyeAnalyzer()
    assert analyzer.max_window_size == 100
    assert len(analyzer.get_history()) == 0
    assert analyzer.get_consecutive_closed_frames() == 0
    assert analyzer.get_consecutive_open_frames() == 0
    assert analyzer.total_frames_processed == 0

    # Test custom window size
    analyzer_custom = TemporalEyeAnalyzer(max_window_size=15)
    assert analyzer_custom.max_window_size == 15

    # Test invalid window size fallback
    analyzer_invalid = TemporalEyeAnalyzer(max_window_size=-5)
    assert analyzer_invalid.max_window_size == 100


def test_analyzer_update_streaks():
    """Verify consecutive streaks increment and reset correctly."""
    analyzer = TemporalEyeAnalyzer(max_window_size=10)

    # 1. Update with OPEN state
    analyzer.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, 0.3)
    assert analyzer.get_consecutive_open_frames() == 1
    assert analyzer.get_consecutive_closed_frames() == 0
    assert analyzer.total_frames_processed == 1

    # 2. Update with another OPEN state
    analyzer.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, 0.32)
    assert analyzer.get_consecutive_open_frames() == 2
    assert analyzer.get_consecutive_closed_frames() == 0

    # 3. Transition to CLOSED state
    analyzer.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.15)
    assert analyzer.get_consecutive_open_frames() == 0
    assert analyzer.get_consecutive_closed_frames() == 1

    # 4. Another CLOSED state
    analyzer.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.12)
    assert analyzer.get_consecutive_open_frames() == 0
    assert analyzer.get_consecutive_closed_frames() == 2


def test_analyzer_unknown_ignores_streaks():
    """Verify that UNKNOWN states do not affect streak counters (they are ignored safely)."""
    analyzer = TemporalEyeAnalyzer(max_window_size=10)

    # Accumulate closed frames
    analyzer.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.12)
    analyzer.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.11)
    assert analyzer.get_consecutive_closed_frames() == 2
    assert analyzer.get_consecutive_open_frames() == 0

    # Update with UNKNOWN -> Counters should remain unchanged
    analyzer.update(EyeState.UNKNOWN, EyeState.UNKNOWN, EyeState.UNKNOWN, None)
    assert analyzer.get_consecutive_closed_frames() == 2
    assert analyzer.get_consecutive_open_frames() == 0

    # Update with CLOSED again -> Should resume accumulating closed frames
    analyzer.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.10)
    assert analyzer.get_consecutive_closed_frames() == 3
    assert analyzer.get_consecutive_open_frames() == 0

    # Update with UNKNOWN -> Counters should remain unchanged
    analyzer.update(EyeState.UNKNOWN, EyeState.UNKNOWN, EyeState.UNKNOWN, None)
    assert analyzer.get_consecutive_closed_frames() == 3
    assert analyzer.get_consecutive_open_frames() == 0

    # Update with OPEN -> State change resets closed streak and increments open streak
    analyzer.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, 0.35)
    assert analyzer.get_consecutive_closed_frames() == 0
    assert analyzer.get_consecutive_open_frames() == 1

    # Update with UNKNOWN -> Counters should remain unchanged
    analyzer.update(EyeState.UNKNOWN, EyeState.UNKNOWN, EyeState.UNKNOWN, None)
    assert analyzer.get_consecutive_closed_frames() == 0
    assert analyzer.get_consecutive_open_frames() == 1

    # Update with OPEN again -> Should resume accumulating open frames
    analyzer.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, 0.36)
    assert analyzer.get_consecutive_closed_frames() == 0
    assert analyzer.get_consecutive_open_frames() == 2


def test_analyzer_sliding_window_limit():
    """Verify that buffer does not grow beyond max_window_size."""
    max_size = 3
    analyzer = TemporalEyeAnalyzer(max_window_size=max_size)

    analyzer.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, 0.3, frame_index=10)
    analyzer.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, 0.31, frame_index=11)
    analyzer.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.12, frame_index=12)

    history = analyzer.get_history()
    assert len(history) == 3
    assert history[0].frame_index == 10
    assert history[2].frame_index == 12

    # Add a 4th frame, oldest (frame_index=10) should be dropped
    analyzer.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.1, frame_index=13)
    history_new = analyzer.get_history()
    assert len(history_new) == 3
    assert history_new[0].frame_index == 11
    assert history_new[2].frame_index == 13


def test_analyzer_rolling_stats():
    """Verify rolling average EAR, variance, and closure percentage metrics."""
    analyzer = TemporalEyeAnalyzer(max_window_size=5)

    # Empty stats cases
    assert analyzer.get_rolling_average_ear() == 0.0
    assert analyzer.get_rolling_ear_variance() == 0.0
    assert analyzer.get_closure_percentage() == 0.0

    # Populate some values: [0.30, 0.28, None, 0.12]
    # Corresponding states: [OPEN, OPEN, UNKNOWN, CLOSED]
    analyzer.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, 0.30)
    analyzer.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, 0.28)
    analyzer.update(EyeState.UNKNOWN, EyeState.UNKNOWN, EyeState.UNKNOWN, None)
    analyzer.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.12)

    # 1. Rolling Average EAR
    # Valid values: 0.30, 0.28, 0.12 -> Mean: (0.30 + 0.28 + 0.12) / 3 = 0.70 / 3 = 0.2333...
    avg_ear = analyzer.get_rolling_average_ear()
    assert pytest.approx(avg_ear, rel=1e-4) == 0.23333

    # Rolling Average EAR with smaller window (last 2 frames: None, 0.12 -> Valid is only 0.12)
    avg_ear_sub = analyzer.get_rolling_average_ear(window_len=2)
    assert avg_ear_sub == 0.12

    # 2. Rolling EAR Variance
    # Valid values: 0.30, 0.28, 0.12. Mean: 0.23333
    # Diff sq: (0.30 - 0.23333)^2 + (0.28 - 0.23333)^2 + (0.12 - 0.23333)^2
    # = (0.06666)^2 + (0.04666)^2 + (-0.11333)^2 = 0.004444 + 0.002178 + 0.012844 = 0.019466
    # Population Variance = 0.019466 / 3 = 0.0064888...
    variance = analyzer.get_rolling_ear_variance()
    assert pytest.approx(variance, rel=1e-4) == 0.0064888

    # Rolling EAR Variance with window = 2 (only 1 valid value, should fallback to 0.0)
    variance_sub = analyzer.get_rolling_ear_variance(window_len=2)
    assert variance_sub == 0.0

    # 3. Closure Percentage
    # Known states in history: OPEN, OPEN, CLOSED (total 3). UNKNOWN is ignored.
    # Closed count: 1 (from frame 4).
    # Ratio: 1 / 3 = 0.3333...
    closure_rate = analyzer.get_closure_percentage()
    assert pytest.approx(closure_rate, rel=1e-4) == 0.33333

    # Closure percentage for last 2 frames (UNKNOWN, CLOSED -> known count is 1: CLOSED -> 1.0)
    closure_rate_sub = analyzer.get_closure_percentage(window_len=2)
    assert closure_rate_sub == 1.0


def test_analyzer_clear():
    """Verify clear_history wipes all internal history queues, streaks, and blink counts."""
    analyzer = TemporalEyeAnalyzer(max_window_size=10)
    analyzer.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.11)
    analyzer.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.10)
    analyzer.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, 0.35)
    
    assert len(analyzer.get_history()) == 3
    assert analyzer.get_consecutive_closed_frames() == 0
    assert analyzer.get_consecutive_open_frames() == 1
    assert analyzer.get_blink_count() == 1

    analyzer.clear_history()
    assert len(analyzer.get_history()) == 0
    assert analyzer.get_consecutive_closed_frames() == 0
    assert analyzer.get_consecutive_open_frames() == 0
    assert analyzer.get_blink_count() == 0


def test_analyzer_input_validation():
    """Verify analyzer safely handles unexpected input types and ranges."""
    analyzer = TemporalEyeAnalyzer()

    # Pass invalid state types
    record = analyzer.update("BAD_STATE", "BAD_STATE", "BAD_STATE", "not-a-float")
    
    assert record.right_state == EyeState.UNKNOWN
    assert record.left_state == EyeState.UNKNOWN
    assert record.overall_state == EyeState.UNKNOWN
    assert record.avg_ear is None

    # Pass a valid float-string for EAR
    record_valid_str = analyzer.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, "0.33")
    assert record_valid_str.avg_ear == 0.33


def test_analyzer_blink_detection_standard():
    """Verify a standard blink sequence (OPEN -> CLOSED -> OPEN) triggers exactly one increment."""
    analyzer = TemporalEyeAnalyzer(min_blink_duration=1, max_blink_duration=5)

    # Starts at 0
    assert analyzer.get_blink_count() == 0

    # Frame 1: OPEN
    analyzer.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, 0.34)
    assert analyzer.get_blink_count() == 0

    # Frame 2: CLOSED
    analyzer.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.12)
    assert analyzer.get_blink_count() == 0

    # Frame 3: CLOSED
    analyzer.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.13)
    assert analyzer.get_blink_count() == 0

    # Frame 4: OPEN (Blink completes)
    analyzer.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, 0.35)
    assert analyzer.get_blink_count() == 1


def test_analyzer_blink_detection_boundaries():
    """Verify that blink duration boundaries (min/max thresholds) are strictly respected."""
    # Setup analyzer with min=2 and max=4
    analyzer = TemporalEyeAnalyzer(min_blink_duration=2, max_blink_duration=4)

    # 1. Test blink of length 1 (too short)
    analyzer.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, 0.35)
    analyzer.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.12)  # duration = 1
    analyzer.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, 0.35)        # opens
    assert analyzer.get_blink_count() == 0

    # 2. Test blink of length 2 (valid - min boundary)
    analyzer.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.12)
    analyzer.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.12)  # duration = 2
    analyzer.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, 0.35)        # opens
    assert analyzer.get_blink_count() == 1

    # 3. Test blink of length 4 (valid - max boundary)
    analyzer.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.12)
    analyzer.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.12)
    analyzer.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.12)
    analyzer.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.12)  # duration = 4
    analyzer.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, 0.35)        # opens
    assert analyzer.get_blink_count() == 2

    # 4. Test blink of length 5 (too long)
    for _ in range(5):
        analyzer.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.12)
    analyzer.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, 0.35)        # opens
    assert analyzer.get_blink_count() == 2  # remains 2


def test_analyzer_blink_detection_duplication_prevention():
    """Verify that multiple consecutive OPEN frames do not duplicate blink count updates."""
    analyzer = TemporalEyeAnalyzer()

    # Steady open frames
    for _ in range(10):
        analyzer.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, 0.35)
    assert analyzer.get_blink_count() == 0

    # Perform a blink
    analyzer.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.10)
    analyzer.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, 0.35)
    assert analyzer.get_blink_count() == 1

    # More open frames
    for _ in range(5):
        analyzer.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, 0.35)
    assert analyzer.get_blink_count() == 1


def test_analyzer_blink_detection_unknown_handling():
    """Verify that UNKNOWN states within a blink are ignored, preserving the blink sequence."""
    analyzer = TemporalEyeAnalyzer(min_blink_duration=1, max_blink_duration=5)

    analyzer.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, 0.35)
    analyzer.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.12)  # 1 closed
    analyzer.update(EyeState.UNKNOWN, EyeState.UNKNOWN, EyeState.UNKNOWN, None)  # ignored
    analyzer.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.11)  # 2 closed
    analyzer.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, 0.35)  # opens
    
    # Blink should be successfully detected with closed duration of 2
    assert analyzer.get_blink_count() == 1


def test_analyzer_blink_detection_manual_set():
    """Verify manual getters/setters for the blink counter work as expected."""
    analyzer = TemporalEyeAnalyzer()
    assert analyzer.get_blink_count() == 0

    analyzer.set_blink_count(42)
    assert analyzer.get_blink_count() == 42

    # Attempt negative value override (should fallback to 0)
    analyzer.set_blink_count(-10)
    assert analyzer.get_blink_count() == 0


def test_analyzer_eye_closure_duration():
    """Verify continuous eye closure tracking in frames and seconds."""
    # Test with default FPS (30.0)
    analyzer = TemporalEyeAnalyzer(fps=30.0)
    
    # Intially 0
    assert analyzer.get_closed_frame_count() == 0
    assert analyzer.get_closed_duration_seconds() == 0.0

    # 1 closed frame -> 1 frame, 1/30 seconds
    analyzer.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.1)
    assert analyzer.get_closed_frame_count() == 1
    assert pytest.approx(analyzer.get_closed_duration_seconds(), rel=1e-4) == 1 / 30.0

    # 15 closed frames -> 15 frames, 15/30 = 0.5 seconds
    for _ in range(14):
        analyzer.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.1)
    assert analyzer.get_closed_frame_count() == 15
    assert analyzer.get_closed_duration_seconds() == 0.5

    # UNKNOWN frames should be ignored (preserves duration)
    analyzer.update(EyeState.UNKNOWN, EyeState.UNKNOWN, EyeState.UNKNOWN, None)
    assert analyzer.get_closed_frame_count() == 15
    assert analyzer.get_closed_duration_seconds() == 0.5

    # Reopening eye -> resets duration and count
    analyzer.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, 0.35)
    assert analyzer.get_closed_frame_count() == 0
    assert analyzer.get_closed_duration_seconds() == 0.0


def test_analyzer_fps_validation():
    """Verify FPS configuration checks and dynamic adjustments."""
    # Invalid constructor FPS fallback
    analyzer_invalid = TemporalEyeAnalyzer(fps=-10.0)
    assert analyzer_invalid.fps == 30.0

    # Dynamic setter test
    analyzer = TemporalEyeAnalyzer(fps=20.0)
    assert analyzer.fps == 20.0

    analyzer.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.1)
    analyzer.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.1)
    assert analyzer.get_closed_frame_count() == 2
    assert analyzer.get_closed_duration_seconds() == 0.1  # 2 / 20.0 = 0.1s

    # Dynamic adjustment to 10 FPS
    analyzer.set_fps(10.0)
    assert analyzer.fps == 10.0
    assert analyzer.get_closed_duration_seconds() == 0.2  # 2 / 10.0 = 0.2s

    # Attempt setting invalid FPS (should remain unchanged)
    analyzer.set_fps(0.0)
    assert analyzer.fps == 10.0
    analyzer.set_fps(-5.0)
    assert analyzer.fps == 10.0


