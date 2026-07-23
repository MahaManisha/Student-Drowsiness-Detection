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
from detection import FaceMeshDetector, EyeLandmarkExtractor, EARCalculator, EyeStateClassifier, TemporalEyeAnalyzer, EyeState
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

        # 4. Initialize EAR Calculator Module
        self.ear_calculator = EARCalculator()

        # 5. Initialize Eye State Classifier Module
        self.classifier = EyeStateClassifier()

        # 6. Initialize Temporal Eye Analyzer Module
        self.temporal_analyzer = TemporalEyeAnalyzer(
            fps=self.camera.fps_target,
            min_blink_duration=getattr(config, "MIN_BLINK_DURATION_FRAMES", 2),
            max_blink_duration=getattr(config, "MAX_BLINK_DURATION_FRAMES", 15),
        )

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

                # Draw a premium semi-transparent HUD background box for the metrics
                hud_overlay = frame.copy()
                # Draw dark gray rectangle on top-left area (expanded height for new metrics)
                cv2.rectangle(hud_overlay, (10, 80), (320, 335), (15, 15, 15), -1)
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
