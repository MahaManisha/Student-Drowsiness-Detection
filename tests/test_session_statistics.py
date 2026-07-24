"""
Unit tests for the SessionStatisticsTracker module (Phase 12.4).
Verifies that the tracker calculates correct averages, tracks maximums, logs event totals,
accumulates state times, and successfully saves statistical reports as JSON.
"""

import json
import time
from pathlib import Path
import pytest
from analytics.session_statistics import SessionStatisticsTracker


def test_statistics_tracker_init() -> None:
    """Verify statistics tracker initializes to correct default states."""
    tracker = SessionStatisticsTracker()
    assert tracker.highest_score == 0.0
    assert tracker.longest_eye_closure == 0.0
    assert tracker.blink_count == 0
    assert tracker.yawn_count == 0
    assert tracker.num_alerts == 0
    assert all(v == 0.0 for v in tracker.state_times.values())


def test_statistics_averages_and_extremes() -> None:
    """Verify calculation of averages (EAR, MAR) and extremes (score, eye closure)."""
    tracker = SessionStatisticsTracker()

    # Frame 1: EAR=0.3, MAR=0.4, Score=10, Eye closure=0.0
    tracker.update(
        current_state="ALERT",
        score=10.0,
        avg_ear=0.30,
        mar=0.40,
        blink_count=0,
        yawn_count=0,
        closed_duration=0.0
    )

    # Frame 2: EAR=0.2, MAR=0.5, Score=45, Eye closure=0.5
    tracker.update(
        current_state="SLIGHTLY_DROWSY",
        score=45.0,
        avg_ear=0.20,
        mar=0.50,
        blink_count=1,
        yawn_count=0,
        closed_duration=0.5
    )

    stats = tracker.get_stats()
    assert stats["average_ear"] == pytest.approx(0.25)
    assert stats["average_mar"] == pytest.approx(0.45)
    assert stats["highest_score"] == 45.0
    assert stats["longest_eye_closure"] == 0.5
    assert stats["blink_count"] == 1
    assert stats["yawn_count"] == 0


def test_statistics_state_times_and_alerts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify state time accumulation and warning alert triggers across mock transitions."""
    tracker = SessionStatisticsTracker()
    
    current_mock_time = 100.0
    monkeypatch.setattr(time, "time", lambda: current_mock_time)
    
    # Restart start_time to mock baseline
    tracker.start_time = current_mock_time
    tracker.last_state_change_time = current_mock_time

    # Update Frame 1: ALERT state at t=100.0
    tracker.update("ALERT", 10.0, 0.3, 0.3, 0, 0, 0.0)

    # Transition to DROWSY at t=105.0 (ALERT should accumulate 5.0 seconds, alert is triggered)
    current_mock_time = 105.0
    tracker.update("DROWSY", 65.0, 0.15, 0.4, 0, 0, 0.0)
    assert tracker.num_alerts == 1

    # Transition to HIGHLY_DROWSY at t=108.0 (DROWSY should accumulate 3.0 seconds, alert remains active)
    current_mock_time = 108.0
    tracker.update("HIGHLY_DROWSY", 85.0, 0.10, 0.7, 0, 1, 3.2)
    assert tracker.num_alerts == 1  # Still inside the alert sequence

    # Transition back to ALERT at t=112.0 (HIGHLY_DROWSY should accumulate 4.0 seconds)
    current_mock_time = 112.0
    tracker.update("ALERT", 10.0, 0.3, 0.3, 1, 1, 0.0)
    assert not tracker.in_alert_period

    # We are in ALERT state up to t=115.0
    current_mock_time = 115.0

    stats = tracker.get_stats()
    
    # ALERT = 5s (first period) + 3s (second active period up to t=115.0) = 8s
    assert stats["time_spent_in_states"]["ALERT"] == pytest.approx(8.0)
    assert stats["time_spent_in_states"]["DROWSY"] == pytest.approx(3.0)
    assert stats["time_spent_in_states"]["HIGHLY_DROWSY"] == pytest.approx(4.0)
    assert stats["number_of_alerts"] == 1
    assert stats["total_session_time"] == pytest.approx(15.0)  # t=115.0 - t=100.0


def test_statistics_save_file(tmp_path: Path) -> None:
    """Verify that session statistics are successfully exported to a JSON file."""
    tracker = SessionStatisticsTracker()
    out_file = tmp_path / "stats.json"

    # Seed mock data
    tracker.update("ALERT", 5.0, 0.28, 0.35, 12, 1, 0.4)
    tracker.save_stats(str(out_file))

    assert out_file.exists()
    with open(out_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["blink_count"] == 12
    assert data["yawn_count"] == 1
    assert data["longest_eye_closure"] == 0.4
