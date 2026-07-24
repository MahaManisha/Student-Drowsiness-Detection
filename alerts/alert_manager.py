"""
Student Drowsiness Detection System - Alert Manager Module

This module provides the AlertManager and AlertChannel interfaces to route
drowsiness alerts (visual HUD overlays, audio alarms, or other future channels)
without creating tight coupling with AI/computer vision estimation modules.

Follows SOLID design principles:
- Single Responsibility Principle (SRP): AlertManager coordinates alert routing and
  cooldown limits; HUDAlertChannel handles visual rendering updates; AudioAlertChannel
  manages audible playback.
- Open/Closed Principle (OCP): New alerting mechanisms (e.g. email, SMS, mobile push)
  can be added by extending AlertChannel and registering with the AlertManager without
  modifying core routing code.
- Liskov Substitution Principle (LSP): Concrete channels subclass the AlertChannel ABC,
  implementing the unified `trigger` signature.
- Interface Segregation Principle (ISP): Uses simple, dedicated interfaces, not bloated
  multipurpose base classes.
- Dependency Inversion Principle (DIP): AlertManager depends on the abstract AlertChannel
  interface, not concrete alert channel implementations.
"""

import time
import os
import threading
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import config
from detection import DrowsinessResult, DrowsinessState
from utils.logger import get_logger

logger = get_logger(__name__)


class AlertChannel(ABC):
    """
    Interface for implementing alert delivery channels.
    Follows Dependency Inversion Principle (DIP) and Open/Closed Principle (OCP).
    """

    @abstractmethod
    def trigger(self, result: DrowsinessResult) -> None:
        """
        Triggers the specific alert channel based on the drowsiness result.

        Args:
            result (DrowsinessResult): The output from the decision engine.
        """
        pass


class HUDAlertChannel(AlertChannel):
    """
    Channel responsible for managing HUD visual warnings.
    Updates the active overlay warning message and severity.
    """

    def __init__(self) -> None:
        self.current_message: Optional[str] = None
        self.current_severity: Optional[str] = None

    def trigger(self, result: DrowsinessResult) -> None:
        enabled = getattr(config, "VISUAL_ALERT_ENABLED", True)
        if not enabled:
            logger.info("HUD Alert: Visual alerts are disabled in config.")
            return

        state = result.state
        if state == DrowsinessState.ALERT:
            self.current_message = None
            self.current_severity = None
            logger.info("HUD Alert: State is ALERT. Visual warnings cleared.")
        elif state == DrowsinessState.SLIGHTLY_DROWSY:
            self.current_message = "Subtle warning: Try blinking or shifting focus."
            self.current_severity = "subtle"
            logger.warning(f"HUD Alert [SUBTLE]: {self.current_message} (Score: {result.score:.1f})")
        elif state == DrowsinessState.DROWSY:
            self.current_message = "Strong warning: High drowsiness detected! Take a break."
            self.current_severity = "strong"
            logger.warning(f"HUD Alert [STRONG]: {self.current_message} (Score: {result.score:.1f})")
        elif state == DrowsinessState.HIGHLY_DROWSY:
            self.current_message = "CRITICAL WARNING: STOP AND REST IMMEDIATELY!"
            self.current_severity = "critical"
            logger.error(f"HUD Alert [CRITICAL]: {self.current_message} (Score: {result.score:.1f})")


class AudioAlertChannel(AlertChannel):
    """
    Channel responsible for playing audible alarms on critical drowsiness states.
    Uses asynchronous background threads to prevent blocking the main video pipeline.
    """

    def __init__(self) -> None:
        self.play_thread: Optional[threading.Thread] = None

    def trigger(self, result: DrowsinessResult) -> None:
        if result.state != DrowsinessState.HIGHLY_DROWSY:
            return

        enabled = getattr(config, "AUDIO_ALERT_ENABLED", True)
        if not enabled:
            logger.info("Audio Alert: Audio alarms are disabled in config.")
            return

        sound_path = getattr(config, "ALARM_SOUND_PATH", "")
        if not sound_path or not os.path.exists(sound_path):
            logger.warning(f"Audio Alert: Sound path '{sound_path}' does not exist. Cannot play audio alarm.")
            return

        logger.error(f"Audio Alert: Triggering audible alarm sound! (Score: {result.score:.1f}, Path: {sound_path})")

        try:
            self.play_thread = threading.Thread(
                target=self._play_sound,
                args=(str(sound_path),),
                daemon=True
            )
            self.play_thread.start()
        except Exception as e:
            logger.error(f"Audio Alert: Failed to start audio playback thread: {e}")

    def _play_sound(self, path: str) -> None:
        try:
            from playsound import playsound
            playsound(path)
        except ImportError:
            logger.warning("Audio Alert: 'playsound' module is not installed. Audio alarm simulated in logs.")
        except Exception as e:
            logger.error(f"Audio Alert: Error playing sound file: {e}")


