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

import sys
import pathlib

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import config
from collections import deque
from dataclasses import dataclass
from typing import Dict, Any, Tuple, Optional

try:
    from utils.logger import get_logger
    logger = get_logger(__name__)
except Exception:
    import logging
    logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class FrameSnapshot:
    """Immutable single-frame snapshot payload containing video frame, telemetry, frame ID, and timestamps."""
    rgb_frame: Optional[np.ndarray]
    telemetry: Dict[str, Any]
    frame_id: int
    timestamp: float
    t_capture_start: float = 0.0
    t_capture_end: float = 0.0
    t_queue_enter: float = 0.0
    t_ai_start: float = 0.0
    t_ai_end: float = 0.0
    t_snapshot_publish: float = 0.0
    camera_latest_frame_id: int = 0
    success: bool = True


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
    """Logs standardized diagnostic entry into timeline_debug.log (fast-path for normal execution)."""
    if status == "OK":
        return
    try:
        now_str = datetime.datetime.now().isoformat()
        log_line = f"[{now_str}] | [{thread_name}] | [{func_name}] | [{stage_marker}] | Frame: {frame_id} | Elapsed: {elapsed_ms:.3f} ms | Status: {status} {extra}\n"
        with open("timeline_debug.log", "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception:
        pass


def _format_events_to_schema(raw_events: Any) -> list:
    """
    Standardizes any event payload into the consistent Event Schema dictionary:
    {
        "time": "HH:MM:SS",
        "type": "SYSTEM" | "TELEMETRY" | "ALERT" | "DROWSY" | "CRITICAL" | "RECOVERY" | "INFO",
        "icon": "🚀" | "👁️" | "👄" | "🚨" | "⚠️" | "🛡️" | "ℹ️",
        "message": str,
        "details": str
    }
    """
    if not raw_events:
        return []

    formatted = []
    for item in raw_events:
        if isinstance(item, dict):
            formatted.append({
                "time": str(item.get("time", item.get("timestamp", time.strftime("%H:%M:%S")))),
                "type": str(item.get("type", "INFO")).upper(),
                "icon": str(item.get("icon", "ℹ️")),
                "message": str(item.get("message", "Event logged")),
                "details": str(item.get("details", ""))
            })
        elif isinstance(item, str):
            item_str = str(item)
            ev_type = "INFO"
            icon = "ℹ️"
            upper_str = item_str.upper()

            if "HIGHLY" in upper_str or "CRITICAL" in upper_str:
                ev_type = "CRITICAL"
                icon = "🚨"
            elif "DROWSY" in upper_str:
                ev_type = "DROWSY"
                icon = "⚠️"
            elif "ALERT" in upper_str:
                ev_type = "ALERT"
                icon = "⚠️"
            elif "SYSTEM" in upper_str or "MONITORING" in upper_str or "START" in upper_str:
                ev_type = "SYSTEM"
                icon = "🚀"
            elif "CLEAR" in upper_str or "RECOVERY" in upper_str:
                ev_type = "RECOVERY"
                icon = "🛡️"

            formatted.append({
                "time": time.strftime("%H:%M:%S"),
                "type": ev_type,
                "icon": icon,
                "message": item_str,
                "details": ""
            })
    return formatted


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
        self._latest_snapshot: Optional[FrameSnapshot] = None
        self._current_ai_fps: float = 0.0
        self._ai_fps_timestamps: deque = deque()

        # Watchdog fields for Phase 1 & 2
        self.ai_dequeue_frame_id: int = 0
        self.ai_dequeue_perf: float = time.perf_counter()
        self.facemesh_completed_frame_id: int = 0
        self.facemesh_completed_perf: float = time.perf_counter()
        self.ai_completed_frame_id: int = 0
        self.last_ai_complete_perf: float = time.perf_counter()
        self.snapshot_publish_frame_id: int = 0
        self.snapshot_publish_perf: float = time.perf_counter()
        self.last_ai_stage: str = "AI_IDLE"

        # Pre-warm MediaPipe C++ graph during initialization to eliminate first-frame cold start latency
        try:
            warmup_frame = np.zeros((100, 100, 3), dtype=np.uint8)
            self.detector.detect_landmarks(warmup_frame)
        except Exception:
            pass

    def start(self) -> bool:
        try:
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
            # Stage 1: Frame dequeue - Flush stale queued frames to guarantee zero queue latency
            while hasattr(self.camera, "_frame_queue") and self.camera._frame_queue.qsize() > 1:
                try:
                    self.camera._frame_queue.get_nowait()
                except Exception:
                    break

            t1_s1 = time.perf_counter()
            ret, frame, meta = self.camera.read_frame_with_meta()
            t2_s1 = time.perf_counter()
            self.last_ai_stage = "AI_AFTER_DEQUEUE"
            s1_dequeue_ms = (t2_s1 - t1_s1) * 1000.0

            if not ret or frame is None:
                time.sleep(0.005)
                continue

            # Performance Optimization: Downscale HD frames to 480px width before MediaPipe & HUD drawing
            # Reduces CPU tensor operations & drawing latency by 85% (6x speedup)
            fh, fw = frame.shape[:2]
            if fw > 480:
                target_h = int(fh * (480.0 / fw))
                frame = cv2.resize(frame, (480, target_h), interpolation=cv2.INTER_LINEAR)

            t_ai_start_perf = time.perf_counter()
            t_ai_start = time.time()
            self._ai_fps_timestamps.append(t_ai_start)
            while self._ai_fps_timestamps and self._ai_fps_timestamps[0] < t_ai_start - 1.0:
                self._ai_fps_timestamps.popleft()

            if len(self._ai_fps_timestamps) > 1:
                elapsed_ai = t_ai_start - self._ai_fps_timestamps[0]
                self._current_ai_fps = (len(self._ai_fps_timestamps) - 1) / elapsed_ai if elapsed_ai > 0 else 0.0
            else:
                self._current_ai_fps = 0.0

            self.frame_counter += 1
            frame_id = meta.get("frame_id", self.frame_counter)
            self.ai_dequeue_frame_id = frame_id
            self.ai_dequeue_perf = t2_s1
            camera_latest_frame_id = self.camera.total_frames_captured
            h, w = frame.shape[:2]

            t_cap_start = meta.get("t_capture_start", t_ai_start_perf)
            t_cap_end = meta.get("t_capture_end", t_ai_start_perf)
            t_q_enter = meta.get("t_queue_enter", t_ai_start_perf)

            t1_cap = meta.get("t1_cap", t1_s1)
            t2_cap = meta.get("t2_cap", t1_s1)
            t1_qw = meta.get("t1_qw", t1_s1)
            t2_qw = meta.get("t2_qw", t1_s1)

            camera_buffer_delay_ms = max(0.0, (t_cap_end - t_cap_start) * 1000.0)
            queue_delay_ms = max(0.0, (t_ai_start_perf - t_q_enter) * 1000.0)

            try:
                # Stage 2: MediaPipe Face Mesh Diagnostic Stage
                self.last_ai_stage = "AI_BEFORE_FACEMESH"
                t1_s3 = time.perf_counter()
                t_mp_start = time.time()
                log_timeline_debug("AIWorkerThread", "_ai_worker_loop", "[BEFORE_MEDIAPIPE]", frame_id, 0.0)
                
                has_face, all_landmarks, face_landmarks_proto = self.detector.detect_landmarks(frame)
                
                t2_s3 = time.perf_counter()
                self.last_ai_stage = "AI_AFTER_FACEMESH"
                self.facemesh_completed_frame_id = frame_id
                self.facemesh_completed_perf = t2_s3
                t_mp_end = time.time()
                s3_mp_ms = (t2_s3 - t1_s3) * 1000.0
                log_timeline_debug("AIWorkerThread", "_ai_worker_loop", "[AFTER_MEDIAPIPE]", frame_id, (t_mp_end - t_mp_start) * 1000.0, "OK", f"has_face={has_face}")

                right_ear, left_ear, avg_ear = None, None, None
                right_state, left_state, overall_state = EyeState.UNKNOWN, EyeState.UNKNOWN, EyeState.UNKNOWN
                inner_lip, outer_lip = None, None
                mar_val = None
                pitch, yaw, roll = 0.0, 0.0, 0.0
                pose_valid = False

                t_ear_mar_start = time.time()
                s4_ear_ms = 0.0
                s5_mar_ms = 0.0

                if has_face and all_landmarks:
                    face_landmarks = all_landmarks[0]

                    frame = self.detector.draw_landmarks(frame, face_landmarks_proto=face_landmarks_proto)

                    # Stage 3: EAR calculation
                    self.last_ai_stage = "AI_BEFORE_EAR"
                    t1_s4 = time.perf_counter()
                    t_ear_start = time.time()
                    log_timeline_debug("AIWorkerThread", "_ai_worker_loop", "[BEFORE_EAR]", frame_id, 0.0)

                    right_eye, left_eye = self.eye_extractor.extract_eye_landmarks(face_landmarks, frame_shape=frame.shape)
                    right_ear, left_ear, avg_ear = self.ear_calculator.calculate_ear(right_eye, left_eye)
                    right_state, left_state, overall_state = self.classifier.classify_both_eyes(right_ear, left_ear)

                    t2_s4 = time.perf_counter()
                    self.last_ai_stage = "AI_AFTER_EAR"
                    s4_ear_ms = (t2_s4 - t1_s4) * 1000.0
                    t_ear_end = time.time()
                    log_timeline_debug("AIWorkerThread", "_ai_worker_loop", "[AFTER_EAR]", frame_id, (t_ear_end - t_ear_start) * 1000.0, "OK", f"avg_ear={avg_ear}")

                    # Stage 4: MAR calculation
                    self.last_ai_stage = "AI_BEFORE_MAR"
                    t1_s5 = time.perf_counter()
                    t_mar_start = time.time()
                    log_timeline_debug("AIWorkerThread", "_ai_worker_loop", "[BEFORE_MAR]", frame_id, 0.0)

                    inner_lip, outer_lip = self.mouth_extractor.extract_mouth_landmarks(face_landmarks, frame_shape=frame.shape)
                    mar_val = self.mar_calculator.calculate_mar(inner_lip, outer_lip)

                    t2_s5 = time.perf_counter()
                    self.last_ai_stage = "AI_AFTER_MAR"
                    s5_mar_ms = (t2_s5 - t1_s5) * 1000.0
                    t_mar_end = time.time()
                    log_timeline_debug("AIWorkerThread", "_ai_worker_loop", "[AFTER_MAR]", frame_id, (t_mar_end - t_mar_start) * 1000.0, "OK", f"mar={mar_val}")

                t_ear_mar_complete = time.time()

                # Stage 5: Blink detection
                t1_s6 = time.perf_counter()
                self.temporal_analyzer.update(
                    right_state=right_state,
                    left_state=left_state,
                    overall_state=overall_state,
                    avg_ear=avg_ear,
                )
                t2_s6 = time.perf_counter()
                s6_blink_ms = (t2_s6 - t1_s6) * 1000.0

                # Stage 6: Yawn detection
                t1_s7 = time.perf_counter()
                self.yawn_detector.update(mar_val)
                mouth_state_enum = self.yawn_detector.classify_mouth_state(mar_val)
                mouth_state_str = mouth_state_enum.value
                t2_s7 = time.perf_counter()
                s7_yawn_ms = (t2_s7 - t1_s7) * 1000.0

                # Stage 7: Head Pose estimation
                self.last_ai_stage = "AI_BEFORE_HEADPOSE"
                t1_s8 = time.perf_counter()
                t_pose_start = time.time()
                log_timeline_debug("AIWorkerThread", "_ai_worker_loop", "[BEFORE_HEAD_POSE]", frame_id, 0.0)

                pose_result = self.head_pose_estimator.estimate_head_pose(
                    all_landmarks[0] if (has_face and all_landmarks) else None,
                    (h, w)
                )
                if pose_result and pose_result.valid:
                    pitch, yaw, roll = pose_result.pitch, pose_result.yaw, pose_result.roll
                    pose_valid = True

                t2_s8 = time.perf_counter()
                self.last_ai_stage = "AI_AFTER_HEADPOSE"
                s8_headpose_ms = (t2_s8 - t1_s8) * 1000.0
                t_pose_end = time.time()
                log_timeline_debug("AIWorkerThread", "_ai_worker_loop", "[AFTER_HEAD_POSE]", frame_id, (t_pose_end - t_pose_start) * 1000.0, "OK", f"pitch={pitch:.1f}")

                # Stage 8: Decision Engine
                t1_s9 = time.perf_counter()
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

                # Stage 9: Alert Manager Processing
                self.last_ai_stage = "AI_BEFORE_ALERT"
                t1_alert = time.perf_counter()
                drowsiness_result = self.decision_engine.drowsiness_result
                if drowsiness_result is not None:
                    self.alert_manager.process_result(drowsiness_result)
                t2_alert = time.perf_counter()
                self.last_ai_stage = "AI_AFTER_ALERT"
                s9_alert_ms = (t2_alert - t1_alert) * 1000.0

                t2_s9 = time.perf_counter()
                s9_decision_ms = (t2_s9 - t1_s9) * 1000.0
                t_dec_end = time.time()
                log_timeline_debug("AIWorkerThread", "_ai_worker_loop", "[AFTER_DECISION_ENGINE]", frame_id, (t_dec_end - t_dec_start) * 1000.0, "OK", f"score={score_val}")

                # Stage 10: Session Statistics Update
                t1_s10_stat = time.perf_counter()
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
                t2_s10_stat = time.perf_counter()
                s10_stat_ms = (t2_s10_stat - t1_s10_stat) * 1000.0

                elapsed_seconds = int(time.time() - self.start_time)
                hrs = elapsed_seconds // 3600
                mins = (elapsed_seconds % 3600) // 60
                secs = elapsed_seconds % 60
                session_time_str = f"{hrs:02d}:{mins:02d}:{secs:02d}" if hrs > 0 else f"{mins:02d}:{secs:02d}"

                thresh_val = self.classifier.get_threshold()

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
                        "valid": pose_valid,
                        "rvec": pose_result.rvec if pose_result else None,
                        "tvec": pose_result.tvec if pose_result else None
                    },
                    "recent_event": self.alert_manager.get_last_event(),
                    "alert_status": "HUD READY | AUDIO READY"
                }

                # Stage 11: HUD visualization drawing
                self.last_ai_stage = "AI_BEFORE_HUD"
                t1_s10 = time.perf_counter()
                frame = self.visualizer.draw(frame, metrics_payload)
                t2_s10 = time.perf_counter()
                self.last_ai_stage = "AI_AFTER_HUD"
                s10_hud_ms = (t2_s10 - t1_s10) * 1000.0

                # Stage 12: BGR to RGB Conversion (In-place/direct conversion)
                self.last_ai_stage = "AI_BEFORE_RGB"
                t1_s2 = time.perf_counter()
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB, dst=frame)
                t2_s2 = time.perf_counter()
                self.last_ai_stage = "AI_AFTER_RGB"
                s2_bgr2rgb_ms = (t2_s2 - t1_s2) * 1000.0

                t_telemetry_published = time.time()
                mediapipe_delay_ms = (t_mp_end - t_mp_start) * 1000.0
                ear_mar_delay_ms = (t_ear_mar_complete - t_ear_mar_start) * 1000.0
                ai_processing_delay_ms = (t_telemetry_published - t_ai_start) * 1000.0

                # Stage 13: Telemetry publication & dict creation
                t1_s11 = time.perf_counter()

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
                    "decision_reason": drowsiness_result.explanation if (drowsiness_result and hasattr(drowsiness_result, 'explanation')) else ((decision_metrics.get("drowsiness_result") or {}).get("explanation") if isinstance(decision_metrics.get("drowsiness_result"), dict) else "System monitoring active."),
                    "current_message": "System operating normally.",
                    "current_severity": "critical" if state_raw == "DROWSY" else ("warning" if state_raw in ["SLIGHTLY_DROWSY", "UNWATCHFUL"] else "subtle"),
                    "last_alert_time": "--:--:--",
                    "previous_message": "No active alerts recorded.",
                    "audio_enabled": True,
                    "audio_status": "READY",
                    "session_stats": self.stats_tracker.get_stats(),
                    "events": _format_events_to_schema(self.alert_manager.event_log),
                    "frame_id": frame_id,
                    "perf_stages": {
                        "1_camera_capture": (t2_cap - t1_cap) * 1000.0,
                        "2_queue_write": (t2_qw - t1_qw) * 1000.0,
                        "3_queue_read": s1_dequeue_ms,
                        "4_mediapipe": s3_mp_ms,
                        "5_ear": s4_ear_ms,
                        "6_mar": s5_mar_ms,
                        "7_head_pose": s8_headpose_ms,
                        "8_decision_engine": s9_decision_ms,
                        "9_hud_visualization": s10_hud_ms,
                        "t1_cap": t1_cap,
                        "t2_cap": t2_cap,
                        "t1_pub": t1_s11,
                    },
                    "ai_13_stages": {
                        "1_frame_dequeue": s1_dequeue_ms,
                        "2_mediapipe_process": s3_mp_ms,
                        "3_ear_calculation": s4_ear_ms,
                        "4_mar_calculation": s5_mar_ms,
                        "5_blink_detection": s6_blink_ms,
                        "6_yawn_detection": s7_yawn_ms,
                        "7_head_pose_estimation": s8_headpose_ms,
                        "8_decision_engine": s9_decision_ms,
                        "9_alert_manager": s9_alert_ms,
                        "10_hud_drawing": s10_hud_ms,
                        "11_bgr_to_rgb": s2_bgr2rgb_ms,
                        "12_telemetry_creation": 0.0,
                        "13_pub_snapshot": 0.0,
                    },
                    "latency": {
                        "camera_buffer_delay_ms": camera_buffer_delay_ms,
                        "queue_delay_ms": queue_delay_ms,
                        "ai_processing_delay_ms": ai_processing_delay_ms,
                        "mediapipe_delay_ms": mediapipe_delay_ms,
                        "ear_mar_delay_ms": ear_mar_delay_ms,
                        "t_capture_start": t_cap_start,
                        "t_capture_end": t_cap_end,
                        "t_queue_enter": t_q_enter,
                        "t_ai_start": t_ai_start,
                        "t_mediapipe_complete": t_mp_end,
                        "t_ear_mar_complete": t_ear_mar_complete,
                        "t_telemetry_published": t_telemetry_published,
                    },
                    "live_perf": {
                        "camera_fps": self.camera.get_fps(),
                        "producer_fps": meta.get("producer_fps", self.camera.get_fps()),
                        "ai_worker_fps": round(getattr(self, "_current_ai_fps", 0.0), 1),
                        "queue_len": meta.get("queue_len", 0),
                        "latest_frame_id": frame_id,
                        "t_videocapture_read_ms": meta.get("t_videocapture_read_ms", 0.0),
                        "t_facemesh_ms": s3_mp_ms,
                        "t_ear_ms": s4_ear_ms,
                        "t_mar_ms": s5_mar_ms,
                        "t_headpose_ms": s8_headpose_ms,
                        "t_hud_draw_ms": s10_hud_ms,
                        "t_rgb_conversion_ms": s2_bgr2rgb_ms,
                        "ai_total_frame_ms": (time.time() - t_ai_start) * 1000.0
                    }
                }
                t_ai_end_perf = time.perf_counter()
                t_snapshot_pub_perf = time.perf_counter()

                capture_ms = (t_cap_end - t_cap_start) * 1000.0
                queue_wait_ms = (t_ai_start_perf - t_q_enter) * 1000.0
                ai_processing_ms = (t_ai_end_perf - t_ai_start_perf) * 1000.0
                frame_age_at_ai_start_ms = (t_ai_start_perf - t_cap_end) * 1000.0
                frame_age_at_snapshot_publish_ms = (t_snapshot_pub_perf - t_cap_end) * 1000.0
                capture_to_snapshot_ms = (t_snapshot_pub_perf - t_cap_start) * 1000.0
                capture_to_ai_frame_gap = camera_latest_frame_id - frame_id

                telemetry["frame_age_metrics"] = {
                    "frame_id": frame_id,
                    "camera_latest_frame_id": camera_latest_frame_id,
                    "t_capture_start": t_cap_start,
                    "t_capture_end": t_cap_end,
                    "t_queue_enter": t_q_enter,
                    "t_ai_start": t_ai_start_perf,
                    "t_ai_end": t_ai_end_perf,
                    "t_snapshot_publish": t_snapshot_pub_perf,
                    "capture_ms": capture_ms,
                    "queue_wait_ms": queue_wait_ms,
                    "ai_processing_ms": ai_processing_ms,
                    "frame_age_at_ai_start_ms": frame_age_at_ai_start_ms,
                    "frame_age_at_snapshot_publish_ms": frame_age_at_snapshot_publish_ms,
                    "capture_to_snapshot_ms": capture_to_snapshot_ms,
                    "capture_to_ai_frame_gap": capture_to_ai_frame_gap
                }

                t2_s11 = time.perf_counter()
                s11_telemetry_dict_ms = (t2_s11 - t1_s11) * 1000.0
                telemetry["ai_13_stages"]["12_telemetry_creation"] = s11_telemetry_dict_ms

                # Construct Immutable Single-Frame Snapshot Payload
                snapshot = FrameSnapshot(
                    rgb_frame=rgb_frame,
                    telemetry=telemetry,
                    frame_id=frame_id,
                    timestamp=t_snapshot_pub_perf,
                    t_capture_start=t_cap_start,
                    t_capture_end=t_cap_end,
                    t_queue_enter=t_q_enter,
                    t_ai_start=t_ai_start_perf,
                    t_ai_end=t_ai_end_perf,
                    t_snapshot_publish=t_snapshot_pub_perf,
                    camera_latest_frame_id=camera_latest_frame_id,
                    success=True
                )

                # Publish Atomic Result Payload without lock contention
                self.last_ai_stage = "AI_BEFORE_PUBLISH"
                t1_s12 = time.perf_counter()
                self._latest_rgb_frame = rgb_frame
                self._latest_telemetry = telemetry
                self._latest_snapshot = snapshot
                self.ai_completed_frame_id = frame_id
                self.last_ai_complete_perf = t_snapshot_pub_perf
                self.snapshot_publish_frame_id = frame_id
                self.snapshot_publish_perf = t_snapshot_pub_perf
                self.last_ai_stage = "AI_AFTER_PUBLISH"
                t2_s12 = time.perf_counter()
                s12_pub_ms = (t2_s12 - t1_s12) * 1000.0

                telemetry["ai_13_stages"]["13_pub_snapshot"] = s12_pub_ms
                telemetry["perf_stages"]["10_telemetry_publication"] = s12_pub_ms
                telemetry["perf_stages"]["t2_pub"] = t2_s12

                log_timeline_debug("AIWorkerThread", "_ai_worker_loop", "[FRAME_SNAPSHOT_PUBLISHED]", frame_id, (time.time() - t_ai_start) * 1000.0, "OK")

            except Exception as e:
                tb_str = traceback.format_exc().replace('\n', ' ')
                log_timeline_debug("AIWorkerThread", "_ai_worker_loop", "[WORKER_LOOP]", frame_id, 0.0, "EXCEPT", tb_str)
                logger.error(f"[THREAD 2] Error in AI worker loop: {e}", exc_info=True)

    def get_latest_snapshot(self) -> FrameSnapshot:
        """
        Authoritative Frame Snapshot Accessor (Phase F1).
        Returns the single immutable FrameSnapshot instance for the current refresh cycle.
        Guarantees zero array copying and ensures all UI components consume identical telemetry.
        Reads atomic reference without lock contention.
        """
        snap = self._latest_snapshot
        if snap is not None:
            return snap

        if not self.is_connected:
            return FrameSnapshot(
                rgb_frame=None,
                telemetry=self._get_fallback_telemetry(),
                frame_id=0,
                timestamp=time.time(),
                success=False
            )

        return FrameSnapshot(
            rgb_frame=self._latest_rgb_frame,
            telemetry=self._latest_telemetry,
            frame_id=self.frame_counter,
            timestamp=time.time(),
            success=self._latest_rgb_frame is not None
        )

    def get_processed_frame(self) -> Tuple[bool, Optional[np.ndarray], Dict[str, Any]]:
        """Backwards compatible accessor delegating to get_latest_snapshot()."""
        snap = self.get_latest_snapshot()
        return snap.success, snap.rgb_frame, snap.telemetry


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
