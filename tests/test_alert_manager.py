"""
Unit tests for the AlertManager module (Phase 12.1).
Verifies alert channel registration, routing on state transition,
cooldown suppression rules, HUD warning levels, and audio alarm thread triggering.
"""

import sys
import os
import time
import pytest
from unittest.mock import MagicMock

import config
from alerts.alert_manager import AlertManager, AlertChannel, HUDAlertChannel, AudioAlertChannel
from detection import DrowsinessResult, DrowsinessState


class MockAlertChannel(AlertChannel):
    """Simple mock channel to record triggered notifications."""

    def __init__(self) -> None:
        self.triggered_results: list[DrowsinessResult] = []

    def trigger(self, result: DrowsinessResult) -> None:
        self.triggered_results.append(result)


def test_alert_manager_registration() -> None:
    """Verify that only valid AlertChannel instances can be registered."""
    manager = AlertManager()
    channel = MockAlertChannel()
    
    manager.register_channel(channel)
    assert channel in manager.channels

    with pytest.raises(TypeError):
        manager.register_channel("invalid_channel")  # type: ignore


def test_alert_manager_routing_on_state_transition() -> None:
    """Verify that alert routing triggers immediately when transitioning to a new state."""
    manager = AlertManager()
    channel = MockAlertChannel()
    manager.register_channel(channel)

    # 1. Start in ALERT state: does not trigger any alert
    res_alert = DrowsinessResult(score=10.0, state=DrowsinessState.ALERT, explanation="Normal baseline")
    manager.process_result(res_alert)
    assert len(channel.triggered_results) == 0

    # 2. Transition to SLIGHTLY_DROWSY: triggers immediately
    res_slightly = DrowsinessResult(score=35.0, state=DrowsinessState.SLIGHTLY_DROWSY, explanation="Slight drowsiness")
    manager.process_result(res_slightly)
    assert len(channel.triggered_results) == 1
    assert channel.triggered_results[-1].state == DrowsinessState.SLIGHTLY_DROWSY

    # 3. Transition to DROWSY: triggers immediately
    res_drowsy = DrowsinessResult(score=65.0, state=DrowsinessState.DROWSY, explanation="Drowsy state")
    manager.process_result(res_drowsy)
    assert len(channel.triggered_results) == 2
    assert channel.triggered_results[-1].state == DrowsinessState.DROWSY

    # 4. Transition back to ALERT: triggers once to clear indicators
    manager.process_result(res_alert)
    assert len(channel.triggered_results) == 3
    assert channel.triggered_results[-1].state == DrowsinessState.ALERT


def test_alert_manager_cooldown_suppression(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that repeated results for the same state are suppressed within the cooldown period."""
    current_time = 100.0
    monkeypatch.setattr(time, "time", lambda: current_time)

    manager = AlertManager()
    manager.cooldown_period = 5.0
    channel = MockAlertChannel()
    manager.register_channel(channel)

    # First trigger: DROWSY state at t=100.0
    res_drowsy_1 = DrowsinessResult(score=65.0, state=DrowsinessState.DROWSY, explanation="Drowsy frame 1")
    manager.process_result(res_drowsy_1)
    assert len(channel.triggered_results) == 1

    # Second trigger: same state at t=100.0 (should be suppressed)
    res_drowsy_2 = DrowsinessResult(score=67.0, state=DrowsinessState.DROWSY, explanation="Drowsy frame 2")
    manager.process_result(res_drowsy_2)
    assert len(channel.triggered_results) == 1

    # Third trigger: same state at t=103.0 (still suppressed, within 5s cooldown)
    current_time = 103.0
    manager.process_result(res_drowsy_2)
    assert len(channel.triggered_results) == 1

    # Fourth trigger: same state at t=105.0 (cooldown expired, should trigger)
    current_time = 105.0
    manager.process_result(res_drowsy_2)
    assert len(channel.triggered_results) == 2
    assert channel.triggered_results[-1].explanation == "Drowsy frame 2"


def test_hud_alert_channel_behavior() -> None:
    """Verify HUDAlertChannel severity classification and messages."""
    hud = HUDAlertChannel()

    # ALERT: clears warning
    hud.trigger(DrowsinessResult(score=10.0, state=DrowsinessState.ALERT, explanation="Ok"))
    assert hud.current_message is None
    assert hud.current_severity is None

    # SLIGHTLY_DROWSY: subtle warning
    hud.trigger(DrowsinessResult(score=35.0, state=DrowsinessState.SLIGHTLY_DROWSY, explanation="Slight"))
    assert hud.current_severity == "subtle"
    assert "subtle" in hud.current_message.lower() or "warning" in hud.current_message.lower()

    # DROWSY: strong warning
    hud.trigger(DrowsinessResult(score=65.0, state=DrowsinessState.DROWSY, explanation="Drowsy"))
    assert hud.current_severity == "strong"
    assert "strong" in hud.current_message.lower()

    # HIGHLY_DROWSY: critical warning
    hud.trigger(DrowsinessResult(score=85.0, state=DrowsinessState.HIGHLY_DROWSY, explanation="Highly"))
    assert hud.current_severity == "critical"
    assert "critical" in hud.current_message.lower() or "stop" in hud.current_message.lower()


def test_audio_alert_channel_behavior(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that AudioAlertChannel only triggers on HIGHLY_DROWSY, respects flags, and starts thread."""
    audio = AudioAlertChannel()

    # Stub playsound module import to prevent OS sound driver errors in tests
    playsound_mock = MagicMock()
    monkeypatch.setitem(sys.modules, "playsound", playsound_mock)

    # 1. ALERT: no audio triggered
    audio.trigger(DrowsinessResult(score=10.0, state=DrowsinessState.ALERT, explanation="Ok"))
    assert audio.play_thread is None

    # 2. HIGHLY_DROWSY but disabled in config: no audio triggered
    monkeypatch.setattr(config, "AUDIO_ALERT_ENABLED", False)
    monkeypatch.setattr(os.path, "exists", lambda path: True)
    monkeypatch.setattr(config, "ALARM_SOUND_PATH", "mock_alarm.wav")
    
    audio.trigger(DrowsinessResult(score=85.0, state=DrowsinessState.HIGHLY_DROWSY, explanation="Highly"))
    assert audio.play_thread is None

    # 3. HIGHLY_DROWSY, enabled in config, but file doesn't exist: no audio triggered
    monkeypatch.setattr(config, "AUDIO_ALERT_ENABLED", True)
    monkeypatch.setattr(os.path, "exists", lambda path: False)
    
    audio.trigger(DrowsinessResult(score=85.0, state=DrowsinessState.HIGHLY_DROWSY, explanation="Highly"))
    assert audio.play_thread is None

    # 4. HIGHLY_DROWSY, enabled in config, file exists: launches playback thread
    monkeypatch.setattr(os.path, "exists", lambda path: True)
    
    audio.trigger(DrowsinessResult(score=85.0, state=DrowsinessState.HIGHLY_DROWSY, explanation="Highly"))
    assert audio.play_thread is not None
    audio.play_thread.join(timeout=1.0)


def test_alert_manager_type_validation() -> None:
    """Verify AlertManager processes only DrowsinessResult instances."""
    manager = AlertManager()
    with pytest.raises(TypeError):
        manager.process_result("invalid_payload")  # type: ignore
