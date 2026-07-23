"""
Student Drowsiness Detection System - Central Configuration Module

This module centralizes all system settings, camera parameters, AI detection thresholds,
file paths, and alert options. Modifying values in this file adjusts application runtime
behavior without altering underlying core modules.
"""

from pathlib import Path

# ==============================================================================
# 1. BASE DIRECTORIES & FILE PATHS
# ==============================================================================
# Base directory of the repository
BASE_DIR = Path(__file__).resolve().parent

# Core project folders
ASSETS_DIR = BASE_DIR / "assets"
DATASETS_DIR = BASE_DIR / "datasets"
DOCS_DIR = BASE_DIR / "docs"
OUTPUT_DIR = BASE_DIR / "output"

# Sub-directories for outputs and assets
LOGS_DIR = OUTPUT_DIR / "logs"
RECORDINGS_DIR = OUTPUT_DIR / "recordings"
REPORTS_DIR = OUTPUT_DIR / "reports"
MODELS_DIR = ASSETS_DIR / "models"
SOUNDS_DIR = ASSETS_DIR / "sounds"

# Specific file paths
ALARM_SOUND_PATH = SOUNDS_DIR / "alarm.wav"
SESSION_LOG_CSV = LOGS_DIR / "drowsiness_session_log.csv"
FACIAL_LANDMARK_MODEL_PATH = MODELS_DIR / "shape_predictor_68_face_landmarks.dat"
FACE_LANDMARKER_TASK_PATH = MODELS_DIR / "face_landmarker.task"
FACE_LANDMARKER_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
)

# Ensure runtime output directories exist
for directory in [OUTPUT_DIR, LOGS_DIR, RECORDINGS_DIR, REPORTS_DIR, ASSETS_DIR, SOUNDS_DIR, MODELS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# 2. CAMERA & VIDEO STREAM SETTINGS
# ==============================================================================
# Camera device ID (0 for default built-in webcam, 1 for external USB camera, or RTSP stream URL string)
CAMERA_ID = 0

# Video capture frame dimensions (Resolution)
WEBCAM_WIDTH = 640
WEBCAM_HEIGHT = 480

# Target Frames Per Second (FPS) for frame capture loop
TARGET_FPS = 30

# Frame buffer size for smooth video streaming
FRAME_BUFFER_SIZE = 2


# ==============================================================================
# 3. FACIAL LANDMARK INDEX CONFIGURATIONS (MEDIAPIPE FACE MESH)
# ==============================================================================
# 6-Point MediaPipe Face Mesh landmark indices for Eye Aspect Ratio (EAR) computation.
# Points map to [P1 (outer/inner corner), P2 (top-1), P3 (top-2), P4 (inner/outer corner), P5 (bottom-2), P6 (bottom-1)]
RIGHT_EYE_LANDMARK_INDICES = [33, 160, 158, 133, 153, 144]
LEFT_EYE_LANDMARK_INDICES = [362, 385, 387, 263, 373, 380]

# 8-Point MediaPipe Face Mesh landmark indices for Mouth Aspect Ratio (MAR) computation.
# Inner lip points are selected for the ratio computation to measure the actual opening aperture:
# - Right Corner: 78
# - Left Corner: 308
# - Right Vertical Pair: Top = 81, Bottom = 178
# - Center Vertical Pair: Top = 13, Bottom = 14
# - Left Vertical Pair: Top = 311, Bottom = 402
# Contribution:
# Width = ||308 - 78|| (Denominator)
# Height = ||81 - 178|| + ||13 - 14|| + ||311 - 402|| (Numerator)
# MAR Formula: Height / (3.0 * Width)
MOUTH_INNER_LIP_INDICES = [78, 81, 13, 311, 308, 402, 14, 178]

# 8-Point landmarks mapping for the outer lip boundary, used for visual HUD rendering/alignment check:
# - Corners: 61, 291
# - Vertical pairs: (37, 91), (0, 17), (267, 321)
MOUTH_OUTER_LIP_INDICES = [61, 37, 0, 267, 291, 321, 17, 91]

# 6-Point landmarks mapping for Head Pose Estimation (solvePnP):
# - Nose tip: 4
# - Chin: 152
# - Left eye outer corner (subject's left): 263
# - Right eye outer corner (subject's right): 33
# - Left mouth corner (subject's left): 291
# - Right mouth corner (subject's right): 61
HEAD_POSE_LANDMARK_INDICES = [4, 152, 263, 33, 291, 61]


# ==============================================================================
# 4. DETECTION THRESHOLDS (PLACEHOLDER VALUES)
# ==============================================================================
# Eye Aspect Ratio (EAR) threshold below which an eye is considered closed
EAR_THRESHOLD = 0.25

# Number of consecutive frames the eye must be below EAR_THRESHOLD to trigger drowsiness
EAR_CONSECUTIVE_FRAMES = 20

# Minimum and maximum consecutive frames for a valid blink (prevents threshold jitter)
MIN_BLINK_DURATION_FRAMES = 2
MAX_BLINK_DURATION_FRAMES = 15

# Mouth Aspect Ratio (MAR) threshold above which a mouth is considered yawning
MAR_THRESHOLD = 0.60

# Number of consecutive frames the mouth must be open to classify as a yawn
MAR_CONSECUTIVE_FRAMES = 15

# Head Pose Angle thresholds (in degrees) for head nodding / posture detection
HEAD_PITCH_NOD_THRESHOLD = 15.0  # Downward head tilt
HEAD_YAW_SIDE_THRESHOLD = 20.0   # Sideways head turn


# ==============================================================================
# 4. ALERT & ALARM SYSTEM SETTINGS
# ==============================================================================
# Enable / disable audio alarm playback
AUDIO_ALERT_ENABLED = True

# Enable / disable visual alert overlays on camera feed / dashboard
VISUAL_ALERT_ENABLED = True

# Minimum duration (in seconds) that an audio alert plays once triggered
ALERT_DURATION_SECONDS = 3.0

# Alarm volume level (0.0 to 1.0)
ALARM_VOLUME = 0.8


# ==============================================================================
# 5. DASHBOARD & MONITORING SETTINGS
# ==============================================================================
# Streamlit dashboard server host & port
DASHBOARD_HOST = "localhost"
DASHBOARD_PORT = 8501

# Dashboard UI title
DASHBOARD_TITLE = "Student Drowsiness Detection System"

# Dashboard refresh rate (in milliseconds)
DASHBOARD_REFRESH_INTERVAL_MS = 100


# ==============================================================================
# 6. LOGGING & DATA EXPORT SETTINGS
# ==============================================================================
# System logging verbosity level ("DEBUG", "INFO", "WARNING", "ERROR")
LOG_LEVEL = "INFO"

# Enable auto-saving recorded video clips on critical drowsiness events
SAVE_DROWSINESS_CLIPS = True