class AlertManager:
    """
    Manages the routing of drowsiness results to active alert channels.
    Maintains alert suppression (cooldowns) per drowsiness state to prevent
    repeated alarms while in the same state.
    """

    def __init__(self, channels: Optional[List[AlertChannel]] = None) -> None:
        self.channels: List[AlertChannel] = channels if channels is not None else []
        self.last_state: DrowsinessState = DrowsinessState.ALERT

        # Maps drowsiness states to the epoch timestamp when they were last triggered
        self.last_trigger_times: Dict[DrowsinessState, float] = {}

        # Load cooldown configurations
        self.cooldown_period: float = getattr(config, "ALERT_COOLDOWN_SECONDS", 5.0)
        
        # Event logging for dashboard display
        self.event_log: List[str] = ["System monitoring active."]
        
        logger.info(
            f"AlertManager initialized. Cooldown: {self.cooldown_period}s. "
            f"Active channels: {[c.__class__.__name__ for c in self.channels]}"
        )

    def register_channel(self, channel: AlertChannel) -> None:
        """
        Registers a new AlertChannel.
        Demonstrates the Open/Closed Principle (OCP) by allowing the addition of new channels
        (e.g., Email, SMS, Mobile push) without changing the AlertManager implementation.
        """
        if not isinstance(channel, AlertChannel):
            raise TypeError("Channel must implement the AlertChannel interface.")
        self.channels.append(channel)
        logger.info(f"Registered new alert channel: {channel.__class__.__name__}")

    def process_result(self, result: DrowsinessResult) -> None:
        """
        Processes a DrowsinessResult from the decision engine.
        Applies cooldown logic and routes triggers to all registered channels.

        Args:
            result (DrowsinessResult): Output from StudentDrowsinessDecisionEngine.
        """
        if not isinstance(result, DrowsinessResult):
            raise TypeError("AlertManager.process_result expects a DrowsinessResult instance.")

        current_state = result.state
        current_time = time.time()

        # 1. State is ALERT -> Clear warnings/alarms, no action
        if current_state == DrowsinessState.ALERT:
            if self.last_state != DrowsinessState.ALERT:
                event_desc = "State transitioned back to ALERT (System Clear)"
                self.event_log.append(event_desc)
                logger.info("Transitioned back to ALERT state. Resetting active alerts.")
                self._trigger_all(result)
                self.last_state = DrowsinessState.ALERT
            return

        # 2. Check transition and cooldown rules for warning states
        is_state_changed = (current_state != self.last_state)
        last_trigger_time = self.last_trigger_times.get(current_state, 0.0)
        time_since_last_trigger = current_time - last_trigger_time
        has_cooldown_expired = (time_since_last_trigger >= self.cooldown_period)

        if is_state_changed or has_cooldown_expired:
            trigger_reason = (
                "State changed"
                if is_state_changed
                else f"Cooldown expired ({time_since_last_trigger:.1f}s >= {self.cooldown_period}s)"
            )
            event_desc = f"State {current_state.value} alert triggered: {trigger_reason}"
            self.event_log.append(event_desc)
            logger.info(f"Triggering alerts for state {current_state.value}. Reason: {trigger_reason}")

            self._trigger_all(result)
            self.last_trigger_times[current_state] = current_time
            self.last_state = current_state
        else:
            logger.debug(
                f"Suppressed alert for state {current_state.value}. "
                f"Time elapsed: {time_since_last_trigger:.1f}s < cooldown: {self.cooldown_period}s"
            )

    def _trigger_all(self, result: DrowsinessResult) -> None:
        """Helper to invoke trigger on all registered channels."""
        for channel in self.channels:
            try:
                channel.trigger(result)
            except Exception as e:
                logger.error(
                    f"Error executing channel {channel.__class__.__name__}.trigger: {e}",
                    exc_info=True,
                )

    def get_last_event(self) -> str:
        """
        Retrieves the most recent alert/event log entry.
        """
        return self.event_log[-1] if self.event_log else "No events recorded."

