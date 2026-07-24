"""
Student Drowsiness Detection System - Main Application Entry Point

This module serves as the central application driver. It initializes system configuration,
the logger, camera video capture stream, and MediaPipe Face Mesh detector, running a clean
and extensible real-time frame processing loop.
"""

import sys
import cv2
import time
import config
from camera import CameraStream
from detection import FaceMeshDetector, EyeLandmarkExtractor, MouthLandmarkExtractor, EARCalculator, MARCalculator, YawnDetector, MouthState, HeadPoseEstimator, HeadPoseResult, StudentDrowsinessDecisionEngine, DrowsinessState, EyeStateClassifier, TemporalEyeAnalyzer, EyeState
from utils import get_logger
from alerts.alert_manager import AlertManager, HUDAlertChannel, AudioAlertChannel
from dashboard.hud import HUDVisualizer

# Import SessionLogger using local path manipulation to avoid standard library conflicts (Phase 12.3)
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "logging")))
try:
    from session_logger import SessionLogger
finally:
    if sys.path[0] == os.path.abspath(os.path.join(os.path.dirname(__file__), "logging")):
        sys.path.pop(0)

from analytics.session_statistics import SessionStatisticsTracker

# Initialize central logger for main application lifecycle
logger = get_logger("MainApplication")


class StudentDrowsinessApp:
    """
    Main application coordinator class managing camera stream and face mesh detection loop.
    """

    def __init__(self) -> None:
        """
        Initializes core system modules: Configuration, Camera Stream, Face Mesh Detector, Eye Landmark Extractor, and EAR Calculator.
        """
        logger.info("==================================================")
        logger.info("  Starting Student Drowsiness Detection System   ")
        logger.info("==================================================")
        logger.info(f"Loaded Settings -> Camera ID: {config.CAMERA_ID}, Target Resolution: {config.WEBCAM_WIDTH}x{config.WEBCAM_HEIGHT} @ {config.TARGET_FPS} FPS")

        # 1. Initialize Camera Module
        self.camera = CameraStream(
            source=config.CAMERA_ID,
            width=config.WEBCAM_WIDTH,
            height=config.WEBCAM_HEIGHT,
            fps_target=config.TARGET_FPS,
        )

        # 2. Initialize MediaPipe Face Mesh Module
        self.detector = FaceMeshDetector(
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        # 3. Initialize Eye Landmark Extractor Module
        self.eye_extractor = EyeLandmarkExtractor()
        self.mouth_extractor = MouthLandmarkExtractor()

        # 4. Initialize EAR Calculator Module
        self.ear_calculator = EARCalculator()
        self.mar_calculator = MARCalculator()
        self.yawn_detector = YawnDetector()
        self.head_pose_estimator = HeadPoseEstimator()

        # 5. Initialize Eye State Classifier Module
        self.classifier = EyeStateClassifier()

        # 6. Initialize Temporal Eye Analyzer Module
        self.temporal_analyzer = TemporalEyeAnalyzer(
            fps=self.camera.fps_target,
            min_blink_duration=getattr(config, "MIN_BLINK_DURATION_FRAMES", 2),
            max_blink_duration=getattr(config, "MAX_BLINK_DURATION_FRAMES", 15),
        )
        self.decision_engine = StudentDrowsinessDecisionEngine()

        # 7. Initialize Alert System (Phase 12.2 Integration)
        self.hud_channel = HUDAlertChannel()
        self.audio_channel = AudioAlertChannel()
        self.alert_manager = AlertManager(channels=[self.hud_channel, self.audio_channel])

        # 8. Initialize HUD Visualizer (Phase 12.2)
        self.visualizer = HUDVisualizer()

        # 9. Initialize Session Logger (Phase 12.3)
        self.session_logger = SessionLogger()

        # 10. Initialize Session Statistics Tracker (Phase 12.4)
        self.stats_tracker = SessionStatisticsTracker()

        # Session tracking variables
        self.start_time: float = 0.0

        self.is_running: bool = False


    def start(self) -> None:
        """
        Starts the real-time application processing loop and displays live video preview window.
        """
        logger.info("Initializing camera feed...")

        if not self.camera.start():
            logger.error("Unable to start camera stream. Please check camera hardware connection.")
            sys.exit(1)

        self.is_running = True
        self.start_time = time.time()
        logger.info("Application pipeline running. Press 'q' or 'ESC' on the video window to quit.")

        window_title = config.DASHBOARD_TITLE
        cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_title, config.WEBCAM_WIDTH, config.WEBCAM_HEIGHT)

        try:
            while self.is_running:
                # Step 1: Read frame from camera
                success, frame = self.camera.read_frame()
                if not success or frame is None:
                    logger.warning("Frame read returned empty or stream was disconnected.")
                    break

                # Step 2: Detect facial landmarks using Face Mesh
                has_face, all_landmarks = self.detector.detect_landmarks(frame)

                right_ear, left_ear, avg_ear = None, None, None
                right_state, left_state, overall_state = EyeState.UNKNOWN, EyeState.UNKNOWN, EyeState.UNKNOWN
                inner_lip, outer_lip = None, None
                mar_val = None

                # Step 3: Draw facial landmark mesh overlays, extract eye landmarks, and calculate EAR
                if has_face and all_landmarks:
                    frame = self.detector.draw_landmarks(frame)

                    # Extract right and left eye landmark subsets
                    face_landmarks = all_landmarks[0]
                    right_eye, left_eye = self.eye_extractor.extract_eye_landmarks(
                        face_landmarks, frame_shape=frame.shape
                    )

                    # Render cyan eye landmark highlights
                    frame = self.eye_extractor.draw_eye_landmarks(frame, right_eye, left_eye)

                    # Extract mouth inner and outer lip landmark subsets (Phase 7.3)
                    inner_lip, outer_lip = self.mouth_extractor.extract_mouth_landmarks(
                        face_landmarks, frame_shape=frame.shape
                    )

                    # Render magenta mouth landmark highlights (Phase 7.3)
                    frame = self.mouth_extractor.draw_mouth_landmarks(frame, inner_lip, outer_lip)

                    # Calculate Mouth Aspect Ratio (MAR) continuously (Phase 8.4)
                    mar_val = self.mar_calculator.calculate_mar(inner_lip)

                    # Calculate Eye Aspect Ratio (EAR) continuously for every frame
                    right_ear, left_ear, avg_ear = self.ear_calculator.calculate_ear(
                        right_eye, left_eye
                    )

                    # Validate range and detect step spikes
                    self.ear_calculator.validate_ear_value(avg_ear)
                    if hasattr(self, "_last_avg_ear"):
                        self.ear_calculator.detect_ear_spike(avg_ear, self._last_avg_ear)
                    self._last_avg_ear = avg_ear

                    # Periodically log EAR metrics (every 30 frames)
                    self.ear_calculator.log_ear_periodically(right_ear, left_ear, avg_ear)

                    # Classify eye states for temporal logging
                    right_state, left_state, overall_state = self.classifier.classify_both_eyes(
                        right_ear, left_ear
                    )

                    num_landmarks = len(face_landmarks)
                    num_right = len(right_eye) if right_eye is not None else 0
                    num_left = len(left_eye) if left_eye is not None else 0
                    status_text = f"Face Mesh Active ({num_landmarks} pts | Eyes: R={num_right}, L={num_left})"
                    status_color = (0, 255, 0)
                else:
                    status_text = "Searching for Face..."
                    status_color = (0, 0, 255)

                # Update the temporal analyzer on every frame
                self.temporal_analyzer.update(
                    right_state=right_state,
                    left_state=left_state,
                    overall_state=overall_state,
                    avg_ear=avg_ear,
                )
                self.yawn_detector.update(mar_val)
                pose_result = self.head_pose_estimator.estimate_head_pose(
                    all_landmarks[0] if (has_face and all_landmarks) else None,
                    (frame.shape[0], frame.shape[1])
                )
                # Step 3.5: Run Drowsiness Decision Engine
                eye_payload = {
                    "blink_count": self.temporal_analyzer.get_blink_count(),
                    "consecutive_closed_frames": self.temporal_analyzer.get_closed_frame_count(),
                    "closed_duration_seconds": self.temporal_analyzer.get_closed_duration_seconds()
                }
                yawn_payload = {
                    "yawn_count": self.yawn_detector.get_yawn_count(),
                    "consecutive_open_frames": self.yawn_detector.get_open_frame_count(),
                    "yawn_duration_seconds": self.yawn_detector.get_open_duration_seconds()
                }
                pose_payload = {
                    "yaw": pose_result.yaw,
                    "pitch": pose_result.pitch,
                    "roll": pose_result.roll,
                    "valid": pose_result.valid
                }
                decision_metrics = self.decision_engine.update(eye_payload, yawn_payload, pose_payload)

                # Process result in Alert Manager (Phase 12.2 Integration)
                drowsiness_result = self.decision_engine.drowsiness_result
                if drowsiness_result is not None:
                    self.alert_manager.process_result(drowsiness_result)

                # Update structured session logs (Phase 12.3)
                score_val = decision_metrics.get("drowsiness_score", 0.0)
                state_raw = decision_metrics.get("drowsiness_state", "ALERT")
                confidence_pct = (decision_metrics.get("intermediate_decision") or {}).get("confidence_score", 0.0) * 100.0
                self.session_logger.update(state_raw, score_val, confidence_pct)

                # Update session statistics (Phase 12.4)
                self.stats_tracker.update(
                    current_state=state_raw,
                    score=score_val,
                    avg_ear=avg_ear,
                    mar=mar_val,
                    blink_count=self.temporal_analyzer.get_blink_count(),
                    yawn_count=self.yawn_detector.get_yawn_count(),
                    closed_duration=self.temporal_analyzer.get_closed_duration_seconds()
                )


                # Query Alert Status
                hud_active = self.hud_channel.current_message is not None
                audio_active = (drowsiness_result.state == DrowsinessState.HIGHLY_DROWSY) if drowsiness_result else False

                # Check config flags
                hud_enabled = getattr(config, "VISUAL_ALERT_ENABLED", True)
                audio_enabled = getattr(config, "AUDIO_ALERT_ENABLED", True)

                alert_statuses = []
                if hud_enabled:
                    alert_statuses.append(f"HUD {'ACTIVE' if hud_active else 'READY'}")
                else:
                    alert_statuses.append("HUD DISABLED")

                if audio_enabled:
                    alert_statuses.append(f"AUDIO {'ACTIVE' if audio_active else 'READY'}")
                else:
                    alert_statuses.append("AUDIO DISABLED")

                alert_status_str = " | ".join(alert_statuses)

                # Format session duration
                elapsed_seconds = int(time.time() - self.start_time)
                hrs = elapsed_seconds // 3600
                mins = (elapsed_seconds % 3600) // 60
                secs = elapsed_seconds % 60
                if hrs > 0:
                    session_time_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"
                else:
                    session_time_str = f"{mins:02d}:{secs:02d}"

                # Extra descriptors for eye & mouth
                thresh_val = self.classifier.get_threshold()
                mouth_state_enum = self.yawn_detector.classify_mouth_state(mar_val)
                mouth_state_str = mouth_state_enum.value

                # Assemble metrics payload for the independent visualizer
                metrics_payload = {
                    "session_time": session_time_str,
                    "fps": self.camera.get_fps(),
                    "drowsiness_state": decision_metrics.get("drowsiness_state", "ALERT"),
                    "drowsiness_score": decision_metrics.get("drowsiness_score", 0.0),
                    "confidence": (decision_metrics.get("intermediate_decision") or {}).get("confidence_score", 0.0) * 100.0,
                    "cooccurrence": (decision_metrics.get("intermediate_decision") or {}).get("signal_cooccurrence_count", 0),
                    "explanation": (decision_metrics.get("drowsiness_result") or {}).get("explanation", ""),
                    "blink_count": self.temporal_analyzer.get_blink_count(),
                    "closed_frames": self.temporal_analyzer.get_closed_frame_count(),
                    "closed_time": self.temporal_analyzer.get_closed_duration_seconds(),
                    "yawn_count": self.yawn_detector.get_yawn_count(),
                    "open_time": self.yawn_detector.get_open_duration_seconds(),
                    "ear_metrics": {
                        "left_ear": left_ear,
                        "right_ear": right_ear,
                        "avg_ear": avg_ear,
                        "threshold": thresh_val,
                        "state": overall_state.value if hasattr(overall_state, "value") else str(overall_state)
                    },
                    "mar_metrics": {
                        "mar": mar_val,
                        "threshold": self.yawn_detector.mar_threshold if hasattr(self.yawn_detector, "mar_threshold") else 0.60,
                        "state": mouth_state_str
                    },
                    "head_pose": {
                        "yaw": pose_result.yaw,
                        "pitch": pose_result.pitch,
                        "roll": pose_result.roll,
                        "valid": pose_result.valid
                    },
                    "recent_event": self.alert_manager.get_last_event(),
                    "alert_status": alert_status_str
                }

                # Step 4: Render new dashboard layout (Phase 12.2)
                frame = self.visualizer.draw(frame, metrics_payload)

                # Step 6: Render video preview window
                cv2.imshow(window_title, frame)

                # Step 7: Process keyboard controls ('q' or ESC to exit)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q") or key == 27:
                    logger.info("Exit requested by user via keyboard shortcut.")
                    break

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt (Ctrl+C) detected. Exiting app...")
        except Exception as e:
            logger.error(f"Unexpected error in application main loop: {e}", exc_info=True)
        finally:
            self.stop()

    def stop(self) -> None:
        """
        Releases camera, closes MediaPipe detectors, and destroys OpenCV preview windows cleanly.
        """
        logger.info("Stopping application and releasing resources...")
        self.is_running = False

        # Save session statistics to reports directory (Phase 12.4)
        if hasattr(self, "stats_tracker") and self.stats_tracker:
            self.stats_tracker.save_stats(config.REPORTS_DIR / "session_statistics.json")

        # Generate session summary report (Phase 12.5)
        if hasattr(self, "stats_tracker") and self.stats_tracker and hasattr(self, "session_logger") and self.session_logger:
            try:
                from reports.report_generator import ReportGenerator
                generator = ReportGenerator(
                    stats_payload=self.stats_tracker.get_stats(),
                    event_log_path=str(self.session_logger.log_path)
                )
                generator.generate_report(config.REPORTS_DIR / "session_summary_report.md")
            except Exception as e:
                logger.error(f"Failed to generate session summary report: {e}", exc_info=True)

        if hasattr(self, "detector") and self.detector:
            self.detector.close()

        if hasattr(self, "camera") and self.camera:
            self.camera.stop()

        cv2.destroyAllWindows()
        logger.info("Application shut down cleanly.")


def main() -> None:
    """Main execution entry point."""
    app = StudentDrowsinessApp()
    app.start()


if __name__ == "__main__":
    main()
