"""
Student Drowsiness Detection System - Drowsiness Decision Engine Module

This module provides the StudentDrowsinessDecisionEngine class, which serves as the central
aggregator for evaluating student drowsiness levels from multi-signal tracking pipelines.

Follows SOLID design principles:
- Single Responsibility Principle (SRP): Focuses exclusively on aggregating multi-modal metrics 
  and computing the drowsiness level. It does not control video rendering or capture.
- Open/Closed Principle (OCP): Designed to accept flexible threshold weights and configuration
  coefficients, permitting new sensor streams without modifying core evaluation loops.
- Liskov Substitution Principle (LSP): Defines input metrics as standard primitive dictionaries,
  enforcing type checks on the parameter signatures.
- Interface Segregation Principle (ISP): Exposes clean, distinct methods for updating states,
  retrieving calculated drowsiness status, and resetting timers.
- Dependency Inversion Principle (DIP): Decouples the engine from specific tracker class 
  instantiations by passing structured data payloads (Data Transfer Objects) instead of 
  direct object references.

Note:
This module contains the architectural skeleton, configuration default setups, and update
signatures for Phase 11.1. Drowsiness classification and alarm logic are not implemented yet.
"""

from enum import Enum
from typing import Any, Dict, Optional
import sys
import pathlib

ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import config
try:
    from utils.logger import get_logger
    logger = get_logger(__name__)
except Exception:
    import logging
    logger = logging.getLogger(__name__)


class DrowsinessState(Enum):
    """
    State model representing the hierarchy of drowsiness alert tiers.
    """
    ALERT = "ALERT"
    SLIGHTLY_DROWSY = "SLIGHTLY_DROWSY"
    DROWSY = "DROWSY"
    HIGHLY_DROWSY = "HIGHLY_DROWSY"


class DrowsinessResult:
    """
    Encapsulates the final drowsiness score, state classification, and explanatory signals.
    """

    def __init__(self, score: float, state: DrowsinessState, explanation: str) -> None:
        self.score: float = score
        self.state: DrowsinessState = state
        self.explanation: str = explanation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "state": self.state.value,
            "explanation": self.explanation,
        }


class DrowsinessIntermediateDecision:
    """
    Encapsulates the intermediate confidence calculations and signal co-occurrences.
    """

    def __init__(
        self,
        abnormal_eye_closure: bool,
        abnormal_yawning: bool,
        abnormal_head_posture: bool,
        signal_cooccurrence_count: int,
        confidence_score: float,
        reason: str,
    ) -> None:
        self.abnormal_eye_closure: bool = abnormal_eye_closure
        self.abnormal_yawning: bool = abnormal_yawning
        self.abnormal_head_posture: bool = abnormal_head_posture
        self.signal_cooccurrence_count: int = signal_cooccurrence_count
        self.confidence_score: float = confidence_score
        self.reason: str = reason

    def to_dict(self) -> Dict[str, Any]:
        return {
            "abnormal_eye_closure": self.abnormal_eye_closure,
            "abnormal_yawning": self.abnormal_yawning,
            "abnormal_head_posture": self.abnormal_head_posture,
            "signal_cooccurrence_count": self.signal_cooccurrence_count,
            "confidence_score": self.confidence_score,
            "reason": self.reason,
        }


