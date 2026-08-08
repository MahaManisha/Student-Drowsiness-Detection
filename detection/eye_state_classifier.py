"""
Student Drowsiness Detection System - Eye State Classifier Module

This module provides the EyeStateClassifier class, which is responsible for evaluating
Eye Aspect Ratio (EAR) metric values for a single frame and classifying eye openness states
(OPEN, CLOSED, or UNKNOWN).

Follows SOLID design principles:
- Single Responsibility Principle (SRP): Focuses exclusively on evaluating single-frame EAR values
  and mapping them to discrete eye openness states.
- Open/Closed Principle (OCP): Configurable threshold values and classification rules allow behavior
  adjustments without modifying core classification code.
- Liskov Substitution Principle (LSP): Strict return types and predictable state Enum outputs across
  single-eye, dual-eye, and dictionary summary methods.
- Interface Segregation Principle (ISP): Exposes granular public methods (classify_eye, classify_both_eyes,
  classify_frame) so callers only invoke required interfaces.
- Dependency Inversion Principle (DIP): Operates independently of hardware, camera capture loops,
  and computer vision landmark extraction algorithms by consuming numeric EAR float values.

Note:
This module performs single-frame classification only (Phase 5.1).
It does NOT perform temporal frame counting, blink detection, or multi-frame drowsiness state evaluation.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Tuple, Union
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

# Default EAR threshold fallback if config is missing or invalid
DEFAULT_EAR_THRESHOLD: float = 0.21

# Realistic physiological EAR threshold bounds for human eyes
MIN_EAR_THRESHOLD_BOUND: float = 0.05
MAX_EAR_THRESHOLD_BOUND: float = 0.50


class EyeState(str, Enum):
    """
    Enum representing single-frame eye openness classification states.
    """
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    UNKNOWN = "UNKNOWN"


@dataclass
class EyeStateResult:
    """
    Structured object representing the single-frame classification output of the average EAR.
    """
    state: EyeState
    ear_value: Optional[float]
    threshold: float


class EyeStateClassifier:
    """
    Independent classifier for evaluating single-frame Eye Aspect Ratio (EAR) metrics
    and mapping them to discrete EyeState categories (OPEN, CLOSED, UNKNOWN).

    Attributes:
        ear_threshold (float): EAR value below which an eye is classified as CLOSED.
    """

    def __init__(self, ear_threshold: Optional[float] = None) -> None:
        """
        Initializes the EyeStateClassifier by loading and validating the EAR threshold
        from the central configuration system (config.py) or constructor parameter.

        Args:
            ear_threshold (Optional[float]): Optional threshold override. If None, reads config.EAR_THRESHOLD.
        """
        self.ear_threshold: float = DEFAULT_EAR_THRESHOLD
        self._load_and_validate_threshold(ear_threshold)

    def validate_threshold(self, threshold: Any) -> bool:
        """
        Validates whether a candidate EAR threshold value is numeric and within realistic bounds [0.05, 0.50].

        Args:
            threshold (Any): Threshold candidate value to validate.

        Returns:
            bool: True if threshold is valid and within range, False otherwise.
        """
        if threshold is None:
            return False

        try:
            val = float(threshold)
            if MIN_EAR_THRESHOLD_BOUND <= val <= MAX_EAR_THRESHOLD_BOUND:
                return True
            else:
                logger.warning(
                    f"EAR threshold candidate '{val:.3f}' is outside valid range "
                    f"[{MIN_EAR_THRESHOLD_BOUND:.2f}, {MAX_EAR_THRESHOLD_BOUND:.2f}]."
                )
                return False

        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid threshold type/value '{threshold}': {e}")
            return False

    def _load_and_validate_threshold(self, ear_threshold: Optional[float] = None) -> None:
        """
        Internal helper to load, validate, and bind the EAR threshold from parameters, config, or fallback defaults.

        Args:
            ear_threshold (Optional[float]): Explicit threshold candidate parameter.
        """
        # Priority 1: Explicit parameter
        if ear_threshold is not None:
            if self.validate_threshold(ear_threshold):
                self.ear_threshold = float(ear_threshold)
                logger.info(
                    f"EyeStateClassifier configured with custom threshold: {self.ear_threshold:.3f}"
                )
                return
            else:
                logger.warning(
                    f"Explicit threshold '{ear_threshold}' failed validation. Attempting to load from config..."
                )

        # Priority 2: Central config system
        config_val = getattr(config, "EAR_THRESHOLD", None)
        if self.validate_threshold(config_val):
            self.ear_threshold = float(config_val)
            logger.info(
                f"EyeStateClassifier loaded threshold from config.EAR_THRESHOLD: {self.ear_threshold:.3f}"
            )
        else:
            # Priority 3: Fallback default
            self.ear_threshold = DEFAULT_EAR_THRESHOLD
            logger.warning(
                f"Config threshold invalid/missing. Falling back to default threshold: {self.ear_threshold:.3f}"
            )

    def get_threshold(self) -> float:
        """
        Retrieves the currently configured EAR threshold.

        Returns:
            float: Current active EAR threshold value.
        """
        return self.ear_threshold

    def set_threshold(self, new_threshold: float) -> bool:
        """
        Updates the active EAR threshold dynamically after validating the new value.

        Args:
            new_threshold (float): New threshold value to set.

        Returns:
            bool: True if set successfully, False if validation failed.
        """
        if self.validate_threshold(new_threshold):
            old_val = self.ear_threshold
            self.ear_threshold = float(new_threshold)
            logger.info(
                f"EAR threshold dynamically updated: {old_val:.3f} -> {self.ear_threshold:.3f}"
            )
            return True
        else:
            logger.error(
                f"Failed to set EAR threshold: value '{new_threshold}' is invalid."
            )
            return False

    def reload_threshold_from_config(self) -> float:
        """
        Reloads and re-validates the EAR threshold from the central config system.

        Returns:
            float: Updated active EAR threshold value.
        """
        logger.info("Reloading EAR threshold from config module...")
        self._load_and_validate_threshold(None)
        return self.ear_threshold


    def classify_eye(
        self,
        ear_value: Optional[float],
        threshold: Optional[float] = None,
    ) -> EyeState:
        """
        Classifies a single eye's state (OPEN, CLOSED, or UNKNOWN) based on its EAR value.

        Classification Rule:
            - If ear_value is None or invalid: EyeState.UNKNOWN
            - If ear_value < threshold: EyeState.CLOSED
            - If ear_value >= threshold: EyeState.OPEN

        Args:
            ear_value (Optional[float]): Eye Aspect Ratio value to evaluate.
            threshold (Optional[float]): Optional threshold override. Defaults to self.ear_threshold.

        Returns:
            EyeState: Categorized eye state (EyeState.OPEN, EyeState.CLOSED, or EyeState.UNKNOWN).
        """
        if ear_value is None:
            logger.debug("EAR value is None. Classifying as EyeState.UNKNOWN.")
            return EyeState.UNKNOWN

        eval_threshold = threshold if threshold is not None else self.ear_threshold

        try:
            ear_float = float(ear_value)
            if ear_float < eval_threshold:
                return EyeState.CLOSED
            else:
                return EyeState.OPEN

        except (ValueError, TypeError) as e:
            logger.warning(f"Error casting EAR value '{ear_value}' to float: {e}")
            return EyeState.UNKNOWN

    def classify_both_eyes(
        self,
        right_ear: Optional[float],
        left_ear: Optional[float],
        threshold: Optional[float] = None,
    ) -> Tuple[EyeState, EyeState, EyeState]:
        """
        Classifies right eye, left eye, and overall dual-eye state independently for a single frame.

        Overall State Determination:
            - If both eyes are CLOSED: EyeState.CLOSED
            - If both eyes are OPEN: EyeState.OPEN
            - If one eye is CLOSED and one eye is OPEN: EyeState.CLOSED (conservative eye-closure flag)
            - If both eyes are UNKNOWN: EyeState.UNKNOWN
            - If one eye is UNKNOWN: returns the known eye's state

        Args:
            right_ear (Optional[float]): EAR value for the right eye.
            left_ear (Optional[float]): EAR value for the left eye.
            threshold (Optional[float]): Optional threshold override.

        Returns:
            Tuple[EyeState, EyeState, EyeState]: (right_state, left_state, overall_state)
        """
        eval_threshold = threshold if threshold is not None else self.ear_threshold
        right_state = self.classify_eye(right_ear, eval_threshold)
        left_state = self.classify_eye(left_ear, eval_threshold)

        if right_ear is not None and left_ear is not None:
            avg_ear = (right_ear + left_ear) / 2.0
        else:
            avg_ear = right_ear if right_ear is not None else left_ear

        if avg_ear is not None:
            overall_state = EyeState.CLOSED if avg_ear < eval_threshold else EyeState.OPEN
        elif right_state == EyeState.CLOSED and left_state == EyeState.CLOSED:
            overall_state = EyeState.CLOSED
        elif right_state == EyeState.OPEN or left_state == EyeState.OPEN:
            overall_state = EyeState.OPEN
        else:
            overall_state = EyeState.UNKNOWN

        logger.debug(
            f"Classified dual eyes -> Right: {right_state.value}, Left: {left_state.value}, Overall: {overall_state.value}"
        )
        return right_state, left_state, overall_state

    def classify_frame(
        self,
        right_ear: Optional[float],
        left_ear: Optional[float],
        avg_ear: Optional[float] = None,
        threshold: Optional[float] = None,
    ) -> Dict[str, Union[str, bool, float, Optional[float]]]:
        """
        Generates a comprehensive single-frame classification summary dictionary.

        Args:
            right_ear (Optional[float]): EAR value for the right eye.
            left_ear (Optional[float]): EAR value for the left eye.
            avg_ear (Optional[float]): Optional average EAR value. If None, calculated automatically.
            threshold (Optional[float]): Optional threshold override.

        Returns:
            Dict[str, Union[str, bool, float, Optional[float]]]: Structured summary dictionary:
                - "right_state": str ("OPEN", "CLOSED", "UNKNOWN")
                - "left_state": str ("OPEN", "CLOSED", "UNKNOWN")
                - "overall_state": str ("OPEN", "CLOSED", "UNKNOWN")
                - "is_closed": bool
                - "threshold_used": float
                - "avg_ear": Optional[float]
        """
        eval_threshold = threshold if threshold is not None else self.ear_threshold
        right_state, left_state, overall_state = self.classify_both_eyes(
            right_ear, left_ear, eval_threshold
        )

        if avg_ear is None:
            if right_ear is not None and left_ear is not None:
                avg_ear = (right_ear + left_ear) / 2.0
            elif right_ear is not None:
                avg_ear = right_ear
            elif left_ear is not None:
                avg_ear = left_ear

        is_closed = (overall_state == EyeState.CLOSED)

        return {
            "right_state": right_state.value,
            "left_state": left_state.value,
            "overall_state": overall_state.value,
            "is_closed": is_closed,
            "threshold_used": eval_threshold,
            "avg_ear": avg_ear,
        }

    def classify_average_ear(
        self,
        avg_ear: Optional[float],
        threshold: Optional[float] = None,
    ) -> EyeStateResult:
        """
        Classifies the single-frame overall eye state (OPEN, CLOSED, or UNKNOWN)
        using the Average EAR calculated by the EAR module.

        Classification Rule:
            - If avg_ear is None or invalid: EyeState.UNKNOWN
            - If avg_ear >= threshold: EyeState.OPEN
            - If avg_ear < threshold: EyeState.CLOSED

        Args:
            avg_ear (Optional[float]): Average Eye Aspect Ratio value to evaluate.
            threshold (Optional[float]): Optional threshold override. Defaults to self.ear_threshold.

        Returns:
            EyeStateResult: Structured result object containing the eye state, EAR value, and threshold used.
        """
        eval_threshold = threshold if threshold is not None else self.ear_threshold
        logger.debug(f"Classifying average EAR: {avg_ear} with threshold: {eval_threshold}")

        if avg_ear is None:
            logger.warning("Average EAR value is None. Classifying overall state as UNKNOWN.")
            return EyeStateResult(state=EyeState.UNKNOWN, ear_value=None, threshold=eval_threshold)

        try:
            ear_float = float(avg_ear)
            # Safe physiological bound checks (valid EAR is generally 0.0 to 1.0)
            if not (0.0 <= ear_float <= 1.0):
                logger.warning(f"Physiologically abnormal average EAR value: {ear_float:.4f}. Classifying state as UNKNOWN.")
                return EyeStateResult(state=EyeState.UNKNOWN, ear_value=ear_float, threshold=eval_threshold)

            if ear_float >= eval_threshold:
                state = EyeState.OPEN
            else:
                state = EyeState.CLOSED

            logger.debug(f"Average EAR classification result: {state.value} (EAR: {ear_float:.4f}, Threshold: {eval_threshold:.3f})")
            return EyeStateResult(state=state, ear_value=ear_float, threshold=eval_threshold)

        except (ValueError, TypeError) as e:
            logger.warning(f"Error casting average EAR value '{avg_ear}' to float: {e}")
            return EyeStateResult(state=EyeState.UNKNOWN, ear_value=None, threshold=eval_threshold)
