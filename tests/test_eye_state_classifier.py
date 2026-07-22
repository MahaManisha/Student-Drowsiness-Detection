"""
Unit test suite for Phase 5.3: Eye State Classification using Average EAR.

Validates that:
1. Average EAR >= Threshold classifies as OPEN.
2. Average EAR < Threshold classifies as CLOSED.
3. Invalid Average EAR values (None, non-numeric, physiologically out-of-bounds) are handled safely and classified as UNKNOWN.
4. Custom threshold overrides work correctly.
5. Returns a structured EyeStateResult object.
"""

import pytest
from detection.eye_state_classifier import EyeStateClassifier, EyeState, EyeStateResult


def test_classify_average_ear_open():
    """Test that average EAR values greater than or equal to the threshold are classified as OPEN."""
    classifier = EyeStateClassifier(ear_threshold=0.25)
    
    # Borderline case: exact threshold
    result = classifier.classify_average_ear(0.25)
    assert isinstance(result, EyeStateResult)
    assert result.state == EyeState.OPEN
    assert result.ear_value == 0.25
    assert result.threshold == 0.25
    
    # Clearly open state
    result = classifier.classify_average_ear(0.38)
    assert result.state == EyeState.OPEN
    assert result.ear_value == 0.38


def test_classify_average_ear_closed():
    """Test that average EAR values below the threshold are classified as CLOSED."""
    classifier = EyeStateClassifier(ear_threshold=0.25)
    
    # Borderline case: just below threshold
    result = classifier.classify_average_ear(0.249)
    assert isinstance(result, EyeStateResult)
    assert result.state == EyeState.CLOSED
    assert result.ear_value == 0.249
    
    # Clearly closed state
    result = classifier.classify_average_ear(0.12)
    assert result.state == EyeState.CLOSED
    assert result.ear_value == 0.12


def test_classify_average_ear_invalid_none():
    """Test that None values are handled safely and classified as UNKNOWN."""
    classifier = EyeStateClassifier(ear_threshold=0.25)
    
    result = classifier.classify_average_ear(None)
    assert isinstance(result, EyeStateResult)
    assert result.state == EyeState.UNKNOWN
    assert result.ear_value is None
    assert result.threshold == 0.25


def test_classify_average_ear_invalid_type():
    """Test that non-numeric types are handled safely and classified as UNKNOWN."""
    classifier = EyeStateClassifier(ear_threshold=0.25)
    
    # String input that cannot be parsed
    result = classifier.classify_average_ear("invalid_ear")
    assert isinstance(result, EyeStateResult)
    assert result.state == EyeState.UNKNOWN
    assert result.ear_value is None
    
    # Parseable string input
    result = classifier.classify_average_ear("0.35")
    assert result.state == EyeState.OPEN
    assert result.ear_value == 0.35


def test_classify_average_ear_out_of_bounds():
    """Test that physiologically out-of-bounds values are handled safely and classified as UNKNOWN."""
    classifier = EyeStateClassifier(ear_threshold=0.25)
    
    # Negative EAR
    result = classifier.classify_average_ear(-0.1)
    assert isinstance(result, EyeStateResult)
    assert result.state == EyeState.UNKNOWN
    assert result.ear_value == -0.1
    
    # Unreasonably high EAR (> 1.0)
    result = classifier.classify_average_ear(1.5)
    assert isinstance(result, EyeStateResult)
    assert result.state == EyeState.UNKNOWN
    assert result.ear_value == 1.5


def test_classify_average_ear_custom_threshold():
    """Test that dynamic threshold overrides are respected."""
    classifier = EyeStateClassifier(ear_threshold=0.25)
    
    # Standard threshold 0.25, input 0.22 -> CLOSED
    result = classifier.classify_average_ear(0.22)
    assert result.state == EyeState.CLOSED
    
    # Custom threshold override of 0.20, input 0.22 -> OPEN
    result = classifier.classify_average_ear(0.22, threshold=0.20)
    assert result.state == EyeState.OPEN
    assert result.threshold == 0.20
    assert result.ear_value == 0.22
