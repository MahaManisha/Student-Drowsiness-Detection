"""
Unit tests for the StudentDrowsinessDecisionEngine module (Phase 11.1).
Verifies that StudentDrowsinessDecisionEngine initializes properly, holds the correct states,
tracks frame counts during updates, resets properly, and returns structured metrics.
"""

import pytest
import config
from detection.drowsiness_decision_engine import StudentDrowsinessDecisionEngine, DrowsinessState


def test_drowsiness_decision_engine_initialization():
    """Verify that StudentDrowsinessDecisionEngine initializes with correct properties and default states."""
    engine = StudentDrowsinessDecisionEngine()
    
    assert engine.drowsiness_score == 0.0
    assert engine.is_drowsy is False
    assert engine.drowsiness_state == DrowsinessState.ALERT
    assert engine.frame_counter == 0


def test_drowsiness_decision_engine_state_model():
    """Verify state model enum contents and config threshold values."""
    assert DrowsinessState.ALERT.value == "ALERT"
    assert DrowsinessState.SLIGHTLY_DROWSY.value == "SLIGHTLY_DROWSY"
    assert DrowsinessState.DROWSY.value == "DROWSY"
    assert DrowsinessState.HIGHLY_DROWSY.value == "HIGHLY_DROWSY"

    engine = StudentDrowsinessDecisionEngine()
    assert engine.max_blink_duration == config.DECISION_MAX_BLINK_DURATION
    assert engine.max_eye_closure_duration == config.DECISION_MAX_EYE_CLOSURE_DURATION
    assert engine.yawn_frequency_limit == config.DECISION_YAWN_FREQUENCY_LIMIT
    assert engine.head_pitch_limit == config.DECISION_HEAD_PITCH_LIMIT


def test_drowsiness_decision_engine_update_signature():
    """Verify that update method tracks frame counts and returns structured status."""
    engine = StudentDrowsinessDecisionEngine()
    
    dummy_eye_metrics = {
        "blink_count": 5,
        "consecutive_closed_frames": 2,
        "closed_duration_seconds": 0.06
    }
    dummy_yawn_metrics = {
        "yawn_count": 0,
        "consecutive_open_frames": 1,
        "yawn_duration_seconds": 0.03
    }
    dummy_pose_metrics = {
        "yaw": 0.5,
        "pitch": -2.0,
        "roll": 0.1,
        "valid": True
    }
    
    result = engine.update(dummy_eye_metrics, dummy_yawn_metrics, dummy_pose_metrics)
    
    assert isinstance(result, dict)
    assert result["drowsiness_score"] == 1.0
    assert result["is_drowsy"] is False
    assert result["drowsiness_state"] == "ALERT"
    assert result["valid"] is True
    assert engine.frame_counter == 1


def test_drowsiness_decision_engine_reset():
    """Verify states and frame counters are reset successfully."""
    engine = StudentDrowsinessDecisionEngine()
    engine.drowsiness_score = 0.85
    engine.is_drowsy = True
    engine.drowsiness_state = DrowsinessState.DROWSY
    engine.frame_counter = 120
    
    engine.reset()
    assert engine.drowsiness_score == 0.0
    assert engine.is_drowsy is False
    assert engine.drowsiness_state == DrowsinessState.ALERT
    assert engine.frame_counter == 0


def test_drowsiness_decision_engine_metrics():
    """Verify the metrics dictionary contains the required keys and types."""
    engine = StudentDrowsinessDecisionEngine()
    
    metrics = engine.get_decision_metrics()
    assert isinstance(metrics, dict)
    assert "drowsiness_score" in metrics
    assert "is_drowsy" in metrics
    assert "drowsiness_state" in metrics
    assert "valid" in metrics
    assert metrics["drowsiness_score"] == 0.0
    assert metrics["is_drowsy"] is False
    assert metrics["drowsiness_state"] == "ALERT"
    assert metrics["valid"] is True


