"""
Student Drowsiness Detection System - Dashboard Mock Telemetry Provider

This module provides simulated telemetry payloads for the Streamlit dashboard
foundation, ensuring zero dependency on active webcam or backend logic during UI testing.
"""

import time
import random
from typing import Dict, Any, List


class MockTelemetryProvider:
    """
    Simulates real-time telemetry dictionary updates for dashboard rendering.
    """

    def __init__(self) -> None:
        self.start_time: float = time.time()
        self.blink_count: int = 142
        self.yawn_count: int = 2
        self.session_events: List[Dict[str, Any]] = [
            {
                "time": "09:24:00",
                "type": "SYSTEM",
                "icon": "🚀",
                "message": "Session monitoring initialized.",
                "details": "Camera ID: 0 (1280x720 @ 30.0 FPS)"
            },
            {
                "time": "09:24:12",
                "type": "TELEMETRY",
                "icon": "👁️",
                "message": "Eye blink detected (#142).",
                "details": "Avg EAR: 0.19 | Duration: 0.18s"
            },
            {
                "time": "09:24:18",
                "type": "TELEMETRY",
                "icon": "👄",
                "message": "Yawn event completed (#2).",
                "details": "MAR: 0.62 | Duration: 2.10s"
            },
            {
                "time": "09:24:25",
                "type": "ALERT",
                "icon": "🚨",
                "message": "Strong drowsiness alarm triggered!",
                "details": "Score: 68/100 | State: DROWSY | Channels: HUD+Audio"
            },
            {
                "time": "09:24:35",
                "type": "RECOVERY",
                "icon": "🛡️",
                "message": "Alert state cleared. Return to ALERT.",
                "details": "Score: 12/100 | Duration: 10.0s"
            }
        ]

    def get_telemetry(self) -> Dict[str, Any]:
        """
        Returns a complete mock telemetry payload matching system schema.
        """
        elapsed = int(time.time() - self.start_time)
        hours = elapsed // 3600
        minutes = (elapsed % 3600) // 60
        seconds = elapsed % 60
        timer_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        # Dynamic slight jitter for realism
        avg_ear = round(0.285 + random.uniform(-0.015, 0.015), 3)
        mar = round(0.180 + random.uniform(-0.010, 0.020), 3)
        pitch = round(2.1 + random.uniform(-0.5, 0.5), 1)
        yaw = round(-1.4 + random.uniform(-0.4, 0.4), 1)
        roll = round(0.8 + random.uniform(-0.3, 0.3), 1)
        drowsiness_score = 12.0

        return {
            "session_time_str": timer_str,
            "fps": 30.0,
            "drowsiness_state": "ALERT",
            "left_ear": round(avg_ear - 0.005, 3),
            "right_ear": round(avg_ear + 0.005, 3),
            "avg_ear": avg_ear,
            "ear_threshold": 0.21,
            "eye_state": "OPEN (NORMAL)",
            "blink_count": self.blink_count,
            "eye_closed_duration": 0.0,
            "mar": mar,
            "mar_threshold": 0.55,
            "mouth_state": "CLOSED",
            "yawn_count": self.yawn_count,
            "mouth_open_duration": 0.0,
            "head_pose_pitch": pitch,
            "head_pose_yaw": yaw,
            "head_pose_roll": roll,
            "head_pose_valid": True,
            "drowsiness_score": drowsiness_score,
            "decision_confidence": 98.0,
            "co_occurrences": {
                "EYE": False,
                "MOUTH": False,
                "POSE": False
            },
            "decision_reason": "Student alert. All telemetry metrics (EAR: 0.285, MAR: 0.180, Pose: 2.1°) within nominal bounds.",
            "current_message": "System operating normally. No active warnings.",
            "current_severity": "subtle",
            "last_alert_time": "09:24:14",
            "previous_message": "Brief EAR dip detected (0.20s).",
            "audio_enabled": True,
            "audio_status": "READY",
            "session_stats": {
                "total_session_time": timer_str,
                "blink_count": self.blink_count,
                "yawn_count": self.yawn_count,
                "average_ear": 0.285,
                "average_mar": 0.180,
                "highest_score": 12.0,
                "longest_eye_closure": 0.0,
                "time_in_alert": "01:20:00 (95.2%)",
                "time_in_drowsy": "00:04:15 (4.8%)"
            },
            "events": self.session_events
        }
