"""
Student Drowsiness Detection System - Yawn Detector Module

This module provides the YawnDetector class, which serves as the temporal sequence
analyzer for evaluating Mouth Aspect Ratio (MAR) transitions to identify yawning events.

Follows SOLID design principles:
- Single Responsibility Principle (SRP): Focuses exclusively on yawn tracking,
  temporal sequence accumulation, and state transitions for mouth openness.
- Open/Closed Principle (OCP): Configurable threshold limits and frame durations
  without modifying baseline state machines.
- Liskov Substitution Principle (LSP): Maintains strict, predictable type contracts
  for update methods and metric properties.
- Interface Segregation Principle (ISP): Exposes modular getters for counts,
  consecutive frame streaks, and active status states.
- Dependency Inversion Principle (DIP): Operates independently of GUI structures,
  camera sources, or facial landmark detectors.

Note:
This module contains the architectural skeleton, property tracking states,
and method interfaces for Phase 9.1.
The actual yawn classification logic and streak accumulation will be implemented in Phase 9.2.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

import config
from utils.logger import get_logger

logger = get_logger(__name__)

# Default configurations from central config file
DEFAULT_MAR_THRESHOLD: float = getattr(config, "MAR_THRESHOLD", 0.60)
DEFAULT_MAR_CONSECUTIVE_FRAMES: int = getattr(config, "MAR_CONSECUTIVE_FRAMES", 15)


class MouthState(Enum):
    """Enumeration representing physiological mouth states."""
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    UNKNOWN = "UNKNOWN"


class YawnDetector:
    """
    Temporal sequence analyzer to monitor Mouth Aspect Ratio (MAR) streams and detect yawn events.

    Attributes:
        mar_threshold (float): Mouth aspect ratio threshold above which the mouth is considered open.
        yawn_duration_frames (int): Minimum consecutive frames the mouth must remain open to count as a yawn.
        fps (float): Current camera execution frame rate target.
        yawn_count (int): Cumulative count of confirmed yawning events.
        consecutive_open_frames (int): Live streak counter of consecutive mouth-open frames.
        is_active_yawn (bool): State indicator flag showing whether the subject is currently yawning.
    """

    def __init__(
        self,
        fps: float = 30.0,
        mar_threshold: Optional[float] = None,
        yawn_duration_frames: Optional[int] = None,
    ) -> None:
        """
        Initializes the YawnDetector with threshold boundaries and lifecycle tracking accumulators.

        Args:
            fps (float): Frame rate target of the capture thread (default: 30.0).
            mar_threshold (Optional[float]): Threshold value for open mouth classification.
                Defaults to config.MAR_THRESHOLD or 0.60.
            yawn_duration_frames (Optional[int]): Minimum consecutive frames representing a yawn.
                Defaults to config.MAR_CONSECUTIVE_FRAMES or 15.
        """
        self.fps: float = float(fps)
        self.mar_threshold: float = (
            float(mar_threshold) if mar_threshold is not None else DEFAULT_MAR_THRESHOLD
        )
        self.yawn_duration_frames: int = (
            int(yawn_duration_frames) if yawn_duration_frames is not None else DEFAULT_MAR_CONSECUTIVE_FRAMES
        )

        # State trackers
        self.yawn_count: int = 0
        self.consecutive_open_frames: int = 0
        self.consecutive_closed_frames: int = 0
        self.is_active_yawn: bool = False
        self.frame_counter: int = 0

        logger.info(
            f"YawnDetector initialized with FPS: {self.fps:.1f} | "
            f"MAR Threshold: {self.mar_threshold:.3f} | "
            f"Yawn Duration: {self.yawn_duration_frames} frames ({self.yawn_duration_frames / self.fps:.2f}s)"
        )

    def classify_mouth_state(self, mar_value: Optional[float]) -> MouthState:
        """
        Classifies the current mouth state as OPEN or CLOSED based on the MAR value and threshold.

        Args:
            mar_value (Optional[float]): Computed Mouth Aspect Ratio for the current frame.

        Returns:
            MouthState: OPEN if MAR >= threshold, CLOSED if MAR < threshold, or UNKNOWN if invalid.
        """
        if mar_value is None:
            logger.debug("Mouth state classification received None for MAR. Returning UNKNOWN.")
            return MouthState.UNKNOWN

        try:
            # MAR must be non-negative
            if mar_value < 0.0:
                logger.warning(f"Mouth state classification received negative MAR: {mar_value}. Returning UNKNOWN.")
                return MouthState.UNKNOWN

            if mar_value >= self.mar_threshold:
                logger.debug(f"Mouth state classified as OPEN (MAR: {mar_value:.4f} >= Threshold: {self.mar_threshold:.4f})")
                return MouthState.OPEN
            else:
                logger.debug(f"Mouth state classified as CLOSED (MAR: {mar_value:.4f} < Threshold: {self.mar_threshold:.4f})")
                return MouthState.CLOSED
        except Exception as e:
            logger.error(f"Error classifying mouth state for MAR value {mar_value}: {e}")
            return MouthState.UNKNOWN

    def update(self, mar_value: Optional[float], current_fps: Optional[float] = None) -> None:
        """
        Updates the temporal state machine with the current frame's MAR value.

        Args:
            mar_value (Optional[float]): Computed Mouth Aspect Ratio for the current frame.
            current_fps (Optional[float]): Optional runtime frame rate override.
        """
        if current_fps is not None and current_fps > 0.0:
            self.fps = float(current_fps)

        self.frame_counter += 1

        state = self.classify_mouth_state(mar_value)

        # Ignore UNKNOWN states safely
        if state == MouthState.UNKNOWN:
            logger.debug("Mouth state is UNKNOWN; skipping temporal calculation for this frame.")
            return

        if state == MouthState.OPEN:
            self.consecutive_open_frames += 1
            self.consecutive_closed_frames = 0

            # If the open frames streak reaches the minimum duration threshold, activate the yawn state
            if self.consecutive_open_frames >= self.yawn_duration_frames:
                if not self.is_active_yawn:
                    self.is_active_yawn = True
                    logger.info(
                        f"Active yawn detected! Streak reached threshold: "
                        f"{self.consecutive_open_frames} >= {self.yawn_duration_frames}"
                    )
        else:  # MouthState.CLOSED
            # If there was an active yawn ongoing, transitioning to CLOSED completes the yawn event
            if self.is_active_yawn:
                self.yawn_count += 1
                logger.info(
                    f"Yawn event completed (Mouth closed after {self.consecutive_open_frames} frames). "
                    f"Total yawn events: {self.yawn_count}"
                )
                self.is_active_yawn = False

            self.consecutive_closed_frames += 1
            self.consecutive_open_frames = 0

        # Log periodically for debug monitoring
        if self.frame_counter % 30 == 0:
            logger.debug(
                f"[Frame {self.frame_counter}] YawnDetector Telemetry - "
                f"MAR: {mar_value if mar_value is not None else 'N/A'} | "
                f"Consecutive Open: {self.consecutive_open_frames} | "
                f"Consecutive Closed: {self.consecutive_closed_frames} | "
                f"Yawn Count: {self.yawn_count}"
            )

    def get_yawn_count(self) -> int:
        """
        Retrieves the cumulative count of detected yawn events.

        Returns:
            int: Total yawn count.
        """
        return self.yawn_count

    def get_consecutive_open_frames(self) -> int:
        """
        Retrieves the current streak of consecutive frames where the mouth is classified as open.

        Returns:
            int: Streak frame count.
        """
        return self.consecutive_open_frames

    def get_open_frame_count(self) -> int:
        """
        Retrieves the current streak of consecutive open frames (alias).

        Returns:
            int: Streak frame count.
        """
        return self.consecutive_open_frames

    def get_open_duration_seconds(self) -> float:
        """
        Calculates the active yawn/open duration in seconds.

        Returns:
            float: Current yawn duration.
        """
        return self.get_yawn_duration_seconds()

    def get_open_duration(self) -> float:
        """
        Calculates the active yawn/open duration in seconds (alias).

        Returns:
            float: Current yawn duration.
        """
        return self.get_yawn_duration_seconds()

    def get_mouth_state(self, mar_value: Optional[float] = None) -> MouthState:
        """
        Retrieves the classified MouthState. If mar_value is not provided,
        returns OPEN if currently in an active yawn, CLOSED otherwise.

        Args:
            mar_value (Optional[float]): Computed Mouth Aspect Ratio for the current frame.

        Returns:
            MouthState: The classified mouth state enum.
        """
        if mar_value is not None:
            return self.classify_mouth_state(mar_value)
        return MouthState.OPEN if self.is_active_yawn else MouthState.CLOSED

    def get_consecutive_closed_frames(self) -> int:
        """
        Retrieves the current streak of consecutive frames where the mouth is classified as closed.

        Returns:
            int: Streak frame count.
        """
        return self.consecutive_closed_frames

    def get_yawn_duration_seconds(self) -> float:
        """
        Calculates the active yawn duration in seconds based on current FPS and open frames.

        Returns:
            float: Current yawn duration.
        """
        if self.fps <= 0.0:
            return 0.0
        return float(self.consecutive_open_frames / self.fps)

    def reset_yawn_status(self) -> None:
        """
        Resets the live open and closed frames accumulators.
        """
        self.consecutive_open_frames = 0
        self.consecutive_closed_frames = 0
        self.is_active_yawn = False
        logger.info("YawnDetector live streak counters reset.")

    def reset_all(self) -> None:
        """
        Resets all state counters including cumulative yawn counts.
        """
        self.yawn_count = 0
        self.consecutive_open_frames = 0
        self.consecutive_closed_frames = 0
        self.is_active_yawn = False
        self.frame_counter = 0
        logger.info("YawnDetector fully reset to initial state.")

    def get_yawn_metrics(self) -> Dict[str, Any]:
        """
        Compiles a structured summary dictionary of yawning indicators.

        Returns:
            Dict[str, Any]: Metrics summary dictionary containing:
                - "yawn_count": int
                - "consecutive_open_frames": int
                - "consecutive_closed_frames": int
                - "yawn_duration_seconds": float
                - "is_active_yawn": bool
                - "valid": bool
        """
        return {
            "yawn_count": self.yawn_count,
            "consecutive_open_frames": self.consecutive_open_frames,
            "consecutive_closed_frames": self.consecutive_closed_frames,
            "yawn_duration_seconds": self.get_yawn_duration_seconds(),
            "is_active_yawn": self.is_active_yawn,
            "valid": self.fps > 0.0,
        }