def test_drowsiness_decision_engine_rules_cooccurrence():
    """Verify rule engine correctly evaluates signal combinations and sets confidence levels."""
    engine = StudentDrowsinessDecisionEngine()
    
    # Base baseline metrics (no triggers)
    eye_base = {"closed_duration_seconds": 0.1, "blink_count": 2}
    yawn_base = {"yawn_count": 0}
    pose_base = {"pitch": 2.0, "valid": True}
    
    # Scenario 0: No indicators triggered
    dec = engine.evaluate_rules(eye_base, yawn_base, pose_base)
    assert dec.abnormal_eye_closure is False
    assert dec.abnormal_yawning is False
    assert dec.abnormal_head_posture is False
    assert dec.signal_cooccurrence_count == 0
    assert dec.confidence_score == 0.0
    assert "normal baselines" in dec.reason

    # Scenario 1a: Isolated abnormal eye closure
    eye_trigger = {"closed_duration_seconds": 4.5, "blink_count": 2}
    dec = engine.evaluate_rules(eye_trigger, yawn_base, pose_base)
    assert dec.abnormal_eye_closure is True
    assert dec.abnormal_yawning is False
    assert dec.signal_cooccurrence_count == 1
    assert dec.confidence_score == 0.45
    assert "Isolated prolonged eye closure" in dec.reason

    # Scenario 1b: Isolated abnormal yawning
    yawn_trigger = {"yawn_count": 3}
    dec = engine.evaluate_rules(eye_base, yawn_trigger, pose_base)
    assert dec.abnormal_eye_closure is False
    assert dec.abnormal_yawning is True
    assert dec.signal_cooccurrence_count == 1
    assert dec.confidence_score == 0.30
    assert "Isolated yawning" in dec.reason

    # Scenario 1c: Isolated abnormal head nodding (mock consecutive droop frames to simulate sustained drooping)
    engine.consecutive_droop_frames = 100
    pose_trigger = {"pitch": 18.5, "valid": True}
    dec = engine.evaluate_rules(eye_base, yawn_base, pose_trigger)
    assert dec.abnormal_head_posture is True
    assert dec.signal_cooccurrence_count == 1
    assert dec.confidence_score == 0.20
    assert "Sustained downward head posture" in dec.reason
    engine.consecutive_droop_frames = 0 # reset

    # Scenario 2: Two indicators (Eye closure + yawning)
    dec = engine.evaluate_rules(eye_trigger, yawn_trigger, pose_base)
    assert dec.abnormal_eye_closure is True
    assert dec.abnormal_yawning is True
    assert dec.abnormal_head_posture is False
    assert dec.signal_cooccurrence_count == 2
    assert dec.confidence_score == 0.80
    assert "Co-occurrence" in dec.reason

    # Scenario 3: All three indicators triggered
    dec = engine.evaluate_rules(eye_trigger, yawn_trigger, pose_trigger)
    assert dec.abnormal_eye_closure is True
    assert dec.abnormal_yawning is True
    assert dec.abnormal_head_posture is True
    assert dec.signal_cooccurrence_count == 3
    assert dec.confidence_score == 0.95
    assert "Simultaneous prolonged eye closure" in dec.reason


def test_drowsiness_decision_engine_scoring_system():
    """Verify that scoring system computes correct scores and maps to drowsiness states."""
    engine = StudentDrowsinessDecisionEngine()
    
    # Base parameters
    eye_base = {"closed_duration_seconds": 0.0, "blink_count": 0}
    yawn_base = {"yawn_count": 0}
    pose_base = {"pitch": 0.0, "valid": True}
    
    # Scenario A: All signals normal (ALERT state, score = 0)
    res = engine.calculate_drowsiness(eye_base, yawn_base, pose_base)
    assert res.score == 0.0
    assert res.state == DrowsinessState.ALERT
    assert "normal limits" in res.explanation

    # Scenario B: Isolated prolonged eye closure (65.0 pts -> DROWSY)
    eye_closure = {"closed_duration_seconds": 3.0, "blink_count": 0}
    res = engine.calculate_drowsiness(eye_closure, yawn_base, pose_base)
    assert res.score == 65.0
    assert res.state == DrowsinessState.DROWSY
    assert "Prolonged eye closure" in res.explanation

    # Scenario C: Slow blink + yawning (eye points = 25 + blink points = 15 + yawn points = 20 -> 60.0 pts -> DROWSY)
    eye_slow = {"closed_duration_seconds": 1.5, "blink_count": 0}
    yawn_trigger = {"yawn_count": 2}
    res = engine.calculate_drowsiness(eye_slow, yawn_trigger, pose_base)
    assert res.score == 60.0
    assert res.state == DrowsinessState.DROWSY
    assert "Slow blink behavior" in res.explanation
    assert "Yawning activity" in res.explanation

    # Scenario D: All components co-occurring (eye points = 25 + blink points = 15 + yawn points = 20 + pose = 15 -> 75.0 pts -> DROWSY)
    pose_nod = {"pitch": 15.0, "valid": True}
    res = engine.calculate_drowsiness(eye_slow, yawn_trigger, pose_nod)
    assert res.score == 75.0
    assert res.state == DrowsinessState.DROWSY
    assert "Downward head posture deflection" in res.explanation

    # Scenario E: Verify update method updates score state variables
    engine.update(eye_slow, yawn_trigger, pose_nod)
    assert engine.drowsiness_score == 75.0
    assert engine.is_drowsy is True
    assert engine.drowsiness_state == DrowsinessState.DROWSY
    
    metrics = engine.get_decision_metrics()
    assert metrics["drowsiness_score"] == 75.0
    assert metrics["is_drowsy"] is True
    assert metrics["drowsiness_state"] == "DROWSY"
    assert isinstance(metrics["drowsiness_result"], dict)
    assert metrics["drowsiness_result"]["score"] == 75.0
