"""
Student Drowsiness Detection System - Session Statistics Module

This module provides the SessionStatisticsTracker class to accumulate real-time
telemetry metrics and export comprehensive session statistics upon shutdown.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class SessionStatisticsTracker:
    """
    Tracks and compiles aggregate session metrics including total session duration,
    EAR/MAR averages, event occurrences, and state-wise time breakdown.
    """

    def __init__(self) -> None:
        """
        Initializes statistics variables and starts session clock.
        """
        self.start_time: float = time.time()

        # Running average accumulators
        self.ear_sum: float = 0.0
        self.ear_count: int = 0

        self.mar_sum: float = 0.0
        self.mar_count: int = 0

        # Maximum thresholds
        self.highest_score: float = 0.0
        self.longest_eye_closure: float = 0.0

        # Totals
        self.blink_count: int = 0
        self.yawn_count: int = 0
        self.num_alerts: int = 0

        # State tracking durations
        self.state_times: Dict[str, float] = {
            "ALERT": 0.0,
            "SLIGHTLY_DROWSY": 0.0,
            "DROWSY": 0.0,
            "HIGHLY_DROWSY": 0.0,
        }
        self.last_state: Optional[str] = None
        self.last_state_change_time: float = time.time()

        # Alert monitoring
        self.in_alert_period: bool = False

        logger.info("SessionStatisticsTracker initialized.")

    def update(
        self,
        current_state: Any,
        score: float,
        avg_ear: Optional[float],
        mar: Optional[float],
        blink_count: int,
        yawn_count: int,
        closed_duration: float,
    ) -> None:
        """
        Updates trackers with telemetry parameters from the current frame.

        Args:
            current_state (Any): Current DrowsinessState enum or string.
            score (float): Current drowsiness score (0-100).
            avg_ear (float | None): Calculated average EAR.
            mar (float | None): Calculated Mouth Aspect Ratio.
            blink_count (int): Total blinks detected in this session.
            yawn_count (int): Total yawns detected in this session.
            closed_duration (float): Active consecutive eye closure duration.
        """
        current_time = time.time()

        # Normalize state parameter to clean uppercase string
        state_str = current_state.name if hasattr(current_state, "name") else str(current_state)
        state_str = state_str.upper().replace(" ", "_")

        # 1. Update running sums for averages
        if avg_ear is not None and avg_ear > 0.0:
            self.ear_sum += avg_ear
            self.ear_count += 1

        if mar is not None and mar > 0.0:
            self.mar_sum += mar
            self.mar_count += 1

        # 2. Update extreme metrics
        if score > self.highest_score:
            self.highest_score = score

        if closed_duration > self.longest_eye_closure:
            self.longest_eye_closure = closed_duration

        # 3. Synchronize absolute counts
        self.blink_count = blink_count
        self.yawn_count = yawn_count

        # 4. State transition and warning alert period tracking
        if self.last_state is None:
            self.last_state = state_str
            self.last_state_change_time = current_time
            if state_str != "ALERT":
                self.in_alert_period = True
                self.num_alerts = 1
            return

        if state_str != self.last_state:
            # Accumulate time in the state that is ending
            elapsed = current_time - self.last_state_change_time
            if self.last_state in self.state_times:
                self.state_times[self.last_state] += elapsed
            else:
                self.state_times[self.last_state] = elapsed

            # Process warning alert boundaries
            if self.last_state == "ALERT" and state_str != "ALERT":
                # Entered warning sequence
                self.in_alert_period = True
                self.num_alerts += 1
            elif state_str == "ALERT":
                # Returned to safe baseline
                self.in_alert_period = False

            # Update tracking states
            self.last_state = state_str
            self.last_state_change_time = current_time

    def get_stats(self) -> Dict[str, Any]:
        """
        Compiles and returns the current session statistics dictionary.

        Returns:
            Dict[str, Any]: Summary dictionary containing all compiled parameters.
        """
        current_time = time.time()
        total_session_time = current_time - self.start_time

        # Calculate accurate state times including the active state up to this moment
        actual_state_times = self.state_times.copy()
        if self.last_state is not None:
            elapsed = current_time - self.last_state_change_time
            if self.last_state in actual_state_times:
                actual_state_times[self.last_state] += elapsed
            else:
                actual_state_times[self.last_state] = elapsed

        # Calculate overall averages
        avg_ear = self.ear_sum / self.ear_count if self.ear_count > 0 else 0.0
        avg_mar = self.mar_sum / self.mar_count if self.mar_count > 0 else 0.0

        return {
            "total_session_time": round(total_session_time, 2),
            "average_ear": round(avg_ear, 4),
            "average_mar": round(avg_mar, 4),
            "blink_count": self.blink_count,
            "yawn_count": self.yawn_count,
            "highest_score": round(self.highest_score, 2),
            "time_spent_in_states": {k: round(v, 2) for k, v in actual_state_times.items()},
            "longest_eye_closure": round(self.longest_eye_closure, 3),
            "number_of_alerts": self.num_alerts,
        }

    def save_stats(self, output_path: str) -> None:
        """
        Compiles and saves the session statistics summary as pretty-printed JSON.

        Args:
            output_path (str): Target output file path.
        """
        stats = self.get_stats()
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(stats, f, indent=4, sort_keys=True)
            logger.info(f"Session statistics successfully saved to: {path}")
        except Exception as e:
            logger.error(f"Failed to save session statistics: {e}", exc_info=True)
