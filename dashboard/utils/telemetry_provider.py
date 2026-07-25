"""
Student Drowsiness Detection System - Telemetry Provider Utility

Bridges real-time AI telemetry dictionary outputs to Streamlit UI components.
Provides safe formatting and fallback 'N/A' handling to prevent dashboard crashes.
"""

from typing import Dict, Any, Optional


class TelemetryProvider:
    """
    Formats and validates telemetry dictionaries for Streamlit rendering.
    """

    @staticmethod
    def format_float(val: Optional[float], decimals: int = 3, fallback: str = "N/A") -> str:
        """Formats float values with specified decimal places or returns fallback string."""
        if val is None:
            return fallback
        try:
            return f"{float(val):.{decimals}f}"
        except (ValueError, TypeError):
            return fallback

    @staticmethod
    def format_int(val: Optional[int], fallback: str = "N/A") -> str:
        """Formats integer values or returns fallback string."""
        if val is None:
            return fallback
        try:
            return str(int(val))
        except (ValueError, TypeError):
            return fallback

    @staticmethod
    def format_timer(seconds: Optional[float], fallback: str = "0.0s") -> str:
        """Formats duration in seconds."""
        if seconds is None:
            return fallback
        try:
            return f"{float(seconds):.1f}s"
        except (ValueError, TypeError):
            return fallback

    @classmethod
    def process_payload(cls, raw_telemetry: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validates raw telemetry dictionary payload and populates safe default values.
        """
        if not raw_telemetry:
            raw_telemetry = {}

        return {
            "session_time_str": raw_telemetry.get("session_time_str", "00:00:00"),
            "fps": raw_telemetry.get("fps", 30.0),
            "drowsiness_state": raw_telemetry.get("drowsiness_state", "ALERT"),
            
            # Eye Telemetry
            "left_ear": cls.format_float(raw_telemetry.get("left_ear"), 3, "N/A"),
            "right_ear": cls.format_float(raw_telemetry.get("right_ear"), 3, "N/A"),
            "avg_ear": raw_telemetry.get("avg_ear", 0.285),
            "avg_ear_str": cls.format_float(raw_telemetry.get("avg_ear"), 3, "N/A"),
            "ear_threshold": raw_telemetry.get("ear_threshold", 0.21),
            "eye_state": raw_telemetry.get("eye_state", "OPEN (NORMAL)"),
            "blink_count": cls.format_int(raw_telemetry.get("blink_count"), "0"),
            "eye_closed_duration": raw_telemetry.get("eye_closed_duration", 0.0),
            "eye_closed_duration_str": cls.format_timer(raw_telemetry.get("eye_closed_duration"), "0.0s"),

            # Mouth Telemetry
            "mar": raw_telemetry.get("mar", 0.180),
            "mar_str": cls.format_float(raw_telemetry.get("mar"), 3, "N/A"),
            "mar_threshold": raw_telemetry.get("mar_threshold", 0.55),
            "mouth_state": raw_telemetry.get("mouth_state", "CLOSED"),
            "yawn_count": cls.format_int(raw_telemetry.get("yawn_count"), "0"),
            "mouth_open_duration": raw_telemetry.get("mouth_open_duration", 0.0),
            "mouth_open_duration_str": cls.format_timer(raw_telemetry.get("mouth_open_duration"), "0.0s"),

            # Head Pose Telemetry
            "head_pose_pitch": raw_telemetry.get("head_pose_pitch", 0.0),
            "head_pose_pitch_str": cls.format_float(raw_telemetry.get("head_pose_pitch"), 1, "N/A"),
            "head_pose_yaw": raw_telemetry.get("head_pose_yaw", 0.0),
            "head_pose_yaw_str": cls.format_float(raw_telemetry.get("head_pose_yaw"), 1, "N/A"),
            "head_pose_roll": raw_telemetry.get("head_pose_roll", 0.0),
            "head_pose_roll_str": cls.format_float(raw_telemetry.get("head_pose_roll"), 1, "N/A"),
            "head_pose_valid": raw_telemetry.get("head_pose_valid", False),

            # AI Decision Engine Telemetry
            "drowsiness_score": raw_telemetry.get("drowsiness_score", 0.0),
            "decision_confidence": raw_telemetry.get("decision_confidence", 98.0),
            "co_occurrences": raw_telemetry.get("co_occurrences", {"EYE": False, "MOUTH": False, "POSE": False}),
            "decision_reason": raw_telemetry.get("decision_reason", "Student alert. All telemetry metrics within nominal bounds."),

            # Alert Center Telemetry
            "current_message": raw_telemetry.get("current_message", "System operating normally."),
            "current_severity": raw_telemetry.get("current_severity", "subtle"),
            "last_alert_time": raw_telemetry.get("last_alert_time", "--:--:--"),
            "previous_message": raw_telemetry.get("previous_message", "No recent alerts."),
            "audio_enabled": raw_telemetry.get("audio_enabled", True),
            "audio_status": raw_telemetry.get("audio_status", "READY"),

            # Session Statistics & Timeline Telemetry
            "session_stats": raw_telemetry.get("session_stats", {}),
            "events": raw_telemetry.get("events", [])
        }
