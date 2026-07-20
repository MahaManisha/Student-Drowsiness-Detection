"""
Student Drowsiness Detection System - Camera Stream Module

This module provides a robust, reusable CameraStream class for video feed ingestion.
It supports camera availability checks, resolution configuration, real-time FPS
calculation, overlay rendering, graceful error handling, and generator-based frame streaming.
"""

import time
import cv2
import numpy as np
from typing import Optional, Tuple, Generator, Union

from config import CAMERA_ID, WEBCAM_WIDTH, WEBCAM_HEIGHT, TARGET_FPS
from utils.logger import get_logger

logger = get_logger(__name__)


class CameraStream:
    """
    Reusable camera manager class for video stream ingestion and frame capture.
    """

    def __init__(
        self,
        source: Union[int, str] = CAMERA_ID,
        width: int = WEBCAM_WIDTH,
        height: int = WEBCAM_HEIGHT,
        fps_target: int = TARGET_FPS,
    ) -> None:
        """
        Initializes the CameraStream parameters.

        Args:
            source (int | str): Camera index (e.g., 0) or RTSP video URL string.
            width (int): Target frame width resolution.
            height (int): Target frame height resolution.
            fps_target (int): Target frames per second.
        """
        self.source = source
        self.width = width
        self.height = height
        self.fps_target = fps_target

        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running: bool = False

        # Internal FPS calculation tracking
        self._prev_time: float = 0.0
        self._current_fps: float = 0.0

    def is_available(self) -> bool:
        """
        Checks if the camera device is accessible without opening a persistent stream.

        Returns:
            bool: True if camera device opens successfully, False otherwise.
        """
        try:
            temp_cap = cv2.VideoCapture(self.source)
            if temp_cap.isOpened():
                ret, _ = temp_cap.read()
                temp_cap.release()
                return ret
            return False
        except Exception as e:
            logger.error(f"Error checking camera availability for source '{self.source}': {e}")
            return False

    def start(self) -> bool:
        """
        Opens the camera device and configures stream properties.

        Returns:
            bool: True if camera started successfully, False on error.
        """
        if self.is_running and self.cap is not None and self.cap.isOpened():
            logger.info("Camera stream is already active.")
            return True

        logger.info(f"Opening camera source: {self.source} ({self.width}x{self.height})...")

        try:
            # OpenCV DirectShow backend preferred on Windows for fast init
            self.cap = cv2.VideoCapture(self.source, cv2.CAP_DSHOW if isinstance(self.source, int) else cv2.CAP_ANY)

            if not self.cap.isOpened():
                # Fallback to standard backend if DSHOW fails
                self.cap = cv2.VideoCapture(self.source)

            if not self.cap.isOpened():
                logger.error(f"Failed to open camera source: {self.source}")
                self.is_running = False
                return False

            # Set camera capture resolution & frame rate
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps_target)

            # Query actual hardware resolution set by OpenCV
            actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            logger.info(f"Camera stream started successfully. Resolution set to {actual_w}x{actual_h}.")

            self.is_running = True
            self._prev_time = time.time()
            return True

        except Exception as e:
            logger.error(f"Unhandled error initializing camera stream: {e}", exc_info=True)
            self.is_running = False
            return False

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Captures a single frame from the camera stream and updates the real-time FPS.

        Returns:
            Tuple[bool, Optional[np.ndarray]]:
                - bool: True if frame read succeeded, False otherwise.
                - np.ndarray: Captured image frame in BGR format, or None if failed.
        """
        if not self.is_running or self.cap is None or not self.cap.isOpened():
            logger.warning("Attempted to read frame from an uninitialized camera stream.")
            return False, None

        try:
            ret, frame = self.cap.read()

            if not ret or frame is None:
                logger.warning("Failed to retrieve frame from camera (end of stream or disconnected).")
                return False, None

            # Update real-time FPS calculation
            current_time = time.time()
            time_diff = current_time - self._prev_time
            if time_diff > 0:
                self._current_fps = 1.0 / time_diff
            self._prev_time = current_time

            return True, frame

        except Exception as e:
            logger.error(f"Error reading frame from camera: {e}")
            return False, None

    def get_fps(self) -> float:
        """
        Returns the current measured FPS (Frames Per Second).

        Returns:
            float: Current frames per second value.
        """
        return round(self._current_fps, 1)

    def draw_fps_overlay(self, frame: np.ndarray) -> np.ndarray:
        """
        Renders an FPS counter overlay on top of the image frame.

        Args:
            frame (np.ndarray): Input image frame.

        Returns:
            np.ndarray: Modified frame with FPS text overlay.
        """
        if frame is None:
            return frame

        fps_text = f"FPS: {self.get_fps()}"
        # Draw background rectangle for high text visibility
        cv2.rectangle(frame, (10, 10), (130, 40), (0, 0, 0), -1)
        cv2.putText(
            frame,
            fps_text,
            (18, 32),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )
        return frame

    def get_frames(self) -> Generator[np.ndarray, None, None]:
        """
        Generator function yielding live video frames for downstream processing loops.

        Yields:
            np.ndarray: Captured video frame with FPS overlay.
        """
        if not self.is_running:
            if not self.start():
                return

        try:
            while self.is_running:
                success, frame = self.read_frame()
                if not success or frame is None:
                    logger.warning("Frame read unsuccessful. Stopping stream generator.")
                    break

                yield frame

        finally:
            self.stop()

    def stop(self) -> None:
        """
        Releases the camera device and cleans up resources cleanly.
        """
        if self.cap is not None and self.cap.isOpened():
            logger.info("Releasing camera stream resources...")
            self.cap.release()
            self.cap = None

        self.is_running = False
        logger.info("Camera stream stopped.")

    def __enter__(self) -> "CameraStream":
        """Context manager entry point."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit point (ensures camera is released automatically)."""
        self.stop()


# Runnable standalone test script when executed directly
if __name__ == "__main__":
    print("=== Testing CameraStream Module ===")
    camera = CameraStream()

    if not camera.is_available():
        print(f"⚠️ Camera source '{CAMERA_ID}' is NOT available or already in use.")
    else:
        print(f"✅ Camera source '{CAMERA_ID}' detected successfully!")
        if camera.start():
            print("Press 'q' in the camera window to exit preview test...")
            while True:
                ret, frame = camera.read_frame()
                if not ret or frame is None:
                    break

                # Draw FPS overlay
                frame = camera.draw_fps_overlay(frame)

                # Show preview window
                cv2.imshow("Camera Stream Test", frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            camera.stop()
            cv2.destroyAllWindows()
            print("Camera preview closed cleanly.")
