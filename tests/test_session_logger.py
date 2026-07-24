"""
Unit tests for the SessionLogger module (Phase 12.3).
Verifies that the session logger creates structured JSON Lines records, calculates
accurate state durations, and registers alert trigger/end lifecycles correctly.
"""

import json
import time
from pathlib import Path
import pytest
import sys
import os
# Safe import logic to bypass standard library naming collision
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logging")))
try:
    from session_logger import SessionLogger
finally:
    if sys.path[0] == os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logging")):
        sys.path.pop(0)


def test_session_logger_init(tmp_path: Path) -> None:
    """Verify logger initializes and creates parent directories."""
    log_file = tmp_path / "subfolder" / "session_log.json"
    logger_instance = SessionLogger(log_path=str(log_file))
    
    assert logger_instance.log_path == log_file
    assert log_file.parent.exists()
    assert not log_file.exists()  # Empty log file not written until first event


def test_session_logger_log_event(tmp_path: Path) -> None:
    """Verify log_event appends valid JSON Lines."""
    log_file = tmp_path / "session_log.json"
    logger_instance = SessionLogger(log_path=str(log_file))

    logger_instance.log_event(
        event_type="test_event",
        state="ALERT",
        score=10.0,
        confidence=80.0,
        duration=2.5,
        extra_info={"message": "extra payload data"}
    )

    assert log_file.exists()
    
    # Read and parse JSON Line
    lines = log_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1
    
    data = json.loads(lines[0])
    assert data["event_type"] == "test_event"
    assert data["state"] == "ALERT"
    assert data["score"] == 10.0
    assert data["confidence"] == 80.0
    assert data["duration"] == 2.5
    assert data["message"] == "extra payload data"
    assert "timestamp" in data


def test_session_logger_transitions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify state transitions and alert durations calculation on simulated frames."""
    log_file = tmp_path / "session_log.json"
    
    # Mock system clock for controlled duration tests
    current_mock_time = 100.0
    monkeypatch.setattr(time, "time", lambda: current_mock_time)

    logger_instance = SessionLogger(log_path=str(log_file))

    # Frame 1: Starts in ALERT state
    logger_instance.update("ALERT", score=5.0, confidence=100.0)
    assert not log_file.exists()  # Initialization in baseline alert doesn't log anything

    # Frame 2: Transition to SLIGHTLY_DROWSY at t=105.0 (ALERT lasted 5.0 seconds)
    current_mock_time = 105.0
    logger_instance.update("SLIGHTLY_DROWSY", score=35.0, confidence=75.0)

    assert log_file.exists()
    lines = log_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2  # student_became_slightly_drowsy and alert_triggered

    # Check student_became_slightly_drowsy
    e1 = json.loads(lines[0])
    assert e1["event_type"] == "student_became_slightly_drowsy"
    assert e1["state"] == "SLIGHTLY_DROWSY"
    assert e1["duration"] == 5.0  # Previous ALERT state duration
    assert e1["score"] == 35.0

    # Check alert_triggered
    e2 = json.loads(lines[1])
    assert e2["event_type"] == "alert_triggered"
    assert e2["state"] == "SLIGHTLY_DROWSY"
    assert e2["duration"] == 0.0

    # Frame 3: Transition to DROWSY at t=108.0 (SLIGHTLY_DROWSY lasted 3.0 seconds)
    current_mock_time = 108.0
    logger_instance.update("DROWSY", score=65.0, confidence=85.0)
    
    lines = log_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 4  # + student_became_drowsy and alert_triggered (escalated)

    e3 = json.loads(lines[2])
    assert e3["event_type"] == "student_became_drowsy"
    assert e3["state"] == "DROWSY"
    assert e3["duration"] == 3.0  # SLIGHTLY_DROWSY state duration

    e4 = json.loads(lines[3])
    assert e4["event_type"] == "alert_triggered"
    assert e4["state"] == "DROWSY"
    assert e4["message"] == "Alert state modified/escalated"

    # Frame 4: Transition back to ALERT at t=112.0 (DROWSY lasted 4.0 seconds, total alert warning was 7.0 seconds)
    current_mock_time = 112.0
    logger_instance.update("ALERT", score=5.0, confidence=100.0)

    lines = log_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 6  # + student_became_alert and alert_ended

    # Check student_became_alert
    e5 = json.loads(lines[4])
    assert e5["event_type"] == "student_became_alert"
    assert e5["state"] == "ALERT"
    assert e5["duration"] == 4.0  # DROWSY state duration

    # Check alert_ended
    e6 = json.loads(lines[5])
    assert e6["event_type"] == "alert_ended"
    assert e6["state"] == "ALERT"
    assert e6["duration"] == 7.0  # Total warning duration (t=112.0 - t=105.0)
