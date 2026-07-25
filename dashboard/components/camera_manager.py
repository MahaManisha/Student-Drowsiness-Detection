"""
Student Drowsiness Detection System - Dashboard Camera Manager Component

Stage-by-Stage Diagnostic Instrumentation - Thread 2: AI Worker.
Logs microsecond timing for MediaPipe, EAR, MAR, Head Pose, and Decision Engine into timeline_debug.log.
Does NOT modify any backend AI detection algorithms, math calculators, or thresholds.
"""

import time
import cv2
import datetime
import traceback
import threading
import numpy as np

import config
from typing import Dict, Any, Tuple, Optional
from utils.logger import get_logger

from camera.camera import CameraStream
from detection.face_mesh import FaceMeshDetector
from detection.eye_landmarks import EyeLandmarkExtractor
from detection.mouth_landmark_extractor import MouthLandmarkExtractor
from detection.ear_calculator import EARCalculator
from detection.mar_calculator import MARCalculator
from detection.yawn_detector import YawnDetector
from detection.head_pose_estimator import HeadPoseEstimator
from detection.eye_state_classifier import EyeStateClassifier, EyeState
from detection.temporal_eye_analyzer import TemporalEyeAnalyzer
from detection.drowsiness_decision_engine import StudentDrowsinessDecisionEngine, DrowsinessState
from alerts.alert_manager import AlertManager
from analytics.session_statistics import SessionStatisticsTracker
from dashboard.hud import HUDVisualizer

logger = get_logger(__name__)


