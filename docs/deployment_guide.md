# 🚀 Student Drowsiness Detection System: Production Deployment & Operations Guide

## 1. System Overview

This guide details the procedure for deploying, configuring, and operating the **Student Drowsiness Detection System** in production educational environments, testing centers, or remote study stations.

---

## 2. Hardware & Operating System Requirements

### 2.1 Hardware Specifications
* **CPU**: Dual-core $2.0 \text{ GHz}$ or higher (Intel Core i3/i5/i7 or AMD Ryzen series).
* **RAM**: $4 \text{ GB}$ minimum ($8 \text{ GB}$ recommended).
* **Camera**: USB Webcam or integrated built-in laptop camera supporting minimum $640 \times 480$ resolution @ $30 \text{ FPS}$.
* **Audio Output**: Internal speakers or connected headphones for audio alarm alerts.

### 2.2 Supported Operating Systems
* **Windows**: Windows 10 / Windows 11 (64-bit).
* **Linux**: Ubuntu 20.04 / 22.04 LTS (64-bit).
* **macOS**: macOS 12 Monterey or higher (Apple Silicon / Intel).

---

## 3. Environment & Dependency Installation

### Step 1: Clone Repository
```bash
git clone https://github.com/MahaManisha/Student-Drowsiness-Detection.git
cd Student-Drowsiness-Detection
```

### Step 2: Create Python Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install --upgrade pip
pip install opencv-python mediapipe numpy scipy pytest
```
*Optional Audio Playback Package*:
```bash
pip install playsound
```

---

## 4. System Configuration Guide (`config.py`)

All operational settings, hardware IDs, thresholds, and alert options are centralized in [config.py](file:///c:/Users/Maha%20Monisha/OneDrive/Desktop/Triton%20Labs/Student-Drowsiness-Detection/config.py):

| Parameter | Default Value | Description |
| :--- | :--- | :--- |
| **`CAMERA_ID`** | `0` | Camera device index (`0` for default webcam, `1` for secondary USB camera). |
| **`WEBCAM_WIDTH`** | `640` | Video frame capture width in pixels. |
| **`WEBCAM_HEIGHT`** | `480` | Video frame capture height in pixels. |
| **`TARGET_FPS`** | `30` | Target frame processing throughput rate. |
| **`EAR_THRESHOLD`** | `0.25` | Eye Aspect Ratio threshold below which eye is classified closed. |
| **`MAR_THRESHOLD`** | `0.60` | Mouth Aspect Ratio threshold above which mouth is classified open. |
| **`HEAD_PITCH_NOD_THRESHOLD`** | `15.0` | Head downward tilt angle threshold in degrees. |
| **`AUDIO_ALERT_ENABLED`** | `True` | Master toggle for audible alarm playback. |
| **`VISUAL_ALERT_ENABLED`** | `True` | Master toggle for HUD warning overlays. |
| **`ALERT_COOLDOWN_SECONDS`** | `5.0` | Cooldown period in seconds to suppress duplicate alerts. |

---

## 5. Running the Application

### 5.1 Main Real-Time Application
Launch the central coordinator processing loop:
```bash
python main.py
```

* **Keyboard Controls**:
  - Press `'q'` or `ESC` on the preview video window to initiate a graceful shutdown.

---

## 6. Automated Testing & Verification

Run the full automated test suite before deployment:
```bash
pytest
```
*All 87 tests across 14 modules must pass with exit code 0.*

---

## 7. Output Logs & Session Reports

Upon graceful shutdown, the system automatically exports:
1. **JSON Event Log**: [output/logs/drowsiness_session_log.json](file:///c:/Users/Maha%20Monisha/OneDrive/Desktop/Triton%20Labs/Student-Drowsiness-Detection/output/logs/drowsiness_session_log.json)
2. **Session Statistics**: [output/reports/session_statistics.json](file:///c:/Users/Maha%20Monisha/OneDrive/Desktop/Triton%20Labs/Student-Drowsiness-Detection/output/reports/session_statistics.json)
3. **Markdown Session Summary**: [output/reports/session_summary_report.md](file:///c:/Users/Maha%20Monisha/OneDrive/Desktop/Triton%20Labs/Student-Drowsiness-Detection/output/reports/session_summary_report.md)

---

## 8. Troubleshooting & Maintenance

* **Problem: Camera fails to open.**
  - *Fix*: Check camera USB connection or privacy permissions. Verify `CAMERA_ID` in `config.py`.
* **Problem: Audio alarm silent on critical state.**
  - *Fix*: Ensure `AUDIO_ALERT_ENABLED = True` in `config.py` and verify `assets/sounds/alarm.wav` exists.
* **Problem: `AttributeError: module 'mediapipe' has no attribute 'solutions'`**
  - *Fix*: Ensure latest `mediapipe` version is installed (`pip install --upgrade mediapipe`).
