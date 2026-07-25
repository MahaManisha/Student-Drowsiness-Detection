# ⚙️ Student Drowsiness Detection System: Settings & Configuration Guide (Phase S9)

## 1. Executive Summary & Objective

Phase S9 introduces the **Settings, Configuration & About Center** to the **Streamlit Web Dashboard**, allowing users to configure UI preferences, camera selection, alert notification volumes, and inspect system hardware diagnostics without modifying any backend AI detection logic.

As strictly mandated, the **AI backend detection engine (`detection/`, `analytics/`, `alerts/`, `camera/`, `logging/`, `models/`, `utils/`) remains 100% untouched and protected**.

---

## 2. Technical Architecture & Persistent State

```
[User UI Preference Toggles]
            │
            ▼
[ConfigurationManager.get_config()] ──► [st.session_state.app_config]
            │
            ├───────────────────────┬───────────────────────┐
            ▼                       ▼                       ▼
   [General Settings]       [Camera Settings]       [Alert Settings]
   - Refresh FPS (30)       - Device Index (0)      - Audio Mute / Audible
   - Time Format (24H)      - Resolution (1280x720) - Volume (80%)
            │                       │                       │
            ├───────────────────────┴───────────────────────┘
            ▼
   [Display & System Info Diagnostics]
   - Dark Mode / Zoom / Show FPS
   - Python, Streamlit, OpenCV, MediaPipe, OS, CPU, RAM
```

---

## 3. Configuration Categories Reference

| Section | User Preference Key | Description | Scope |
| :--- | :--- | :--- | :--- |
| **General** | `config["refresh_fps"]` | Target UI refresh frame rate slider ($15 \to 60\text{ FPS}$) | UI rendering loop |
| **General** | `config["time_format"]` | Timestamps display format (`24 Hour` / `12 Hour`) | Display formatting |
| **General** | `config["default_page"]` | Default landing page route | Sidebar default |
| **Camera** | `config["camera_id"]` | WebCam device index selector | Video capture source |
| **Camera** | `config["resolution"]` | Frame preview scale preference | Viewport display |
| **Alerts** | `config["audio_enabled"]` | Audio alarm toggle (UI preference) | Sound channel |
| **Alerts** | `config["volume"]` | Notification volume slider ($0\% \to 100\%$) | Sound volume |
| **Display** | `config["dark_mode"]` | Dark theme toggle | DOM style injection |
| **Display** | `config["show_fps"]` | Header FPS counter toggle | Header bar widget |
| **System Info** | Diagnostics reporter | Queries Python, Streamlit, OpenCV, MediaPipe, OS, CPU, RAM | Environment status |

---

## 4. Hardware Environment Diagnostics (`system_info.py`)

The System Information panel queries runtime hardware versions with safe `"Information unavailable"` fallbacks:
- **Python Version**: `sys.version`
- **Streamlit Version**: `st.__version__`
- **OpenCV Version**: `cv2.__version__`
- **MediaPipe Version**: `mp.__version__`
- **Platform OS**: `platform.platform()`
- **CPU & Memory Usage**: `psutil.cpu_percent()`, `psutil.virtual_memory()`

---

## 5. Decoupling & Zero-Backend-Modification Verification

| Backend Module | File Path | Status | Verification Detail |
| :--- | :--- | :--- | :--- |
| **Configuration Manager** | `dashboard/utils/configuration_manager.py` | **NEW** | Decoupled UI preference storage. |
| **Decision Engine** | `analytics/decision_engine.py` | **UNTOUCHED** | Scoring rules unmodified. |
| **EAR Calculator** | `detection/ear_calculator.py` | **UNTOUCHED** | EAR math unmodified. |
| **MAR Calculator** | `detection/mar_calculator.py` | **UNTOUCHED** | MAR math unmodified. |
| **Camera Stream** | `camera/camera.py` | **UNTOUCHED** | OpenCV video capture unmodified. |