def log_timeline_debug(thread_name: str, func_name: str, stage_marker: str, frame_id: int, elapsed_ms: float, status: str = "OK", extra: str = "") -> None:
    """Logs standardized diagnostic entry into timeline_debug.log."""
    try:
        now_str = datetime.datetime.now().isoformat()
        log_line = f"[{now_str}] | [{thread_name}] | [{func_name}] | [{stage_marker}] | Frame: {frame_id} | Elapsed: {elapsed_ms:.3f} ms | Status: {status} {extra}\n"
        with open("timeline_debug.log", "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception:
        pass


class DashboardCameraManager:
    """
    Thread 2: AI Worker Manager with stage-by-stage diagnostic instrumentation.
    """

    def __init__(self) -> None:
        logger.info("[THREAD 2] Initializing DashboardCameraManager with main.py pipeline solvers...")

        self.camera = CameraStream()

        self.detector = FaceMeshDetector()
        self.eye_extractor = EyeLandmarkExtractor()
        self.mouth_extractor = MouthLandmarkExtractor()
        self.ear_calculator = EARCalculator()
        self.mar_calculator = MARCalculator()
        self.yawn_detector = YawnDetector(fps=self.camera.fps_target)
        self.head_pose_estimator = HeadPoseEstimator()
        self.classifier = EyeStateClassifier()
        self.temporal_analyzer = TemporalEyeAnalyzer(
            fps=self.camera.fps_target,
            min_blink_duration=getattr(config, "MIN_BLINK_DURATION_FRAMES", 2),
            max_blink_duration=getattr(config, "MAX_BLINK_DURATION_FRAMES", 15),
        )
        self.decision_engine = StudentDrowsinessDecisionEngine()

        self.alert_manager = AlertManager()
        self.stats_tracker = SessionStatisticsTracker()
        self.visualizer = HUDVisualizer()

        self.start_time: float = time.time()
        self.is_connected: bool = False
        self.last_error: Optional[str] = None
        self.highest_score: float = 0.0
        self.longest_closure: float = 0.0
        self.frame_counter: int = 0

        self._worker_thread: Optional[threading.Thread] = None
        self._worker_running: bool = False
        self._result_lock: threading.Lock = threading.Lock()
        self._latest_rgb_frame: Optional[np.ndarray] = None
        self._latest_telemetry: Dict[str, Any] = self._get_fallback_telemetry()

    def start(self) -> bool:
        try:
            if not self.camera.is_available():
                self.is_connected = False
                self.last_error = "Camera source is unavailable or currently in use by another process."
                logger.warning(f"[THREAD 2] Camera start failed: {self.last_error}")
                return False

            success = self.camera.start()
            if success:
                self.is_connected = True
                self.last_error = None
                self.start_time = time.time()

                self._worker_running = True
                self._worker_thread = threading.Thread(target=self._ai_worker_loop, name="AIWorkerThread", daemon=True)
                self._worker_thread.start()

                logger.info("[THREAD 2] DashboardCameraManager AI Worker thread active.")
                return True
            else:
                self.is_connected = False
                self.last_error = "Failed to initialize OpenCV VideoCapture stream."
                logger.error(f"[THREAD 2] Camera start failed: {self.last_error}")
                return False

        except Exception as e:
            self.is_connected = False
            self.last_error = f"Camera initialization error: {e}"
            logger.error(f"[THREAD 2] Exception during camera start: {self.last_error}", exc_info=True)
            return False

    def _ai_worker_loop(self) -> None:
        logger.info("[THREAD 2] AI Worker loop started.")
        while self._worker_running and self.is_connected:
            ret, frame = self.camera.read_frame()
            if not ret or frame is None:
                time.sleep(0.005)
                continue

            self.frame_counter += 1
            frame_id = self.frame_counter
            h, w = frame.shape[:2]

            try:
                # 1. MediaPipe Face Mesh Diagnostic Stage
                t_mp_start = time.time()
                log_timeline_debug("AIWorkerThread", "_ai_worker_loop", "[BEFORE_MEDIAPIPE]", frame_id, 0.0)
                
                has_face, all_landmarks = self.detector.detect_landmarks(frame)
                
                t_mp_end = time.time()
                log_timeline_debug("AIWorkerThread", "_ai_worker_loop", "[AFTER_MEDIAPIPE]", frame_id, (t_mp_end - t_mp_start) * 1000.0, "OK", f"has_face={has_face}")

                right_ear, left_ear, avg_ear = None, None, None
                right_state, left_state, overall_state = EyeState.UNKNOWN, EyeState.UNKNOWN, EyeState.UNKNOWN
                inner_lip, outer_lip = None, None
                mar_val = None
                pitch, yaw, roll = 0.0, 0.0, 0.0
                pose_valid = False

                if has_face and all_landmarks:
                    face_landmarks = all_landmarks[0]

                    frame = self.detector.draw_landmarks(frame)

                    # Extract Eye landmarks & EAR Diagnostic Stage
                    t_ear_start = time.time()
                    log_timeline_debug("AIWorkerThread", "_ai_worker_loop", "[BEFORE_EAR]", frame_id, 0.0)

                    right_eye, left_eye = self.eye_extractor.extract_eye_landmarks(face_landmarks, frame_shape=frame.shape)
                    frame = self.eye_extractor.draw_eye_landmarks(frame, right_eye, left_eye)
                    right_ear, left_ear, avg_ear = self.ear_calculator.calculate_ear(right_eye, left_eye)
                    right_state, left_state, overall_state = self.classifier.classify_both_eyes(right_ear, left_ear)

                    t_ear_end = time.time()
                    log_timeline_debug("AIWorkerThread", "_ai_worker_loop", "[AFTER_EAR]", frame_id, (t_ear_end - t_ear_start) * 1000.0, "OK", f"avg_ear={avg_ear}")

                    # Extract Mouth landmarks & MAR Diagnostic Stage
                    t_mar_start = time.time()
                    log_timeline_debug("AIWorkerThread", "_ai_worker_loop", "[BEFORE_MAR]", frame_id, 0.0)

                    inner_lip, outer_lip = self.mouth_extractor.extract_mouth_landmarks(face_landmarks, frame_shape=frame.shape)
                    frame = self.mouth_extractor.draw_mouth_landmarks(frame, inner_lip, outer_lip)
                    mar_val = self.mar_calculator.calculate_mar(inner_lip)

                    t_mar_end = time.time()
                    log_timeline_debug("AIWorkerThread", "_ai_worker_loop", "[AFTER_MAR]", frame_id, (t_mar_end - t_mar_start) * 1000.0, "OK", f"mar={mar_val}")

                # Update temporal sequence analyzers
                self.temporal_analyzer.update(
                    right_state=right_state,
                    left_state=left_state,
                    overall_state=overall_state,
                    avg_ear=avg_ear,
                )
                self.yawn_detector.update(mar_val)

                # Head Pose Diagnostic Stage
                t_pose_start = time.time()
                log_timeline_debug("AIWorkerThread", "_ai_worker_loop", "[BEFORE_HEAD_POSE]", frame_id, 0.0)

                pose_result = self.head_pose_estimator.estimate_head_pose(
                    all_landmarks[0] if (has_face and all_landmarks) else None,
                    (h, w)
                )
                if pose_result and pose_result.valid:
                    pitch, yaw, roll = pose_result.pitch, pose_result.yaw, pose_result.roll
                    pose_valid = True

                t_pose_end = time.time()
                log_timeline_debug("AIWorkerThread", "_ai_worker_loop", "[AFTER_HEAD_POSE]", frame_id, (t_pose_end - t_pose_start) * 1000.0, "OK", f"pitch={pitch:.1f}")

                # Decision Engine Diagnostic Stage
                t_dec_start = time.time()
                log_timeline_debug("AIWorkerThread", "_ai_worker_loop", "[BEFORE_DECISION_ENGINE]", frame_id, 0.0)

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
                    "yaw": yaw,
                    "pitch": pitch,
                    "roll": roll,
                    "valid": pose_valid
                }
                decision_metrics = self.decision_engine.update(eye_payload, yawn_payload, pose_payload)
                score_val = decision_metrics.get("drowsiness_score", 0.0)
                state_raw = decision_metrics.get("drowsiness_state", "ALERT")

                t_dec_end = time.time()
                log_timeline_debug("AIWorkerThread", "_ai_worker_loop", "[AFTER_DECISION_ENGINE]", frame_id, (t_dec_end - t_dec_start) * 1000.0, "OK", f"score={score_val}")

                # Alert Manager Process
                drowsiness_result = self.decision_engine.drowsiness_result
                if drowsiness_result is not None:
                    self.alert_manager.process_result(drowsiness_result)

                # Update Session Statistics
                self.highest_score = max(self.highest_score, score_val)
                closed_dur = self.temporal_analyzer.get_closed_duration_seconds()
                self.longest_closure = max(self.longest_closure, closed_dur)

                self.stats_tracker.update(
                    current_state=state_raw,
                    score=score_val,
                    avg_ear=avg_ear,
                    mar=mar_val,
                    blink_count=self.temporal_analyzer.get_blink_count(),
                    yawn_count=self.yawn_detector.get_yawn_count(),
                    closed_duration=closed_dur
                )

                elapsed_seconds = int(time.time() - self.start_time)
                hrs = elapsed_seconds // 3600
                mins = (elapsed_seconds % 3600) // 60
                secs = elapsed_seconds % 60
                session_time_str = f"{hrs:02d}:{mins:02d}:{secs:02d}" if hrs > 0 else f"{mins:02d}:{secs:02d}"

                thresh_val = self.classifier.get_threshold()
                mouth_state_enum = self.yawn_detector.classify_mouth_state(mar_val)
                mouth_state_str = mouth_state_enum.value

                metrics_payload = {
                    "session_time": session_time_str,
                    "fps": self.camera.get_fps(),
                    "drowsiness_state": state_raw,
                    "drowsiness_score": score_val,
                    "confidence": (decision_metrics.get("intermediate_decision") or {}).get("confidence_score", 0.0) * 100.0,
                    "cooccurrence": (decision_metrics.get("intermediate_decision") or {}).get("signal_cooccurrence_count", 0),
                    "explanation": (decision_metrics.get("drowsiness_result") or {}).get("explanation", ""),
                    "blink_count": self.temporal_analyzer.get_blink_count(),
                    "closed_frames": self.temporal_analyzer.get_closed_frame_count(),
                    "closed_time": closed_dur,
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
                        "yaw": yaw,
                        "pitch": pitch,
                        "roll": roll,
                        "valid": pose_valid
                    },
                    "recent_event": self.alert_manager.get_last_event(),
                    "alert_status": "HUD READY | AUDIO READY"
                }

                # Draw OpenCV HUD Overlay onto frame
                frame = self.visualizer.draw(frame, metrics_payload)

                # Single-pass BGR to RGB Conversion
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Telemetry dictionary for Streamlit UI
                telemetry = {
                    "has_face": has_face,
                    "session_time_str": session_time_str,
                    "fps": self.camera.get_fps() if self.camera.get_fps() > 0 else 30.0,
                    "drowsiness_state": state_raw,
                    "left_ear": left_ear,
                    "right_ear": right_ear,
                    "avg_ear": avg_ear,
                    "ear_threshold": thresh_val,
                    "eye_state": overall_state.value if hasattr(overall_state, "value") else (str(overall_state) if has_face else "Searching for Face..."),
                    "blink_count": self.temporal_analyzer.get_blink_count(),
                    "eye_closed_duration": closed_dur,
                    "mar": mar_val,
                    "mar_threshold": self.yawn_detector.mar_threshold if hasattr(self.yawn_detector, "mar_threshold") else 0.60,
                    "mouth_state": mouth_state_str if has_face else "Searching for Face...",
                    "yawn_count": self.yawn_detector.get_yawn_count(),
                    "mouth_open_duration": self.yawn_detector.get_open_duration_seconds(),
                    "head_pose_pitch": pitch,
                    "head_pose_yaw": yaw,
                    "head_pose_roll": roll,
                    "head_pose_valid": pose_valid,
                    "drowsiness_score": score_val,
                    "decision_confidence": (decision_metrics.get("intermediate_decision") or {}).get("confidence_score", 0.98) * 100.0,
                    "co_occurrences": {
                        "EYE": closed_dur > 0,
                        "MOUTH": self.yawn_detector.get_open_duration_seconds() > 0,
                        "POSE": abs(pitch) > 15.0 or abs(yaw) > 20.0
                    },
                    "decision_reason": (decision_metrics.get("drowsiness_result") or {}).get("explanation", "System monitoring active."),
                    "current_message": "System operating normally.",
                    "current_severity": "critical" if state_raw == "DROWSY" else ("warning" if state_raw in ["SLIGHTLY_DROWSY", "UNWATCHFUL"] else "subtle"),
                    "last_alert_time": "--:--:--",
                    "previous_message": "No active alerts recorded.",
                    "audio_enabled": True,
                    "audio_status": "READY",
                    "session_stats": self.stats_tracker.get_stats(),
                    "events": self.alert_manager.event_log
                }

                # Publish Atomic Result Payload under Mutex Lock
                with self._result_lock:
                    self._latest_rgb_frame = rgb_frame
                    self._latest_telemetry = telemetry

            except Exception as e:
                tb_str = traceback.format_exc().replace('\n', ' ')
                log_timeline_debug("AIWorkerThread", "_ai_worker_loop", "[WORKER_LOOP]", frame_id, 0.0, "EXCEPT", tb_str)
                logger.error(f"[THREAD 2] Error in AI worker loop: {e}", exc_info=True)

    def get_processed_frame(self) -> Tuple[bool, Optional[np.ndarray], Dict[str, Any]]:
        if not self.is_connected:
            return False, None, self._get_fallback_telemetry()

        with self._result_lock:
            if self._latest_rgb_frame is not None:
                return True, self._latest_rgb_frame.copy(), self._latest_telemetry.copy()
            return False, None, self._latest_telemetry.copy()

    def _get_fallback_telemetry(self) -> Dict[str, Any]:
        return {
            "has_face": False,
            "session_time_str": "00:00",
            "fps": 0.0,
            "drowsiness_state": "ALERT",
            "left_ear": None,
            "right_ear": None,
            "avg_ear": None,
            "ear_threshold": 0.25,
            "eye_state": "Searching for Face...",
            "blink_count": 0,
            "eye_closed_duration": None,
            "mar": None,
            "mar_threshold": 0.60,
            "mouth_state": "Searching for Face...",
            "yawn_count": 0,
            "mouth_open_duration": None,
            "head_pose_pitch": None,
            "head_pose_yaw": None,
            "head_pose_roll": None,
            "head_pose_valid": False,
            "drowsiness_score": 0.0,
            "decision_confidence": 0.0,
            "co_occurrences": {"EYE": False, "MOUTH": False, "POSE": False},
            "decision_reason": "Searching for Face...",
            "current_message": "Searching for Face...",
            "current_severity": "subtle",
            "last_alert_time": "--:--:--",
            "previous_message": "No face detected in viewport.",
            "audio_enabled": True,
            "audio_status": "MUTED",
            "session_stats": {
                "total_session_time": "00:00",
                "blink_count": 0,
                "yawn_count": 0,
                "average_ear": 0.0,
                "average_mar": 0.0,
                "highest_score": 0.0,
                "longest_eye_closure": 0.0,
                "time_in_alert": "00:00:00 (0.0%)",
                "time_in_drowsy": "00:00:00 (0.0%)"
            },
            "events": []
        }

    def stop(self) -> None:
        logger.info("[THREAD 2] Stopping AI Worker thread...")
        self._worker_running = False

        if self._worker_thread is not None and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)

        self.camera.stop()
        logger.info("[THREAD 2] DashboardCameraManager stopped.")