class StudentDrowsinessDecisionEngine:
    """
    Evaluates student drowsiness levels by combining eye closures, yawning counts,
    and head pose deflection indicators.

    Attributes:
        drowsiness_score (float): Calculated drowsiness score (normalized 0.0 to 1.0).
        is_drowsy (bool): Classification flag indicating whether the student is drowsy.
        drowsiness_state (DrowsinessState): Current classified drowsiness state level.
        frame_counter (int): Total frame updates processed.
    """

    def __init__(self) -> None:
        """
        Initializes the StudentDrowsinessDecisionEngine with default configurations.
        """
        # Load centralized configuration thresholds (Phase 11.2)
        self.max_blink_duration: float = getattr(config, "DECISION_MAX_BLINK_DURATION", 0.50)
        self.max_eye_closure_duration: float = getattr(config, "DECISION_MAX_EYE_CLOSURE_DURATION", 3.0)
        self.yawn_frequency_limit: int = getattr(config, "DECISION_YAWN_FREQUENCY_LIMIT", 2)
        self.head_pitch_limit: float = getattr(config, "DECISION_HEAD_PITCH_LIMIT", 15.0)

        # Load centralized score boundary limits (Phase 11.4)
        self.score_alert_limit: float = getattr(config, "DECISION_SCORE_ALERT_LIMIT", 30.0)
        self.score_slightly_drowsy_limit: float = getattr(config, "DECISION_SCORE_SLIGHTLY_DROWSY_LIMIT", 50.0)
        self.score_drowsy_limit: float = getattr(config, "DECISION_SCORE_DROWSY_LIMIT", 80.0)

        # Internal state trackers
        self.drowsiness_score: float = 0.0
        self.is_drowsy: bool = False
        self.drowsiness_state: DrowsinessState = DrowsinessState.ALERT
        self.intermediate_decision: Optional[DrowsinessIntermediateDecision] = None
        self.drowsiness_result: Optional[DrowsinessResult] = None
        self.frame_counter: int = 0
        self.fps: float = 30.0
        self.consecutive_droop_frames: int = 0

        logger.info(
            f"StudentDrowsinessDecisionEngine initialized. Thresholds -> "
            f"Max Blink: {self.max_blink_duration}s | Max Eye Closure: {self.max_eye_closure_duration}s | "
            f"Yawn Limit: {self.yawn_frequency_limit} | Pitch Limit: {self.head_pitch_limit} degrees | "
            f"Alert Limit: {self.score_alert_limit} | Slightly Drowsy: {self.score_slightly_drowsy_limit} | "
            f"Drowsy: {self.score_drowsy_limit}"
        )

    def update(
        self,
        eye_metrics: Dict[str, Any],
        yawn_metrics: Dict[str, Any],
        pose_metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Updates the decision engine state with the current frame's tracking data
        and evaluates intermediate rule confidence metrics.

        Args:
            eye_metrics (Dict[str, Any]): Structured metrics payload from TemporalEyeAnalyzer.
                Expected keys: "blink_count", "consecutive_closed_frames", "closed_duration_seconds".
            yawn_metrics (Dict[str, Any]): Structured metrics payload from YawnDetector.
                Expected keys: "yawn_count", "consecutive_open_frames", "yawn_duration_seconds".
            pose_metrics (Dict[str, Any]): Structured metrics payload from HeadPoseEstimator.
                Expected keys: "yaw", "pitch", "roll", "valid".

        Returns:
            Dict[str, Any]: Decision status summary dictionary including intermediate outcomes.
        """
        self.frame_counter += 1

        # Update consecutive droop frames counter (Phase 11.8 Calibration)
        pitch = pose_metrics.get("pitch", 0.0)
        pose_valid = pose_metrics.get("valid", False)
        if pose_valid and pitch > self.head_pitch_limit:
            self.consecutive_droop_frames += 1
        else:
            self.consecutive_droop_frames = 0

        # Run rule engine combining signals (Phase 11.3)
        self.intermediate_decision = self.evaluate_rules(eye_metrics, yawn_metrics, pose_metrics)

        # Run scoring and state classification (Phase 11.4)
        self.drowsiness_result = self.calculate_drowsiness(eye_metrics, yawn_metrics, pose_metrics)

        # Update internal status fields
        self.drowsiness_score = self.drowsiness_result.score
        self.is_drowsy = (
            self.drowsiness_result.state in [DrowsinessState.DROWSY, DrowsinessState.HIGHLY_DROWSY]
        )
        self.drowsiness_state = self.drowsiness_result.state

        # Periodic logging for telemetry tracking
        if self.frame_counter % 30 == 0:
            logger.debug(
                f"[Frame {self.frame_counter}] DrowsinessDecisionEngine Rule Evaluation - "
                f"Score: {self.drowsiness_score:.1f} | State: {self.drowsiness_state.value} | "
                f"Co-occurrence Count: {self.intermediate_decision.signal_cooccurrence_count} | "
                f"Confidence Score: {self.intermediate_decision.confidence_score:.2f} | "
                f"Reason: {self.intermediate_decision.reason}"
            )

        return self.get_decision_metrics()

    def evaluate_rules(
        self,
        eye_metrics: Dict[str, Any],
        yawn_metrics: Dict[str, Any],
        pose_metrics: Dict[str, Any],
    ) -> DrowsinessIntermediateDecision:
        """
        Runs the rule engine combining multi-signal tracking parameters.

        Principles:
        1. Long eye closure alone does not immediately imply high drowsiness.
        2. A single yawn alone does not imply high drowsiness.
        3. Temporary downward head deflection while reading does not trigger drowsiness.
        4. Multiple indicators occurring together increase evaluation confidence.
        """
        # Extract eye closed duration & blinks
        closed_duration = eye_metrics.get("closed_duration_seconds", 0.0)

        # Extract yawn parameters
        yawn_count = yawn_metrics.get("yawn_count", 0)
        yawn_duration = yawn_metrics.get("yawn_duration_seconds", 0.0)
        is_active_yawn = yawn_metrics.get("is_active_yawn", False)
        mar_val = yawn_metrics.get("mar_val", None)

        # Extract pose parameters
        pitch = pose_metrics.get("pitch", 0.0)
        pose_valid = pose_metrics.get("valid", False)

        # Apply rule components
        abnormal_eye_closure = closed_duration >= self.max_eye_closure_duration
        abnormal_yawning = (
            is_active_yawn
            or (yawn_duration >= 0.2)
            or (mar_val is not None and mar_val >= getattr(config, "MAR_THRESHOLD", 0.25) and yawn_duration >= 0.1)
            or (yawn_count >= self.yawn_frequency_limit)
        )
        
        # Determine if head pose contribution is allowed (Phase 11.8 Calibration)
        droop_duration = self.consecutive_droop_frames / self.fps if self.fps > 0 else 0.0
        sustained_droop = droop_duration >= 3.0
        allow_head_pose = sustained_droop or abnormal_eye_closure or abnormal_yawning
        
        # Downward head slumping (pitch > limit) is only abnormal if pose is valid and contribution is allowed
        abnormal_head_posture = pose_valid and (pitch > self.head_pitch_limit) and allow_head_pose

        # Compute signal co-occurrence count
        cooccurrence_count = int(abnormal_eye_closure) + int(abnormal_yawning) + int(abnormal_head_posture)

        # Compute confidence score and reason based on co-occurrence rules, quality of evidence, and temporal stability
        if cooccurrence_count == 3:
            confidence = 0.95
            reason = "Simultaneous prolonged eye closure, excessive yawning, and sustained downward head posture detected."
        elif cooccurrence_count == 2:
            if abnormal_eye_closure and abnormal_yawning:
                confidence = 0.75
                reason = "Co-occurrence of high-quality indicators (prolonged eye closure and excessive yawning) detected."
            elif abnormal_eye_closure and abnormal_head_posture:
                confidence = 0.65
                reason = "Co-occurrence of prolonged eye closure and sustained downward head posture detected."
            else:  # abnormal_yawning and abnormal_head_posture
                confidence = 0.50
                reason = "Co-occurrence of excessive yawning and sustained downward head posture detected."
        elif cooccurrence_count == 1:
            if abnormal_eye_closure:
                confidence = 0.40
                reason = "Isolated prolonged eye closure detected. Confidence remains low without other signals."
            elif abnormal_yawning:
                confidence = 0.50
                reason = "Isolated yawning activity detected."
            else:  # abnormal_head_posture
                confidence = 0.20
                reason = "Sustained downward head posture detected. Confidence remains low without other signals."
        else:
            confidence = 0.0
            reason = "All tracking signals are within normal baselines."

        # Add temporal stability adjustments
        if confidence > 0.0 and confidence < 0.95:
            if closed_duration >= 4.0:
                confidence += 0.05
            if droop_duration >= 5.0:
                confidence += 0.05
            confidence = min(0.95, confidence)

        return DrowsinessIntermediateDecision(
            abnormal_eye_closure=abnormal_eye_closure,
            abnormal_yawning=abnormal_yawning,
            abnormal_head_posture=abnormal_head_posture,
            signal_cooccurrence_count=cooccurrence_count,
            confidence_score=confidence,
            reason=reason,
        )

    def calculate_drowsiness(
        self,
        eye_metrics: Dict[str, Any],
        yawn_metrics: Dict[str, Any],
        pose_metrics: Dict[str, Any],
    ) -> DrowsinessResult:
        """
        Computes the aggregate drowsiness score (0-100) based on multiple signals.

        Score distribution:
        - Prolonged eye closure: Max 50 points
        - Slow blink behavior: Max 15 points
        - Yawn activity: Max 50 points (Active Yawn: min 35-50 pts to trigger DROWSY state)
        - Downward head posture: Max 15 points
        """
        closed_duration = eye_metrics.get("closed_duration_seconds", 0.0)
        yawn_count = yawn_metrics.get("yawn_count", 0)
        yawn_duration = yawn_metrics.get("yawn_duration_seconds", 0.0)
        is_active_yawn = yawn_metrics.get("is_active_yawn", False)
        mar_val = yawn_metrics.get("mar_val", None)
        pitch = pose_metrics.get("pitch", 0.0)
        pose_valid = pose_metrics.get("valid", False)

        # 1. Prolonged / Active Eye Closure (max 50 pts)
        consecutive_closed_frames = eye_metrics.get("consecutive_closed_frames", 0)
        if closed_duration >= self.max_eye_closure_duration:
            eye_pts = 50.0
        elif closed_duration > 0.0 or consecutive_closed_frames > 0:
            # Immediately trigger DROWSY state (min 50.0 pts) when eyes are closed
            eye_pts = max(50.0, (closed_duration / self.max_eye_closure_duration) * 50.0)
        else:
            eye_pts = 0.0

        # 2. Slow Blink / abnormal blink duration scoring (max 15 pts)
        if closed_duration >= self.max_blink_duration:
            blink_pts = 15.0
        else:
            blink_pts = 0.0

        # 3. Yawn Activity scoring (max 50 pts)
        # Active yawning (MAR >= threshold & open duration >= 0.1s) allocates 35-50 pts while actively open
        is_open_yawn = (
            is_active_yawn
            or (yawn_duration >= 0.2)
            or (mar_val is not None and mar_val >= getattr(config, "MAR_THRESHOLD", 0.25) and yawn_duration >= 0.1)
        )

        if is_open_yawn:
            # Active yawn in progress: min 35.0 pts up to 50.0 pts based on duration and yawn count
            if yawn_count >= self.yawn_frequency_limit:
                yawn_pts = 50.0
            else:
                yawn_pts = min(50.0, 35.0 + (yawn_duration * 10.0))
        else:
            # Mouth is closed: zero active yawn points
            yawn_pts = 0.0

        # 4. Downward Head posture deflection scoring (max 15 pts)
        abnormal_eye_closure = closed_duration >= self.max_eye_closure_duration
        abnormal_yawning = is_open_yawn or (yawn_count >= self.yawn_frequency_limit)
        droop_duration = self.consecutive_droop_frames / self.fps if self.fps > 0 else 0.0
        sustained_droop = droop_duration >= 3.0
        allow_head_pose = sustained_droop or abnormal_eye_closure or abnormal_yawning

        if pose_valid and allow_head_pose and pitch > self.head_pitch_limit:
            pose_pts = min(15.0, (pitch / self.head_pitch_limit) * 15.0)
        else:
            pose_pts = 0.0

        # Sum the contributing weights
        total_score = eye_pts + blink_pts + yawn_pts + pose_pts
        total_score = max(0.0, min(100.0, total_score))

        # Map to DrowsinessState using config boundary ranges
        if total_score >= self.score_drowsy_limit:
            state = DrowsinessState.HIGHLY_DROWSY
        elif total_score >= self.score_slightly_drowsy_limit:
            state = DrowsinessState.DROWSY
        elif total_score >= self.score_alert_limit:
            state = DrowsinessState.SLIGHTLY_DROWSY
        else:
            state = DrowsinessState.ALERT

        # Generate explanatory signals list
        explanations = []
        if eye_pts > 0:
            explanations.append(f"Prolonged eye closure (+{eye_pts:.1f} pts)")
        if blink_pts > 0:
            explanations.append(f"Slow blink behavior (+{blink_pts:.1f} pts)")
        if yawn_pts > 0:
            explanations.append(f"Yawning activity (+{yawn_pts:.1f} pts)")
        if pose_pts > 0:
            explanations.append(f"Downward head posture deflection (+{pose_pts:.1f} pts)")

        explanation_str = (
            ", ".join(explanations)
            if explanations
            else "All tracking signals within normal limits."
        )

        return DrowsinessResult(score=total_score, state=state, explanation=explanation_str)

    def get_decision_metrics(self) -> Dict[str, Any]:
        """
        Retrieves the structured evaluation outcomes and intermediate decision parameters.

        Returns:
            Dict[str, Any]: Decision summary dictionary containing:
                - "drowsiness_score": float
                - "is_drowsy": bool
                - "drowsiness_state": str
                - "intermediate_decision": Optional[Dict[str, Any]]
                - "drowsiness_result": Optional[Dict[str, Any]]
                - "valid": bool
        """
        inter_dict = (
            self.intermediate_decision.to_dict()
            if self.intermediate_decision is not None
            else None
        )
        result_dict = (
            self.drowsiness_result.to_dict()
            if self.drowsiness_result is not None
            else None
        )
        return {
            "drowsiness_score": self.drowsiness_score,
            "is_drowsy": self.is_drowsy,
            "drowsiness_state": self.drowsiness_state.value,
            "intermediate_decision": inter_dict,
            "drowsiness_result": result_dict,
            "valid": True,
        }

    def reset(self) -> None:
        """
        Resets calculated decision orientation states to initial values.
        """
        self.drowsiness_score = 0.0
        self.is_drowsy = False
        self.drowsiness_state = DrowsinessState.ALERT
        self.intermediate_decision = None
        self.drowsiness_result = None
        self.frame_counter = 0
        logger.info("StudentDrowsinessDecisionEngine state counters reset.")
