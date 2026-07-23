"""
Student Drowsiness Detection System - Main Application Entry Point

This module serves as the central application driver. It initializes system configuration,
the logger, camera video capture stream, and MediaPipe Face Mesh detector, running a clean
and extensible real-time frame processing loop.
"""

import sys
import cv2

import config
from camera import CameraStream
from detection import FaceMeshDetector, EyeLandmarkExtractor, MouthLandmarkExtractor, EARCalculator, MARCalculator, YawnDetector, MouthState, HeadPoseEstimator, HeadPoseResult, StudentDrowsinessDecisionEngine, DrowsinessState, EyeStateClassifier, TemporalEyeAnalyzer, EyeState
from utils import get_logger

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

                # Step 4: Render UI status banner on frame
                cv2.putText(
                    frame,
                    status_text,
                    (15, 65),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    status_color,
                    2,
                    cv2.LINE_AA,
                )

                # Step 5: Render Metrics Overlay (HUD Style)
                # Format string representations of EAR values
                l_str = f"{left_ear:.3f}" if left_ear is not None else "N/A"
                r_str = f"{right_ear:.3f}" if right_ear is not None else "N/A"
                avg_str = f"{avg_ear:.3f}" if avg_ear is not None else "N/A"
                thresh_val = self.classifier.get_threshold()
                state_str = overall_state.value

                # Get temporal metrics for display
                blink_count = self.temporal_analyzer.get_blink_count()
                closed_frames = self.temporal_analyzer.get_closed_frame_count()
                closed_time = self.temporal_analyzer.get_closed_duration_seconds()

                # Get mouth metrics for display (Phase 7.5, 8.4, & 9.5)
                yawn_metrics = self.yawn_detector.get_yawn_metrics()
                yawn_count = yawn_metrics["yawn_count"]
                open_frames = yawn_metrics["consecutive_open_frames"]
                open_duration = yawn_metrics["yawn_duration_seconds"]

                mouth_state_enum = self.yawn_detector.classify_mouth_state(mar_val)
                mouth_state_str = mouth_state_enum.value

                # Color-code mouth state (Vivid Green = CLOSED, Magenta = OPEN, Gray = UNKNOWN)
                if mouth_state_enum == MouthState.OPEN:
                    mouth_state_color = (255, 0, 255)  # Magenta
                elif mouth_state_enum == MouthState.CLOSED:
                    mouth_state_color = (0, 255, 0)    # Vivid Green
                else:
                    mouth_state_color = (130, 130, 130) # Neutral Gray

                mar_str = f"{mar_val:.2f}" if mar_val is not None else "N/A"

                # Draw a premium semi-transparent HUD background boxes for the metrics
                hud_overlay = frame.copy()
                # Draw left metrics box (expanded height for yawn and mouth metrics)
                cv2.rectangle(hud_overlay, (10, 80), (320, 460), (15, 15, 15), -1)
                # Draw right metrics box for head pose (symmetrical size)
                cv2.rectangle(hud_overlay, (330, 80), (630, 215), (15, 15, 15), -1)
                # Draw right metrics box for drowsiness decision engine (symmetrical size)
                cv2.rectangle(hud_overlay, (330, 230), (630, 390), (15, 15, 15), -1)
                alpha = 0.7
                cv2.addWeighted(hud_overlay, alpha, frame, 1.0 - alpha, 0, frame)

                # Set up typography styling
                font = cv2.FONT_HERSHEY_SIMPLEX
                scale = 0.55
                text_color = (245, 245, 245)  # Soft white
                thickness = 2
                line_type = cv2.LINE_AA

                # Draw the individual EAR values and Threshold inside the HUD box
                cv2.putText(frame, f"Left EAR : {l_str}", (20, 105), font, scale, text_color, thickness, line_type)
                cv2.putText(frame, f"Right EAR : {r_str}", (20, 135), font, scale, text_color, thickness, line_type)
                cv2.putText(frame, f"Average EAR : {avg_str}", (20, 165), font, scale, text_color, thickness, line_type)
                cv2.putText(frame, f"Threshold : {thresh_val:.3f}", (20, 195), font, scale, text_color, thickness, line_type)

                # Color-code the Eye State to make it immediately recognizable (Green = OPEN, Red = CLOSED, Gray = UNKNOWN)
                if overall_state == EyeState.OPEN:
                    state_color = (0, 255, 0)      # Vivid Green
                elif overall_state == EyeState.CLOSED:
                    state_color = (0, 0, 255)      # Vivid Red
                else:
                    state_color = (130, 130, 130)  # Neutral Gray

                cv2.putText(frame, f"Eye State : {state_str}", (20, 225), font, 0.6, state_color, 2, line_type)

                # Render Phase 6.5 temporal metrics
                cv2.putText(frame, f"Blink Count : {blink_count}", (20, 255), font, scale, text_color, thickness, line_type)
                cv2.putText(frame, f"Closed Frames : {closed_frames}", (20, 285), font, scale, text_color, thickness, line_type)
                cv2.putText(frame, f"Closed Time : {closed_time:.2f} s", (20, 315), font, scale, text_color, thickness, line_type)

                # Render Phase 9.5 YawnDetector metrics (compact spacing)
                cv2.putText(frame, f"MAR : {mar_str}", (20, 340), font, scale, text_color, thickness, line_type)
                
                cv2.putText(frame, "Mouth State : ", (20, 365), font, scale, text_color, thickness, line_type)
                cv2.putText(frame, mouth_state_str, (135, 365), font, 0.6, mouth_state_color, 2, line_type)
                
                cv2.putText(frame, f"Yawn Count : {yawn_count}", (20, 390), font, scale, text_color, thickness, line_type)
                cv2.putText(frame, f"Open Frames : {open_frames}", (20, 415), font, scale, text_color, thickness, line_type)
                cv2.putText(frame, f"Open Time : {open_duration:.2f} s", (20, 440), font, scale, text_color, thickness, line_type)

                # Render Phase 10.5 HeadPoseEstimator metrics (top-right box)
                pitch_val = pose_result.pitch
                yaw_val = pose_result.yaw
                roll_val = pose_result.roll
                
                if pose_result.valid:
                    pitch_val_str = f"{pitch_val:.1f}"
                    yaw_val_str = f"{yaw_val:.1f}"
                    roll_val_str = f"{roll_val:.1f}"
                    
                    p_text = f"Pitch : {pitch_val_str}"
                    (pw, ph), _ = cv2.getTextSize(p_text, font, scale, thickness)
                    cv2.putText(frame, p_text, (340, 105), font, scale, text_color, thickness, line_type)
                    cv2.circle(frame, (340 + pw + 3, 105 - ph + 2), 2, text_color, 1)

                    y_text = f"Yaw : {yaw_val_str}"
                    (yw, yh), _ = cv2.getTextSize(y_text, font, scale, thickness)
                    cv2.putText(frame, y_text, (340, 135), font, scale, text_color, thickness, line_type)
                    cv2.circle(frame, (340 + yw + 3, 135 - yh + 2), 2, text_color, 1)

                    r_text = f"Roll : {roll_val_str}"
                    (rw, rh), _ = cv2.getTextSize(r_text, font, scale, thickness)
                    cv2.putText(frame, r_text, (340, 165), font, scale, text_color, thickness, line_type)
                    cv2.circle(frame, (340 + rw + 3, 165 - rh + 2), 2, text_color, 1)
                    
                    pose_status_str = "TRACKING"
                    pose_status_color = (0, 255, 0)      # Vivid Green
                else:
                    cv2.putText(frame, "Pitch : N/A", (340, 105), font, scale, text_color, thickness, line_type)
                    cv2.putText(frame, "Yaw : N/A", (340, 135), font, scale, text_color, thickness, line_type)
                    cv2.putText(frame, "Roll : N/A", (340, 165), font, scale, text_color, thickness, line_type)
                    pose_status_str = "SEARCHING"
                    pose_status_color = (0, 0, 255)      # Vivid Red
                
                cv2.putText(frame, "Status : ", (340, 195), font, scale, text_color, thickness, line_type)
                cv2.putText(frame, pose_status_str, (415, 195), font, 0.6, pose_status_color, 2, line_type)

                # Render Phase 11.5 DrowsinessDecisionEngine metrics (bottom-right box)
                score_val = decision_metrics["drowsiness_score"]
                state_raw = decision_metrics["drowsiness_state"]
                state_str = state_raw.replace("_", " ")

                # Color-code drowsiness state
                if state_raw == "ALERT":
                    state_color = (0, 255, 0)         # Vivid Green
                elif state_raw == "SLIGHTLY_DROWSY":
                    state_color = (0, 255, 255)       # Vivid Yellow
                elif state_raw == "DROWSY":
                    state_color = (0, 165, 255)       # Orange
                else:  # HIGHLY_DROWSY
                    state_color = (0, 0, 255)         # Vivid Red

                # Extract intermediate decision parameters for confidence indicator
                inter_dec = decision_metrics.get("intermediate_decision")
                if inter_dec is not None:
                    confidence_pct = inter_dec.get("confidence_score", 0.0) * 100.0
                    cooccurrence = inter_dec.get("signal_cooccurrence_count", 0)
                else:
                    confidence_pct = 0.0
                    cooccurrence = 0

                cv2.putText(frame, f"Score : {score_val:.0f}", (340, 255), font, scale, text_color, thickness, line_type)
                
                cv2.putText(frame, "State : ", (340, 285), font, scale, text_color, thickness, line_type)
                cv2.putText(frame, state_str, (405, 285), font, 0.6, state_color, 2, line_type)
                
                cv2.putText(frame, f"Confidence : {confidence_pct:.0f}%", (340, 315), font, scale, text_color, thickness, line_type)
                cv2.putText(frame, f"Co-occurrence : {cooccurrence} / 3", (340, 345), font, scale, text_color, thickness, line_type)

                # Step 5: Render FPS counter badge
                frame = self.camera.draw_fps_overlay(frame)

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
