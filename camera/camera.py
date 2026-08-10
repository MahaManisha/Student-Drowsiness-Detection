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
from collections import deque
from typing import Optional, Tuple, Generator, Union

import sys
import pathlib

ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import CAMERA_ID, WEBCAM_WIDTH, WEBCAM_HEIGHT, TARGET_FPS
try:
    from utils.logger import get_logger
    logger = get_logger(__name__)
except Exception:
    import logging
    logger = logging.getLogger(__name__)


def log_runtime_debug(thread_name: str, func_name: str, stage_marker: str, frame_id: int, elapsed_ms: float, status: str = "OK", extra: str = "") -> None:
    """Logs standardized diagnostic entry into runtime_debug.log (fast-path for normal execution)."""
    if status == "OK":
        return
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
        self._queue_lock: threading.Lock = threading.Lock()

        self.consecutive_failed_reads: int = 0
        self.last_frame_timestamp: float = 0.0
        self.total_frames_captured: int = 0

        self._prev_time: float = 0.0
        self._current_fps: float = 0.0
        self._fps_timestamps: deque = deque()

        # Thread-safe buffer for zero-latency MJPEG streaming
        self._latest_raw_frame: Optional[np.ndarray] = None
        self._latest_raw_frame_id: int = 0
        self._raw_frame_lock: threading.Lock = threading.Lock()

        # Phase 1 & 2 Frame-Progression Watchdog Counters & Timestamps
        self.camera_read_frame_id: int = 0
        self.queue_publish_frame_id: int = 0
        self.last_camera_success_perf: float = time.perf_counter()
        self.last_queue_publish_perf: float = time.perf_counter()
        self.last_producer_stage: str = "CAMERA_IDLE"

    def is_available(self) -> bool:
        """
        Safely checks camera availability without creating duplicate VideoCapture
        instances if the stream is already active.
        """
        with self._lock:
            if self.cap is not None:
                return self.cap.isOpened()

        if self.is_running:
            return True

        try:
            temp_cap = cv2.VideoCapture(self.source, cv2.CAP_MSMF if isinstance(self.source, int) else cv2.CAP_ANY)
            if not temp_cap.isOpened():
                temp_cap = cv2.VideoCapture(self.source, cv2.CAP_DSHOW if isinstance(self.source, int) else cv2.CAP_ANY)

            if temp_cap.isOpened():
                temp_cap.release()
                return True
            return False
        except Exception as e:
            logger.error(f"Error checking camera availability for source '{self.source}': {e}")
            return False

    def _try_open_backend(self, backend: int) -> Optional[cv2.VideoCapture]:
        try:
            cap = cv2.VideoCapture(self.source, backend)
            if not cap.isOpened():
                try:
                    cap.release()
                except Exception:
                    pass
                return None

            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            cap.set(cv2.CAP_PROP_FPS, self.fps_target)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            # Perform a test read to ensure hardware is actively delivering frames
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                return cap

            try:
                cap.release()
            except Exception:
                pass
            return None
        except Exception as e:
            logger.warning(f"[THREAD 1] Exception trying backend {backend}: {e}")
            return None

    def start(self) -> bool:
        with self._lock:
            if self.is_running and self.cap is not None and self.cap.isOpened():
                logger.info("Camera stream is already active.")
                return True

            logger.info(f"[THREAD 1] Opening camera source: {self.source} ({self.width}x{self.height})...")

            try:
                if self.cap is not None:
                    try:
                        self.cap.release()
                    except Exception:
                        pass
                    self.cap = None

                backends = []
                if isinstance(self.source, int):
                    backends = [cv2.CAP_MSMF, cv2.CAP_DSHOW, cv2.CAP_ANY]
                else:
                    backends = [cv2.CAP_ANY]

                for backend in backends:
                    cap = self._try_open_backend(backend)
                    if cap is not None:
                        self.cap = cap
                        break

                if self.cap is None or not self.cap.isOpened():
                    logger.error(f"[THREAD 1] Failed to open camera source: {self.source}")
                    self.is_running = False
                    return False

                actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                reported_fps = self.cap.get(cv2.CAP_PROP_FPS)
                reported_buf = self.cap.get(cv2.CAP_PROP_BUFFERSIZE)
                backend_name = self.cap.getBackendName() if hasattr(self.cap, 'getBackendName') else 'UNKNOWN'

                self.camera_info = {
                    "backend": backend_name,
                    "width": actual_w,
                    "height": actual_h,
                    "fps": reported_fps,
                    "buffersize": reported_buf
                }

                logger.info(f"[THREAD 1] Camera stream started ({backend_name}). Res: {actual_w}x{actual_h}, Reported FPS: {reported_fps}, BUFFERSIZE: {reported_buf}.")

                self.is_running = True
                self._prev_time = time.time()
                self.last_frame_timestamp = time.time()
                self.consecutive_failed_reads = 0

                if self._producer_thread is None or not self._producer_thread.is_alive():
                    self._producer_thread = threading.Thread(target=self._producer_loop, name="CameraProducerThread", daemon=True)
                    self._producer_thread.start()
                return True

            except Exception as e:
                logger.error(f"[THREAD 1] Unhandled error initializing camera: {e}", exc_info=True)
                self.is_running = False
                return False

    def _reconnect_camera(self) -> None:
        """Reconnects camera hardware ONLY during true disconnects or sustained long-term failure."""
        logger.warning("[THREAD 1 WATCHDOG] True camera disconnect or sustained failure detected. Reconnecting hardware...")
        with self._lock:
            try:
                if self.cap is not None:
                    try:
                        self.cap.release()
                    except Exception:
                        pass
                    self.cap = None

                time.sleep(0.5)

                backends = [cv2.CAP_MSMF, cv2.CAP_DSHOW, cv2.CAP_ANY] if isinstance(self.source, int) else [cv2.CAP_ANY]
                for backend in backends:
                    cap = self._try_open_backend(backend)
                    if cap is not None:
                        self.cap = cap
                        break

                if self.cap is not None and self.cap.isOpened():
                    self.consecutive_failed_reads = 0
                    self.last_frame_timestamp = time.time()
                    logger.info("[THREAD 1 WATCHDOG] Camera reconnected successfully.")
                else:
                    logger.error("[THREAD 1 WATCHDOG] Reconnection attempt failed.")
            except Exception as e:
                logger.error(f"[THREAD 1 WATCHDOG] Error during camera reconnection: {e}")

    def _producer_loop(self) -> None:
        logger.info("[THREAD 1] Camera Producer thread loop active (30 FPS target).")
        while self.is_running:
            try:
                if self.cap is None or not self.cap.isOpened():
                    time_since_last = time.time() - self.last_frame_timestamp if self.last_frame_timestamp > 0 else 0.0
                    logger.warning(
                        f"[WATCHDOG] Camera closed/invalid. Time since last frame: {time_since_last:.3f}s | "
                        f"Consecutive failures: {self.consecutive_failed_reads} | Reconnecting..."
                    )
                    self._reconnect_camera()
                    time.sleep(0.5)
                    continue

                frame_id = self.total_frames_captured + 1
                t_start = time.time()
                t1_cap = time.perf_counter()
                log_runtime_debug("CameraProducerThread", "_producer_loop", "[BEFORE_CAMERA_READ]", frame_id, 0.0)

                ret = False
                frame = None
                cap_ref = None
                with self._lock:
                    if self.cap is not None and self.cap.isOpened():
                        cap_ref = self.cap

                if cap_ref is not None:
                    self.last_producer_stage = "CAMERA_BEFORE_READ"
                    t_cap_1 = time.perf_counter()
                    ret, frame = cap_ref.read()
                    t_cap_2 = time.perf_counter()
                    self.last_producer_stage = "CAMERA_AFTER_READ"

                    t2_cap = t_cap_2
                    t_end = time.time()
                    elapsed_ms = (t_end - t_start) * 1000.0
                    t_videocapture_read_ms = (t_cap_2 - t_cap_1) * 1000.0

                if ret and frame is not None:
                    log_runtime_debug("CameraProducerThread", "_producer_loop", "[AFTER_CAMERA_READ]", frame_id, elapsed_ms, "OK", f"shape={frame.shape}")
                    with self._raw_frame_lock:
                        self._latest_raw_frame = frame
                        self._latest_raw_frame_id = frame_id
                    self.consecutive_failed_reads = 0
                    self.total_frames_captured += 1
                    self.camera_read_frame_id = frame_id
                    self.last_camera_success_perf = t2_cap
                    now = time.time()
                    self.last_frame_timestamp = now

                    self._fps_timestamps.append(now)
                    while self._fps_timestamps and self._fps_timestamps[0] < now - 1.0:
                        self._fps_timestamps.popleft()

                    if len(self._fps_timestamps) > 1:
                        elapsed = now - self._fps_timestamps[0]
                        self._current_fps = (len(self._fps_timestamps) - 1) / elapsed if elapsed > 0 else 0.0
                    else:
                        self._current_fps = 0.0

                    t1_qw = time.perf_counter()
                    self.last_producer_stage = "CAMERA_BEFORE_PUBLISH"
                    with self._queue_lock:
                        if self._frame_queue.full():
                            try:
                                self._frame_queue.get_nowait()
                            except queue.Empty:
                                pass
                        t2_qw = time.perf_counter()
                        meta = {
                            "t_capture_start": t1_cap,
                            "t_capture_end": t2_cap,
                            "t_queue_enter": t2_qw,
                            "t1_cap": t1_cap,
                            "t2_cap": t2_cap,
                            "t1_qw": t1_qw,
                            "t2_qw": t2_qw,
                            "frame_id": frame_id,
                            "t_videocapture_read_ms": t_videocapture_read_ms,
                            "producer_fps": round(self._current_fps, 1),
                            "queue_len": 1
                        }
                        self._frame_queue.put_nowait((frame, meta))
                        self.queue_publish_frame_id = frame_id
                        self.last_queue_publish_perf = time.perf_counter()
                        self.last_producer_stage = "CAMERA_AFTER_PUBLISH"

                else:
                    log_runtime_debug("CameraProducerThread", "_producer_loop", "[AFTER_CAMERA_READ]", frame_id, elapsed_ms, "FAIL_RET_FALSE")
                    self.consecutive_failed_reads += 1
                    time.sleep(0.005)

                    now = time.time()
                    time_since_last = now - self.last_frame_timestamp if self.last_frame_timestamp > 0 else 0.0

                    if self.consecutive_failed_reads == 1 or self.consecutive_failed_reads % 50 == 0:
                        logger.warning(
                            f"[WATCHDOG] Temporary cap.read() fail. Time since last frame: {time_since_last:.3f}s | "
                            f"Consecutive failures: {self.consecutive_failed_reads}"
                        )

                    # Only reconnect after true hardware disconnect (150+ consecutive failed reads AND > 15s)
                    if self.consecutive_failed_reads >= 150 and time_since_last >= 15.0:
                        logger.error(
                            f"[WATCHDOG] True camera disconnect detected (150+ failed reads over {time_since_last:.1f}s). Triggering reconnection."
                        )
                        self._reconnect_camera()

            except Exception as e:
                tb_str = traceback.format_exc().replace('\n', ' ')
                log_runtime_debug("CameraProducerThread", "_producer_loop", "[AFTER_CAMERA_READ]", self.total_frames_captured + 1, 0.0, "EXCEPT", tb_str)
                self.consecutive_failed_reads += 1
                logger.error(f"[THREAD 1] Unexpected exception in producer loop: {e}")
                time.sleep(0.05)

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        success, frame, _ = self.read_frame_with_meta()
        return success, frame

    def read_frame_with_meta(self, timeout: float = 0.0) -> Tuple[bool, Optional[np.ndarray], dict]:
        if not self.is_running:
            return False, None, {}

        latest_item = None
        with self._queue_lock:
            while True:
                try:
                    latest_item = self._frame_queue.get_nowait()
                except queue.Empty:
                    break

        if latest_item is None:
            try:
                # If queue is empty right after startup, wait up to 0.05s for first frame
                wait_time = 0.05 if self.total_frames_captured <= 1 else timeout
                if wait_time > 0:
                    latest_item = self._frame_queue.get(block=True, timeout=wait_time)
                else:
                    return False, None, {}
            except queue.Empty:
                return False, None, {}

        frame, meta = latest_item
        return True, frame, meta

    def get_latest_raw_frame(self) -> Tuple[Optional[np.ndarray], int]:
        """
        Thread-safe accessor for the newest raw camera frame and frame ID.
        Provides zero-latency, zero-wait access for the HTTP MJPEG streaming server.
        """
        with self._raw_frame_lock:
            if self._latest_raw_frame is None:
                return None, 0
            return self._latest_raw_frame, self._latest_raw_frame_id

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
            self._producer_thread.join(timeout=2.0)
            self._producer_thread = None

        with self._lock:
            if self.cap is not None:
                try:
                    self.cap.release()
                except Exception as e:
                    logger.warning(f"[THREAD 1] Exception releasing VideoCapture: {e}")
                self.cap = None

        logger.info("[THREAD 1] Camera stream stopped.")

