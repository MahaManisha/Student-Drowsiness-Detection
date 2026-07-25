"""
Student Drowsiness Detection System - Dashboard Telemetry Formatters Utility

Provides type-safe formatting helper functions for numeric telemetry values,
guaranteeing zero TypeError: unsupported format string passed to NoneType.__format__ exceptions.
Does NOT modify any backend AI detection algorithms or math calculators.
"""

from typing import Any, Optional


def safe_float(val: Any, precision: int = 3, default: str = "N/A") -> str:
    """
    Safely formats a float value. Returns default string if val is None or non-numeric.
    """
    if val is None:
        return default
    try:
        f_val = float(val)
        return f"{f_val:.{precision}f}"
    except (ValueError, TypeError):
        return default


def safe_int(val: Any, default: str = "0") -> str:
    """
    Safely formats an integer value. Returns default string if val is None or non-numeric.
    """
    if val is None:
        return default
    try:
        i_val = int(val)
        return f"{i_val:,}"
    except (ValueError, TypeError):
        return default


def safe_percentage(val: Any, precision: int = 0, default: str = "0%") -> str:
    """
    Safely formats a percentage value. Returns default string if val is None.
    """
    if val is None:
        return default
    try:
        f_val = float(val)
        return f"{f_val:.{precision}f}%"
    except (ValueError, TypeError):
        return default


def safe_duration(val: Any, precision: int = 1, default: str = "0.0s") -> str:
    """
    Safely formats a duration in seconds. Returns default string if val is None.
    """
    if val is None:
        return default
    try:
        f_val = float(val)
        return f"{f_val:.{precision}f}s"
    except (ValueError, TypeError):
        return default


def safe_angle(val: Any, precision: int = 1, default: str = "0.0°") -> str:
    """
    Safely formats an angle degree with sign (+/-). Returns default string if val is None.
    """
    if val is None:
        return default
    try:
        f_val = float(val)
        return f"{f_val:+.{precision}f}°"
    except (ValueError, TypeError):
        return default
