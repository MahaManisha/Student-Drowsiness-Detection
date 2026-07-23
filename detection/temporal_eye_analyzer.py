"""
Student Drowsiness Detection System - Temporal Eye Analyzer Module

This module provides the TemporalEyeAnalyzer class and EyeTemporalRecord dataclass.
It is responsible for maintaining the historical sequence of eye openness states
and Eye Aspect Ratio (EAR) metric values over time (frames) to facilitate stateful
analysis of eye behavior.

Follows SOLID design principles:
- Single Responsibility Principle (SRP): Focuses exclusively on storing, validating,
  and aggregating chronological frame logs of eye states. It does not perform detection,
  classification, alerting, or UI layout operations.
- Open/Closed Principle (OCP): Designed with configurable window limits and extensible
  statistical methods. It can be extended or subclassed to support customized temporal behaviors.
- Liskov Substitution Principle (LSP): Adheres strictly to standard typing structures
  and expected outputs, ensuring subtyping compatibility.
- Interface Segregation Principle (ISP): Exposes minimal, highly cohesive public interfaces
  (update, clear, and statistics getters) rather than forcing dependencies on large monolithic interfaces.
- Dependency Inversion Principle (DIP): Relies on abstractions (like standard Python types,
  dataclasses, and the EyeState enum) rather than concrete lower-level camera streams or GUI drivers.
"""

from collections import deque
from dataclasses import dataclass
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from detection.eye_state_classifier import EyeState
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class EyeTemporalRecord:
    """
    Structured data representing a single frame's eye state snapshot within the temporal analyzer.
    """
    timestamp: float          # Unix epoch timestamp of when the frame was processed
    frame_index: int          # Monotonically increasing frame index
    right_state: EyeState     # Classification state of the right eye
    left_state: EyeState      # Classification state of the left eye
    overall_state: EyeState   # Combined dual-eye classification state
    avg_ear: Optional[float]  # Combined average Eye Aspect Ratio value


