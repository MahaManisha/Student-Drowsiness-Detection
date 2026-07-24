"""
Student Drowsiness Detection System - Phase 12.7 System Validation Suite

This module performs comprehensive QA validation across all 7 operational scenarios:
1. Normal studying -> Expected: No alerts
2. Slightly Drowsy -> Expected: HUD warning only
3. Drowsy -> Expected: Warning and logging
4. Highly Drowsy -> Expected: Alarm + HUD + logging
5. Face loss -> Expected: No false alerts
6. Face recovery -> Expected: Resume normally
7. Session end -> Expected: Statistics and report generated
"""

import os
import sys
import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Adjust path for root imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from main import StudentDrowsinessApp
from detection import DrowsinessState, DrowsinessResult

# Safe import for SessionLogger to bypass standard library naming collision
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logging")))
try:
    from session_logger import SessionLogger
finally:
    if sys.path[0] == os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logging")):
        sys.path.pop(0)

from analytics.session_statistics import SessionStatisticsTracker
from alerts.alert_manager import AlertManager, HUDAlertChannel, AudioAlertChannel
from reports.report_generator import ReportGenerator


class TestPhase127Validation(unittest.TestCase):
    """
    QA System Validation Suite covering all 7 required operational scenarios for Phase 12.7.
    """

    def setUp(self) -> None:
        """Set up temporary test directories and mock instances."""
        self.test_output_dir = Path(__file__).parent / "tmp_qa_validation_output"
        self.test_output_dir.mkdir(parents=True, exist_ok=True)
        self.test_log_path = self.test_output_dir / "qa_session_log.json"

        # Patch config paths to use temp directory
        self.config_log_patcher = patch.object(config, "SESSION_LOG_CSV", str(self.test_log_path.with_suffix(".csv")))
        self.config_reports_patcher = patch.object(config, "REPORTS_DIR", self.test_output_dir)
        self.camera_patcher = patch("main.CameraStream")
        self.detector_patcher = patch("main.FaceMeshDetector")

        self.config_log_patcher.start()
        self.config_reports_patcher.start()
        self.mock_camera_cls = self.camera_patcher.start()
        self.mock_detector_cls = self.detector_patcher.start()

        # Set valid camera parameters
        mock_camera_inst = self.mock_camera_cls.return_value
        mock_camera_inst.fps_target = 30.0

    def tearDown(self) -> None:
        """Clean up temporary test artifacts."""
        self.config_log_patcher.stop()
        self.config_reports_patcher.stop()
        self.camera_patcher.stop()
        self.detector_patcher.stop()

        if self.test_output_dir.exists():
            for item in self.test_output_dir.glob("*"):
                try:
                    item.unlink()
                except Exception:
                    pass
            try:
                self.test_output_dir.rmdir()
            except Exception:
                pass

    def test_scenario_1_normal_studying(self) -> None:
        """
        Scenario 1: Normal studying
        Expected: No alerts (ALERT state, clean baseline)
        """
        app = StudentDrowsinessApp()
        app.session_logger = SessionLogger(log_path=str(self.test_log_path))

        # Normal studying parameters: open eyes, normal posture, 0 yawns
        eye_data = {"blink_count": 1, "consecutive_closed_frames": 0, "closed_duration_seconds": 0.0}
        yawn_data = {"yawn_count": 0, "consecutive_open_frames": 0, "yawn_duration_seconds": 0.0}
        pose_data = {"yaw": 0.0, "pitch": 0.0, "roll": 0.0, "valid": True}

        metrics = app.decision_engine.update(eye_data, yawn_data, pose_data)
        drowsiness_result = app.decision_engine.drowsiness_result

        if drowsiness_result:
            app.alert_manager.process_result(drowsiness_result)

        # Verification: ALERT state, score < 30, no active HUD warnings or audio
        self.assertEqual(metrics["drowsiness_state"], "ALERT")
        self.assertLess(metrics["drowsiness_score"], 30.0)
        self.assertIsNone(app.hud_channel.current_message)
        self.assertIsNone(app.hud_channel.current_severity)
        self.assertIsNone(app.audio_channel.play_thread)

    def test_scenario_2_slightly_drowsy(self) -> None:
        """
        Scenario 2: Slightly Drowsy
        Expected: HUD warning only (subtle warning overlay, no audio alarm)
        """
        app = StudentDrowsinessApp()
        app.session_logger = SessionLogger(log_path=str(self.test_log_path))

        # Slightly drowsy parameters: score between 30.0 and 49.9
        # eye_pts = (1.2 / 3.0) * 50 = 20.0, blink_pts = 15.0 -> total score = 35.0 (SLIGHTLY_DROWSY)
        eye_data = {"blink_count": 3, "consecutive_closed_frames": 36, "closed_duration_seconds": 1.2}
        yawn_data = {"yawn_count": 0, "consecutive_open_frames": 0, "yawn_duration_seconds": 0.0}
        pose_data = {"yaw": 5.0, "pitch": 8.0, "roll": 0.0, "valid": True}

        metrics = app.decision_engine.update(eye_data, yawn_data, pose_data)
        drowsiness_result = app.decision_engine.drowsiness_result

        self.assertIsNotNone(drowsiness_result)
        app.alert_manager.process_result(drowsiness_result)

        # Verification: SLIGHTLY_DROWSY state, HUD subtle warning present, Audio thread is None
        self.assertEqual(drowsiness_result.state, DrowsinessState.SLIGHTLY_DROWSY)
        self.assertEqual(app.hud_channel.current_severity, "subtle")
        self.assertIsNotNone(app.hud_channel.current_message)
        self.assertIn("subtle warning", app.hud_channel.current_message.lower())
        self.assertIsNone(app.audio_channel.play_thread)

    def test_scenario_3_drowsy(self) -> None:
        """
        Scenario 3: Drowsy
        Expected: Warning and logging (strong HUD warning, recorded in structured session log, no audio alarm)
        """
        app = StudentDrowsinessApp()
        app.session_logger = SessionLogger(log_path=str(self.test_log_path))

        # Drowsy parameters: score between 50.0 and 79.9
        # eye_pts = (2.2 / 3.0) * 50 = 36.6, blink_pts = 15.0, yawn_pts = 10.0 -> total score = 61.6 (DROWSY)
        eye_data = {"blink_count": 5, "consecutive_closed_frames": 66, "closed_duration_seconds": 2.2}
        yawn_data = {"yawn_count": 1, "consecutive_open_frames": 0, "yawn_duration_seconds": 0.0}
        pose_data = {"yaw": 8.0, "pitch": 8.0, "roll": 2.0, "valid": True}

        metrics = app.decision_engine.update(eye_data, yawn_data, pose_data)
        drowsiness_result = app.decision_engine.drowsiness_result

        self.assertIsNotNone(drowsiness_result)
        app.alert_manager.process_result(drowsiness_result)

        # Log transition in session logger
        score_val = metrics.get("drowsiness_score", 0.0)
        state_raw = metrics.get("drowsiness_state", "ALERT")
        app.session_logger.update(state_raw, score_val, 90.0)

        # Verification: DROWSY state, HUD strong warning present, event logged in JSON file, Audio thread is None
        self.assertEqual(drowsiness_result.state, DrowsinessState.DROWSY)
        self.assertEqual(app.hud_channel.current_severity, "strong")
        self.assertIsNotNone(app.hud_channel.current_message)
        self.assertIn("strong warning", app.hud_channel.current_message.lower())
        self.assertIsNone(app.audio_channel.play_thread)

        # Check JSON log file
        self.assertTrue(self.test_log_path.exists())
        with open(self.test_log_path, "r", encoding="utf-8") as f:
            lines = [json.loads(line) for line in f if line.strip()]
        self.assertGreater(len(lines), 0)

    def test_scenario_4_highly_drowsy(self) -> None:
        """
        Scenario 4: Highly Drowsy
        Expected: Alarm + HUD + logging (critical HUD warning, audio alarm thread launched, logged in session log)
        """
        app = StudentDrowsinessApp()
        app.session_logger = SessionLogger(log_path=str(self.test_log_path))

        # Patch playsound and file exists for audio alarm validation
        with patch("os.path.exists", return_value=True), patch("config.ALARM_SOUND_PATH", "dummy_alarm.wav"):
            # Highly drowsy parameters: score >= 80.0
            # eye_pts = 50.0, blink_pts = 15.0, yawn_pts = 20.0 -> total score = 85.0 (HIGHLY_DROWSY)
            eye_data = {"blink_count": 8, "consecutive_closed_frames": 100, "closed_duration_seconds": 3.33}
            yawn_data = {"yawn_count": 2, "consecutive_open_frames": 0, "yawn_duration_seconds": 0.0}
            pose_data = {"yaw": 12.0, "pitch": 25.0, "roll": 5.0, "valid": True}

            metrics = app.decision_engine.update(eye_data, yawn_data, pose_data)
            drowsiness_result = app.decision_engine.drowsiness_result

            self.assertIsNotNone(drowsiness_result)
            app.alert_manager.process_result(drowsiness_result)

            score_val = metrics.get("drowsiness_score", 0.0)
            state_raw = metrics.get("drowsiness_state", "ALERT")
            app.session_logger.update(state_raw, score_val, 95.0)

            # Verification: HIGHLY_DROWSY state, critical HUD, audio thread launched, JSON event logged
            self.assertEqual(drowsiness_result.state, DrowsinessState.HIGHLY_DROWSY)
            self.assertEqual(app.hud_channel.current_severity, "critical")
            self.assertIsNotNone(app.hud_channel.current_message)
            self.assertIn("critical warning", app.hud_channel.current_message.lower())
            self.assertIsNotNone(app.audio_channel.play_thread)

            # Join thread to clean up
            if app.audio_channel.play_thread:
                app.audio_channel.play_thread.join(timeout=1.0)

            self.assertTrue(self.test_log_path.exists())

    def test_scenario_5_face_loss(self) -> None:
        """
        Scenario 5: Face loss
        Expected: No false alerts (smooth handling when face detection returns False)
        """
        app = StudentDrowsinessApp()
        app.session_logger = SessionLogger(log_path=str(self.test_log_path))

        # Simulate face loss input payload (has_face=False, no landmarks)
        eye_data = {"blink_count": 2, "consecutive_closed_frames": 0, "closed_duration_seconds": 0.0}
        yawn_data = {"yawn_count": 0, "consecutive_open_frames": 0, "yawn_duration_seconds": 0.0}
        pose_data = {"yaw": 0.0, "pitch": 0.0, "roll": 0.0, "valid": False}  # Pose invalid during face loss

        metrics = app.decision_engine.update(eye_data, yawn_data, pose_data)
        drowsiness_result = app.decision_engine.drowsiness_result

        if drowsiness_result:
            app.alert_manager.process_result(drowsiness_result)

        # Verification: ALERT state maintained, score remains 0, no false alerts triggered
        self.assertEqual(metrics["drowsiness_state"], "ALERT")
        self.assertEqual(metrics["drowsiness_score"], 0.0)
        self.assertIsNone(app.hud_channel.current_message)

    def test_scenario_6_face_recovery(self) -> None:
        """
        Scenario 6: Face recovery
        Expected: Resume normally after face re-detection
        """
        app = StudentDrowsinessApp()
        app.session_logger = SessionLogger(log_path=str(self.test_log_path))

        # Step 1: Face loss frame
        pose_data_invalid = {"yaw": 0.0, "pitch": 0.0, "roll": 0.0, "valid": False}
        app.decision_engine.update(
            {"blink_count": 2, "consecutive_closed_frames": 0, "closed_duration_seconds": 0.0},
            {"yawn_count": 0, "consecutive_open_frames": 0, "yawn_duration_seconds": 0.0},
            pose_data_invalid
        )

        # Step 2: Face re-detected (Face Recovery)
        pose_data_valid = {"yaw": 2.0, "pitch": 3.0, "roll": 1.0, "valid": True}
        metrics_recovered = app.decision_engine.update(
            {"blink_count": 3, "consecutive_closed_frames": 0, "closed_duration_seconds": 0.0},
            {"yawn_count": 0, "consecutive_open_frames": 0, "yawn_duration_seconds": 0.0},
            pose_data_valid
        )
        drowsiness_result = app.decision_engine.drowsiness_result

        if drowsiness_result:
            app.alert_manager.process_result(drowsiness_result)

        # Verification: Successfully recovers, computes valid decision metrics, state remains normal ALERT
        self.assertEqual(metrics_recovered["drowsiness_state"], "ALERT")
        self.assertTrue(metrics_recovered["valid"])

    def test_scenario_7_session_end(self) -> None:
        """
        Scenario 7: Session end
        Expected: Statistics and summary report generated cleanly on app.stop()
        """
        app = StudentDrowsinessApp()
        app.session_logger = SessionLogger(log_path=str(self.test_log_path))
        app.stats_tracker = SessionStatisticsTracker()

        # Update mock frames
        app.stats_tracker.update("ALERT", 10.0, 0.32, 0.18, 5, 0, 0.0)
        app.stats_tracker.update("DROWSY", 75.0, 0.18, 0.62, 5, 1, 2.0)
        app.session_logger.update("ALERT", 10.0, 100.0)
        app.session_logger.update("DROWSY", 75.0, 90.0)

        # Mock hardware stop methods
        app.camera.stop = MagicMock()
        app.detector.close = MagicMock()

        # Run graceful shutdown
        app.stop()

        # Verification: session_statistics.json and session_summary_report.md created in REPORTS_DIR
        stats_file = self.test_output_dir / "session_statistics.json"
        report_file = self.test_output_dir / "session_summary_report.md"

        self.assertTrue(stats_file.exists(), "Expected session_statistics.json to exist after shutdown.")
        self.assertTrue(report_file.exists(), "Expected session_summary_report.md to exist after shutdown.")

        with open(stats_file, "r", encoding="utf-8") as f:
            stats = json.load(f)
        self.assertIn("total_session_time", stats)
        self.assertIn("highest_score", stats)

        with open(report_file, "r", encoding="utf-8") as f:
            report_text = f.read()
        self.assertIn("Student Drowsiness Monitoring: Session Summary Report", report_text)


if __name__ == "__main__":
    unittest.main()
