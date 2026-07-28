"""
Student Drowsiness Detection System - Camera Stream Module

Stage-by-Stage Diagnostic Instrumentation - Thread 1: Camera Producer.
Logs [BEFORE_CAMERA_READ] and [AFTER_CAMERA_READ] with microsecond timing into runtime_debug.log.
Does NOT modify any backend AI detection algorithms, math calculators, or thresholds.
"""

import time
import cv2
import queue
import datetime
import traceback
import threading
import numpy as np
from typing import Optional, Tuple, Generator, Union

from config import CAMERA_ID, WEBCAM_WIDTH, WEBCAM_HEIGHT, TARGET_FPS
from utils.logger import get_logger

logger = get_logger(__name__)


def log_runtime_debug(thread_name: str, func_name: str, stage_marker: str, frame_id: int, elapsed_ms: float, status: str = "OK", extra: str = "") -> None:
    """Logs standardized diagnostic entry into runtime_debug.log."""
    try:
        now_str = datetime.datetime.now().isoformat()
        log_line = f"[{now_str}] | [{thread_name}] | [{func_name}] | [{stage_marker}] | Frame: {frame_id} | Elapsed: {elapsed_ms:.3f} ms | Status: {status} {extra}\n"
        with open("runtime_debug.log", "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception:
        pass


class CameraStream:
    """
    Thread 1: Asynchronous Camera Producer Thread with stage-by-stage diagnostic logging.
    """

    def __init__(
        self,
        source: Union[int, str] = CAMERA_ID,
        width: int = WEBCAM_WIDTH,
        height: int = WEBCAM_HEIGHT,
        fps_target: int = TARGET_FPS,
    ) -> None:
        self.source = source
        self.width = width
        self.height = height
        self.fps_target = fps_target

        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running: bool = False

        self._frame_queue: queue.Queue = queue.Queue(maxsize=1)
        self._producer_thread: Optional[threading.Thread] = None
        self._lock: threading.Lock = threading.Lock()

        self.consecutive_failed_reads: int = 0
        self.last_frame_timestamp: float = 0.0
        self.total_frames_captured: int = 0

        self._prev_time: float = 0.0
        self._current_fps: float = 0.0

    def is_available(self) -> bool:
        try:
            temp_cap = cv2.VideoCapture(self.source)
            if temp_cap.isOpened():
                ret, _ = temp_cap.read()
                temp_cap.release()
                time.sleep(0.1)
                return ret
            return False
        except Exception as e:
            logger.error(f"Error checking camera availability for source '{self.source}': {e}")
            return False

    def start(self) -> bool:
        if self.is_running and self.cap is not None and self.cap.isOpened():
            logger.info("Camera stream is already active.")
            return True

        logger.info(f"[THREAD 1] Opening camera source: {self.source} ({self.width}x{self.height})...")

        try:
            self.cap = cv2.VideoCapture(self.source, cv2.CAP_DSHOW if isinstance(self.source, int) else cv2.CAP_ANY)

            if not self.cap.isOpened():
                if self.cap is not None:
                    self.cap.release()
                self.cap = cv2.VideoCapture(self.source)

            if not self.cap.isOpened():
                logger.error(f"[THREAD 1] Failed to open camera source: {self.source}")
                self.is_running = False
                return False

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps_target)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            logger.info(f"[THREAD 1] Camera stream started. Resolution: {actual_w}x{actual_h}. CAP_PROP_BUFFERSIZE=1.")

            self.is_running = True
            self._prev_time = time.time()
            self.last_frame_timestamp = time.time()
            self.consecutive_failed_reads = 0

            self._producer_thread = threading.Thread(target=self._producer_loop, name="CameraProducerThread", daemon=True)
            self._producer_thread.start()
            return True

        except Exception as e:
            logger.error(f"[THREAD 1] Unhandled error initializing camera: {e}", exc_info=True)
            self.is_running = False
            return False

    def _reconnect_camera(self) -> None:
        logger.warning("[THREAD 1 WATCHDOG] Frame drop stall detected. Auto-reconnecting camera hardware...")
        try:
            if self.cap is not None:
                self.cap.release()
            
            time.sleep(0.2)
            self.cap = cv2.VideoCapture(self.source, cv2.CAP_DSHOW if isinstance(self.source, int) else cv2.CAP_ANY)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(self.source)

            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                self.cap.set(cv2.CAP_PROP_FPS, self.fps_target)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                self.consecutive_failed_reads = 0
                logger.info("[THREAD 1 WATCHDOG] Camera reconnected successfully.")
            else:
                logger.error("[THREAD 1 WATCHDOG] Reconnection attempt failed.")
        except Exception as e:
            logger.error(f"[THREAD 1 WATCHDOG] Error during camera reconnection: {e}")

    def _producer_loop(self) -> None:
        logger.info("[THREAD 1] Camera Producer thread loop active (30 FPS target).")
        while self.is_running:
            if self.cap is None or not self.cap.isOpened():
                self._reconnect_camera()
                time.sleep(0.5)
                continue

            frame_id = self.total_frames_captured + 1
            t_start = time.time()
            t1_cap = time.perf_counter()
            log_runtime_debug("CameraProducerThread", "_producer_loop", "[BEFORE_CAMERA_READ]", frame_id, 0.0)

            try:
                ret, frame = self.cap.read()
                t2_cap = time.perf_counter()
                t_end = time.time()
                elapsed_ms = (t_end - t_start) * 1000.0

                if ret and frame is not None:
                    log_runtime_debug("CameraProducerThread", "_producer_loop", "[AFTER_CAMERA_READ]", frame_id, elapsed_ms, "OK", f"shape={frame.shape}")
                    self.consecutive_failed_reads = 0
                    self.total_frames_captured += 1
                    now = time.time()
                    self.last_frame_timestamp = now

                    dt = now - self._prev_time
                    if dt > 0:
                        self._current_fps = 1.0 / dt
                    self._prev_time = now

                    t1_qw = time.perf_counter()
                    if self._frame_queue.full():
                        try:
                            self._frame_queue.get_nowait()
                        except queue.Empty:
                            pass

                    self._frame_queue.put_nowait((frame, meta if 'meta' in locals() else {}))
                    t2_qw = time.perf_counter()

                    meta = {
                        "t_capture_start": t_start,
                        "t_capture_end": t_end,
                        "t_queue_enter": time.time(),
                        "t1_cap": t1_cap,
                        "t2_cap": t2_cap,
                        "t1_qw": t1_qw,
                        "t2_qw": t2_qw,
                        "frame_id": frame_id
                    }
                    # Update queue item with completed meta
                    try:
                        self._frame_queue.get_nowait()
                    except queue.Empty:
                        pass
                    self._frame_queue.put_nowait((frame, meta))
                else:
                    log_runtime_debug("CameraProducerThread", "_producer_loop", "[AFTER_CAMERA_READ]", frame_id, elapsed_ms, "FAIL_RET_FALSE")
                    self.consecutive_failed_reads += 1
                    time.sleep(0.005)

                    if self.consecutive_failed_reads >= 45:
                        self._reconnect_camera()

            except Exception as e:
                tb_str = traceback.format_exc().replace('\n', ' ')
                log_runtime_debug("CameraProducerThread", "_producer_loop", "[AFTER_CAMERA_READ]", frame_id, 0.0, "EXCEPT", tb_str)
                self.consecutive_failed_reads += 1
                time.sleep(0.01)

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        success, frame, _ = self.read_frame_with_meta()
        return success, frame

    def read_frame_with_meta(self) -> Tuple[bool, Optional[np.ndarray], dict]:
        if not self.is_running:
            return False, None, {}

        # Safely drain queue to get the NEWEST available frame (discarding outdated items)
        latest_item = None
        while not self._frame_queue.empty():
            try:
                latest_item = self._frame_queue.get_nowait()
            except queue.Empty:
                break

        if latest_item is None:
            try:
                latest_item = self._frame_queue.get_nowait()
            except queue.Empty:
                return False, None, {}

        frame, meta = latest_item
        return True, frame, meta

    def get_fps(self) -> float:
        return round(self._current_fps, 1)

    def draw_fps_overlay(self, frame: np.ndarray) -> np.ndarray:
        fps_text = f"FPS: {self.get_fps():.1f}"
        cv2.putText(
            frame,
            fps_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )
        return frame

    def generate_frames(self) -> Generator[np.ndarray, None, None]:
        while self.is_running:
            ret, frame = self.read_frame()
            if ret and frame is not None:
                yield frame
            else:
                time.sleep(0.005)

    def stop(self) -> None:
        logger.info("[THREAD 1] Stopping Camera Producer thread...")
        self.is_running = False

        if self._producer_thread is not None and self._producer_thread.is_alive():
            self._producer_thread.join(timeout=1.0)

        if self.cap is not None:
            self.cap.release()
            self.cap = None

        logger.info("[THREAD 1] Camera stream stopped.")