class TemporalEyeAnalyzer:
    """
    Manages a sliding window of historical frame eye states and calculates
    temporal eye-tracking metrics (e.g., rolling averages, variances, closure rates,
    and consecutive open/closed streaks) to support drowsiness evaluations.
    """

    def __init__(
        self,
        max_window_size: int = 100,
        min_blink_duration: int = 1,
        max_blink_duration: int = 15,
        fps: float = 30.0,
    ) -> None:
        """
        Initializes the TemporalEyeAnalyzer with a configurable maximum buffer history,
        blink duration thresholds, and camera FPS.

        Args:
            max_window_size (int): The maximum number of past frames to keep in the
                sliding window buffer. Defaults to 100.
            min_blink_duration (int): Minimum number of consecutive closed frames for a valid blink. Defaults to 1.
            max_blink_duration (int): Maximum number of consecutive closed frames for a valid blink. Defaults to 15.
            fps (float): Estimated camera acquisition frame rate in frames per second. Defaults to 30.0.
        """
        if max_window_size <= 0:
            logger.warning(
                f"Invalid max_window_size: {max_window_size}. Falling back to default (100)."
            )
            max_window_size = 100

        if min_blink_duration <= 0:
            logger.warning(
                f"Invalid min_blink_duration: {min_blink_duration}. Setting to 1."
            )
            min_blink_duration = 1

        if max_blink_duration < min_blink_duration:
            logger.warning(
                f"Invalid max_blink_duration: {max_blink_duration} is less than min_blink_duration {min_blink_duration}. "
                f"Setting to {min_blink_duration + 14}."
            )
            max_blink_duration = min_blink_duration + 14

        if fps <= 0.0:
            logger.warning(
                f"Invalid camera FPS value: {fps}. Falling back to default (30.0)."
            )
            fps = 30.0

        self.max_window_size: int = max_window_size
        self.min_blink_duration: int = min_blink_duration
        self.max_blink_duration: int = max_blink_duration
        self.fps: float = float(fps)
        self.history: deque[EyeTemporalRecord] = deque(maxlen=self.max_window_size)

        # Streak tracking
        self.consecutive_closed_frames: int = 0
        self.consecutive_open_frames: int = 0

        # Blink counter
        self.blink_count: int = 0

        # Lifetime counters
        self.total_frames_processed: int = 0

        logger.info(
            f"TemporalEyeAnalyzer initialized with max_window_size: {self.max_window_size}, "
            f"min_blink_duration: {self.min_blink_duration}, max_blink_duration: {self.max_blink_duration}, "
            f"fps: {self.fps}"
        )

    def update(
        self,
        right_state: EyeState,
        left_state: EyeState,
        overall_state: EyeState,
        avg_ear: Optional[float],
        frame_index: Optional[int] = None,
        timestamp: Optional[float] = None,
    ) -> EyeTemporalRecord:
        """
        Processes and records the eye state metrics of a new frame, updating the sliding
        history window and consecutive state counters.

        Args:
            right_state (EyeState): The single-frame classification state of the right eye.
            left_state (EyeState): The single-frame classification state of the left eye.
            overall_state (EyeState): The combined dual-eye classification state.
            avg_ear (Optional[float]): The average EAR for the current frame.
            frame_index (Optional[int]): The frame index. If None, auto-increments based
                on total processed frames.
            timestamp (Optional[float]): Epoch timestamp of the frame. If None, generated automatically.

        Returns:
            EyeTemporalRecord: The structured record created and stored for the current frame.
        """
        # Fallback values
        if timestamp is None:
            timestamp = time.time()
        if frame_index is None:
            frame_index = self.total_frames_processed

        # Validate types/values safely
        if not isinstance(right_state, EyeState):
            logger.warning(f"Unexpected right_state type: {type(right_state)}. Casting to UNKNOWN.")
            right_state = EyeState.UNKNOWN
        if not isinstance(left_state, EyeState):
            logger.warning(f"Unexpected left_state type: {type(left_state)}. Casting to UNKNOWN.")
            left_state = EyeState.UNKNOWN
        if not isinstance(overall_state, EyeState):
            logger.warning(f"Unexpected overall_state type: {type(overall_state)}. Casting to UNKNOWN.")
            overall_state = EyeState.UNKNOWN

        if avg_ear is not None:
            try:
                avg_ear = float(avg_ear)
                if not (0.0 <= avg_ear <= 1.0):
                    logger.debug(f"Physiologically abnormal EAR value: {avg_ear}")
            except (ValueError, TypeError) as e:
                logger.warning(f"Cannot cast avg_ear '{avg_ear}' to float: {e}. Setting to None.")
                avg_ear = None

        # Build record
        record = EyeTemporalRecord(
            timestamp=timestamp,
            frame_index=frame_index,
            right_state=right_state,
            left_state=left_state,
            overall_state=overall_state,
            avg_ear=avg_ear,
        )

        # Update sliding history
        self.history.append(record)
        self.total_frames_processed += 1

        # Update streak metrics based on overall state
        if overall_state == EyeState.CLOSED:
            self.consecutive_closed_frames += 1
            self.consecutive_open_frames = 0
        elif overall_state == EyeState.OPEN:
            # Check for completed blink transition: CLOSED -> OPEN
            if self.consecutive_closed_frames > 0:
                closed_duration = self.consecutive_closed_frames
                if self.min_blink_duration <= closed_duration <= self.max_blink_duration:
                    self.blink_count += 1
                    logger.info(
                        f"Blink detected! Frame: {frame_index} | Duration: {closed_duration} frames | "
                        f"Total Blink Count: {self.blink_count}"
                    )
                else:
                    logger.debug(
                        f"Eye opened after {closed_duration} frames, but not classified as a blink "
                        f"(valid range: [{self.min_blink_duration}, {self.max_blink_duration}])."
                    )
            
            self.consecutive_open_frames += 1
            self.consecutive_closed_frames = 0
        elif overall_state == EyeState.UNKNOWN:
            # Safely ignore UNKNOWN eye states: do not increment and do not reset counters
            logger.info(
                f"Frame {frame_index}: EyeState is UNKNOWN. Ignoring state update for streak counters. "
                f"Consecutive CLOSED: {self.consecutive_closed_frames}, Consecutive OPEN: {self.consecutive_open_frames}"
            )

        logger.debug(
            f"Analyzer Update -> Frame: {frame_index} | State: {overall_state.value} | "
            f"EAR: {avg_ear if avg_ear is not None else 'N/A'} | "
            f"Consecutive Closed: {self.consecutive_closed_frames} | "
            f"Consecutive Open: {self.consecutive_open_frames} | "
            f"Total Blinks: {self.blink_count}"
        )

        return record

    def get_history(self) -> List[EyeTemporalRecord]:
        """
        Retrieves a copy of all frame records currently stored in the sliding history buffer.

        Returns:
            List[EyeTemporalRecord]: List containing historical records, ordered from oldest to newest.
        """
        return list(self.history)

    def get_consecutive_closed_frames(self) -> int:
        """
        Retrieves the current streak of consecutive frames with a CLOSED overall eye state.

        Returns:
            int: Number of consecutive CLOSED frames.
        """
        return self.consecutive_closed_frames

    def get_closed_frame_count(self) -> int:
        """
        Retrieves the current continuous closed frame count.

        Returns:
            int: Number of consecutive CLOSED frames.
        """
        return self.consecutive_closed_frames

    def get_closed_duration_seconds(self) -> float:
        """
        Calculates the current continuous closed duration in seconds using camera FPS.

        Returns:
            float: Continuous closed duration in seconds.
        """
        return float(self.consecutive_closed_frames / self.fps)

    def set_fps(self, fps: float) -> None:
        """
        Updates the camera FPS configuration dynamically.

        Args:
            fps (float): The new frames per second value.
        """
        if fps <= 0.0:
            logger.warning(f"Invalid camera FPS '{fps}'. Configuration remains unchanged.")
        else:
            old_fps = self.fps
            self.fps = float(fps)
            logger.info(f"Camera FPS updated dynamically: {old_fps} -> {self.fps}")

    def get_consecutive_open_frames(self) -> int:
        """
        Retrieves the current streak of consecutive frames with an OPEN overall eye state.

        Returns:
            int: Number of consecutive OPEN frames.
        """
        return self.consecutive_open_frames

    def get_blink_count(self) -> int:
        """
        Retrieves the total number of detected completed blinks.

        Returns:
            int: Total count of detected blinks.
        """
        return self.blink_count

    def set_blink_count(self, count: int) -> None:
        """
        Updates the blink count to a specific value.

        Args:
            count (int): The new value for the blink count.
        """
        if count < 0:
            logger.warning(f"Attempted to set negative blink count: {count}. Setting to 0.")
            self.blink_count = 0
        else:
            self.blink_count = count
            logger.info(f"Blink count updated manually to: {self.blink_count}")

    def get_rolling_average_ear(self, window_len: Optional[int] = None) -> float:
        """
        Calculates the average EAR value over a specified rolling window.

        Args:
            window_len (Optional[int]): The number of recent frames to analyze.
                If None or greater than the current history size, the entire history is used.

        Returns:
            float: Arithmetic average of valid EAR values in the window. Returns 0.0 if
                there are no valid EAR values.
        """
        records = self._get_recent_records(window_len)
        valid_ears = [r.avg_ear for r in records if r.avg_ear is not None]

        if not valid_ears:
            return 0.0

        return float(np.mean(valid_ears))

    def get_rolling_ear_variance(self, window_len: Optional[int] = None) -> float:
        """
        Calculates the variance of average EAR values within a specified rolling window.

        Args:
            window_len (Optional[int]): The number of recent frames to analyze.
                If None or greater than the current history size, the entire history is used.

        Returns:
            float: The variance of EAR values in the window. Returns 0.0 if there
                are fewer than 2 valid EAR values.
        """
        records = self._get_recent_records(window_len)
        valid_ears = [r.avg_ear for r in records if r.avg_ear is not None]

        if len(valid_ears) < 2:
            return 0.0

        return float(np.var(valid_ears))

    def get_closure_percentage(self, window_len: Optional[int] = None) -> float:
        """
        Calculates the percentage of closed-eye frames within a specified rolling window.
        Only considers frames with a known state (OPEN or CLOSED), excluding UNKNOWN frames.

        Args:
            window_len (Optional[int]): The number of recent frames to analyze.
                If None or greater than the current history size, the entire history is used.

        Returns:
            float: The ratio of CLOSED frames to total known frames in the window (range [0.0, 1.0]).
                Returns 0.0 if no known eye states are present in the window.
        """
        records = self._get_recent_records(window_len)
        known_records = [
            r for r in records if r.overall_state in (EyeState.OPEN, EyeState.CLOSED)
        ]

        if not known_records:
            return 0.0

        closed_count = sum(1 for r in known_records if r.overall_state == EyeState.CLOSED)
        return float(closed_count / len(known_records))

    def clear_history(self) -> None:
        """
        Clears the sliding window history buffer and resets all streak tracking statistics.
        """
        self.history.clear()
        self.consecutive_closed_frames = 0
        self.consecutive_open_frames = 0
        self.blink_count = 0
        logger.info("TemporalEyeAnalyzer history, streak tracking, and blink count cleared.")

    def _get_recent_records(self, window_len: Optional[int] = None) -> List[EyeTemporalRecord]:
        """
        Internal utility to retrieve the most recent N records from history.

        Args:
            window_len (Optional[int]): The number of records to retrieve from the end of the history.

        Returns:
            List[EyeTemporalRecord]: Sub-list of recent records.
        """
        history_list = list(self.history)
        if not history_list:
            return []

        if window_len is None or window_len >= len(history_list) or window_len <= 0:
            return history_list

        return history_list[-window_len:]
