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
from detection import FaceMeshDetector
from utils import get_logger

# Initialize central logger for main application lifecycle
logger = get_logger("MainApplication")


class StudentDrowsinessApp:
    """
    Main application coordinator class managing camera stream and face mesh detection loop.
    """

    def __init__(self) -> None:
        """
        Initializes core system modules: Configuration, Camera Stream, and Face Mesh Detector.
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

                # Step 3: Draw facial landmark mesh overlays
                if has_face:
                    frame = self.detector.draw_landmarks(frame)
                    num_landmarks = len(all_landmarks[0]) if all_landmarks else 0
                    status_text = f"Face Mesh Active ({num_landmarks} landmarks)"
                    status_color = (0, 255, 0)
                else:
                    status_text = "Searching for Face..."
                    status_color = (0, 0, 255)

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
