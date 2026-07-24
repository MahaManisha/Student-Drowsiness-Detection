"""
Student Drowsiness Detection System - Session Logger Module

This module provides the SessionLogger class to record structured session events,
such as drowsiness state transitions, alert triggers, and alert ends, to a
JSON Lines formatted log file.
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
import config
from utils.logger import get_logger

logger = get_logger(__name__)


class SessionLogger:
    """
    Structured logger that writes student drowsiness transitions and alert lifecycle
    events to a machine-readable JSON Lines (.json) file.
    """

    def __init__(self, log_path: Optional[str] = None) -> None:
        """
        Initializes the SessionLogger and ensures log directories exist.

        Args:
            log_path (str | None): Custom absolute path for the session log.
                                   If None, resolves from config.SESSION_LOG_CSV.
        """
        if log_path is None:
            # Fallback to config path and adjust extension to .json for structured formats
            csv_path = getattr(config, "SESSION_LOG_CSV", None)
            if csv_path:
                self.log_path = Path(csv_path).with_suffix(".json")
            else:
                self.log_path = Path("output/logs/drowsiness_session_log.json")
        else:
            self.log_path = Path(log_path)

        # Create target directories
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # State transition tracking
        self.last_state: Optional[str] = None
        self.last_state_change_time: float = time.time()
        self.alert_start_time: Optional[float] = None

        logger.info(f"Structured SessionLogger initialized. Log path: {self.log_path}")

    def log_event(
        self,
        event_type: str,
        state: str,
        score: float,
        confidence: float,
        duration: float,
        extra_info: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Serializes and appends a single structured event to the JSON Lines log file.

        Args:
            event_type (str): Type of event (e.g. 'alert_triggered').
            state (str): Current drowsiness state name.
            score (float): Current drowsiness score (0-100).
            confidence (float): Decision confidence percentage (0-100).
            duration (float): Duration in seconds of the event or state.
            extra_info (dict | None): Optional additional event payload key/values.
        """
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        log_entry = {
            "timestamp": timestamp,
            "event_type": event_type,
            "state": state,
            "score": round(score, 2),
            "confidence": round(confidence, 2),
            "duration": round(duration, 3),
        }
        if extra_info:
            log_entry.update(extra_info)

        try:
            # Thread-safe write by opening in append mode
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, sort_keys=True) + "\n")
            logger.info(
                f"Logged event [{event_type}] | State: {state} | "
                f"Score: {score:.1f} | Duration: {duration:.2f}s"
            )
        except Exception as e:
            logger.error(f"Failed to write structured session log: {e}", exc_info=True)

    def update(self, state: Any, score: float, confidence: float) -> None:
        """
        Evaluates the current state on each frame and logs transitions/alert events.

        Args:
            state (Any): Current DrowsinessState enum or string.
            score (float): Drowsiness score (0-100).
            confidence (float): Decision confidence percentage (0-100).
        """
        current_time = time.time()
        
        # Convert state parameter to a uniform clean string
        state_str = state.name if hasattr(state, "name") else str(state)
        state_str = state_str.upper().replace(" ", "_")

        # 1. First frame initialization
        if self.last_state is None:
            self.last_state = state_str
            self.last_state_change_time = current_time
            if state_str != "ALERT":
                self.alert_start_time = current_time
                self.log_event(
                    event_type="alert_triggered",
                    state=state_str,
                    score=score,
                    confidence=confidence,
                    duration=0.0
                )
            return

        # 2. Process transitions on state change
        if state_str != self.last_state:
            # Calculate duration of the previous state
            prev_state_duration = current_time - self.last_state_change_time

            # Log transition event
            event_type = f"student_became_{state_str.lower()}"
            self.log_event(
                event_type=event_type,
                state=state_str,
                score=score,
                confidence=confidence,
                duration=prev_state_duration
            )

            # Handle Alert Trigger and End events
            # Transition from ALERT to warning state -> Trigger new alert period
            if self.last_state == "ALERT" and state_str != "ALERT":
                self.alert_start_time = current_time
                self.log_event(
                    event_type="alert_triggered",
                    state=state_str,
                    score=score,
                    confidence=confidence,
                    duration=0.0
                )

            # Transition from warning state to ALERT -> End the alert period
            elif self.last_state != "ALERT" and state_str == "ALERT":
                alert_duration = 0.0
                if self.alert_start_time is not None:
                    alert_duration = current_time - self.alert_start_time
                    self.alert_start_time = None
                self.log_event(
                    event_type="alert_ended",
                    state=state_str,
                    score=score,
                    confidence=confidence,
                    duration=alert_duration
                )

            # Transition between warning states -> Trigger alert escalation
            elif self.last_state != "ALERT" and state_str != "ALERT":
                self.log_event(
                    event_type="alert_triggered",
                    state=state_str,
                    score=score,
                    confidence=confidence,
                    duration=0.0,
                    extra_info={"message": "Alert state modified/escalated"}
                )

            # Update tracking states
            self.last_state = state_str
            self.last_state_change_time = current_time
