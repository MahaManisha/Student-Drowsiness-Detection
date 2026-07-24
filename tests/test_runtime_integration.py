"""
Student Drowsiness Detection System - Phase 12.6 Runtime Integration Tests

This test module verifies the complete integration of AlertManager, SessionLogger,
SessionStatisticsTracker, and ReportGenerator in main.py.
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
from detection import DrowsinessState

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


class TestRuntimeIntegration(unittest.TestCase):
    """
    Integration test suite verifying the multi-module runtime execution in main.py.
    """

    def setUp(self) -> None:
        """Set up temporary test directories and mock instances."""
        self.test_output_dir = Path(__file__).parent / "tmp_test_output"
        self.test_output_dir.mkdir(parents=True, exist_ok=True)
        self.test_log_path = self.test_output_dir / "test_session_log.json"
        self.test_stats_path = self.test_output_dir / "test_session_stats.json"
        self.test_report_path = self.test_output_dir / "test_session_report.md"

        # Patch config paths to use temp directory
        self.config_log_patcher = patch.object(config, "SESSION_LOG_CSV", str(self.test_log_path.with_suffix(".csv")))
        self.config_reports_patcher = patch.object(config, "REPORTS_DIR", self.test_output_dir)
        self.camera_patcher = patch("main.CameraStream")
        self.detector_patcher = patch("main.FaceMeshDetector")

        self.config_log_patcher.start()
        self.config_reports_patcher.start()
        self.mock_camera_cls = self.camera_patcher.start()
        self.mock_detector_cls = self.detector_patcher.start()

        # Ensure mocked camera instance has valid numeric fps_target
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

    def test_app_initialization(self) -> None:
        """Verifies that StudentDrowsinessApp initializes all components cleanly."""
        app = StudentDrowsinessApp()

        self.assertIsNotNone(app.camera)
        self.assertIsNotNone(app.detector)
        self.assertIsNotNone(app.eye_extractor)
        self.assertIsNotNone(app.mouth_extractor)
        self.assertIsNotNone(app.ear_calculator)
        self.assertIsNotNone(app.mar_calculator)
        self.assertIsNotNone(app.yawn_detector)
        self.assertIsNotNone(app.head_pose_estimator)
        self.assertIsNotNone(app.classifier)
        self.assertIsNotNone(app.temporal_analyzer)
        self.assertIsNotNone(app.decision_engine)
        self.assertIsNotNone(app.alert_manager)
        self.assertIsNotNone(app.visualizer)
        self.assertIsNotNone(app.session_logger)
        self.assertIsNotNone(app.stats_tracker)

    def test_runtime_pipeline_update_cycle(self) -> None:
        """
        Simulates pipeline updates across state transitions (ALERT -> DROWSY -> ALERT)
        and verifies synchronous data flow to AlertManager, SessionLogger, and SessionStatisticsTracker.
        """
        app = StudentDrowsinessApp()
        app.session_logger = SessionLogger(log_path=str(self.test_log_path))
        app.stats_tracker = SessionStatisticsTracker()

        # Phase 1: Simulate ALERT state frames
        for _ in range(5):
            metrics = app.decision_engine.update(
                {"blink_count": 2, "consecutive_closed_frames": 0, "closed_duration_seconds": 0.0},
                {"yawn_count": 0, "consecutive_open_frames": 0, "yawn_duration_seconds": 0.0},
                {"yaw": 0.0, "pitch": 0.0, "roll": 0.0, "valid": True}
            )

            drowsiness_result = app.decision_engine.drowsiness_result
            if drowsiness_result:
                app.alert_manager.process_result(drowsiness_result)

            score_val = metrics.get("drowsiness_score", 0.0)
            state_raw = metrics.get("drowsiness_state", "ALERT")
            confidence_pct = (metrics.get("intermediate_decision") or {}).get("confidence_score", 0.0) * 100.0

            app.session_logger.update(state_raw, score_val, confidence_pct)
            app.stats_tracker.update(
                current_state=state_raw,
                score=score_val,
                avg_ear=0.32,
                mar=0.18,
                blink_count=2,
                yawn_count=0,
                closed_duration=0.0
            )

        # Phase 2: Simulate DROWSY state frames
        for _ in range(10):
            metrics = app.decision_engine.update(
                {"blink_count": 2, "consecutive_closed_frames": 60, "closed_duration_seconds": 2.0},
                {"yawn_count": 1, "consecutive_open_frames": 20, "yawn_duration_seconds": 2.5},
                {"yaw": 5.0, "pitch": 18.0, "roll": 2.0, "valid": True}
            )

            drowsiness_result = app.decision_engine.drowsiness_result
            if drowsiness_result:
                app.alert_manager.process_result(drowsiness_result)

            score_val = metrics.get("drowsiness_score", 0.0)
            state_raw = metrics.get("drowsiness_state", "ALERT")
            confidence_pct = (metrics.get("intermediate_decision") or {}).get("confidence_score", 0.0) * 100.0

            app.session_logger.update(state_raw, score_val, confidence_pct)
            app.stats_tracker.update(
                current_state=state_raw,
                score=score_val,
                avg_ear=0.15,
                mar=0.65,
                blink_count=2,
                yawn_count=1,
                closed_duration=2.0
            )

        # Verify SessionStatistics calculation
        stats = app.stats_tracker.get_stats()
        self.assertGreater(stats["highest_score"], 50.0)
        self.assertEqual(stats["yawn_count"], 1)
        self.assertGreater(stats["average_mar"], 0.0)
        self.assertGreater(stats["average_ear"], 0.0)

        # Verify SessionLogger wrote JSON event records
        self.assertTrue(self.test_log_path.exists())
        with open(self.test_log_path, "r", encoding="utf-8") as f:
            lines = [json.loads(line) for line in f if line.strip()]
        self.assertGreater(len(lines), 0)
        event_types = [l["event_type"] for l in lines]
        self.assertIn("alert_triggered", event_types)

    def test_graceful_shutdown(self) -> None:
        """
        Verifies that app.stop() cleanly exports stats, generates markdown summary reports,
        and releases internal detector and camera resources.
        """
        app = StudentDrowsinessApp()
        app.session_logger = SessionLogger(log_path=str(self.test_log_path))

        # Log mock initial state to generate log entries
        app.session_logger.update("ALERT", 10.0, 100.0)
        app.session_logger.update("DROWSY", 85.0, 95.0)

        # Mock camera and detector close methods to avoid hardware calls
        app.camera.stop = MagicMock()
        app.detector.close = MagicMock()

        # Run graceful shutdown
        app.stop()

        # Verify resource releases were called
        app.camera.stop.assert_called_once()
        app.detector.close.assert_called_once()
        self.assertFalse(app.is_running)

        # Verify session_statistics.json was created in config.REPORTS_DIR
        stats_file = self.test_output_dir / "session_statistics.json"
        self.assertTrue(stats_file.exists(), f"Expected {stats_file} to exist after shutdown.")
        with open(stats_file, "r", encoding="utf-8") as f:
            saved_stats = json.load(f)
        self.assertIn("total_session_time", saved_stats)
        self.assertIn("highest_score", saved_stats)

        # Verify session_summary_report.md was created in config.REPORTS_DIR
        report_file = self.test_output_dir / "session_summary_report.md"
        self.assertTrue(report_file.exists(), f"Expected {report_file} to exist after shutdown.")
        with open(report_file, "r", encoding="utf-8") as f:
            report_text = f.read()
        self.assertIn("Student Drowsiness Monitoring: Session Summary Report", report_text)
        self.assertIn("Key Performance Indicators", report_text)


if __name__ == "__main__":
    unittest.main()
