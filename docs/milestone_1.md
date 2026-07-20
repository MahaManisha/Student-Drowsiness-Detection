# 📄 Milestone 1 Documentation: System Foundation & Vision Pipeline

**Project**: Student Drowsiness Detection System  
**Milestone**: 1 (Foundation, Camera Feed & Face Mesh Integration)  
**Status**: Completed ✅  

---

## 🎯 Executive Summary

Milestone 1 establishes the production-grade architectural foundation for the **Student Drowsiness Detection System**. The project strictly adheres to modular software engineering principles, separating camera frame ingestion, facial landmark extraction, configuration management, logging, and user preview execution.

---

## 📁 1. Project Directory Structure

The repository has been structured cleanly into discrete packages:

```text
Student-Drowsiness-Detection/
├── config.py           # Centralized configuration constants & paths
├── main.py             # Main entry point application loop
├── requirements.txt    # Production Python dependencies
├── .gitignore          # Version control exclusion rules
├── camera/             # Camera stream management package
│   └── camera.py       # CameraStream class (OpenCV ingestion & FPS)
├── detection/          # Computer Vision algorithms package
│   └── face_mesh.py    # FaceMeshDetector (MediaPipe 468 landmarks)
├── utils/              # System utilities package
│   └── logger.py       # Reusable rotating file & console logger
├── alerts/             # Alert management subpackage
├── dashboard/          # Streamlit monitoring dashboard subpackage
├── reports/            # Analytics & session report subpackage
├── assets/             # Sound clips, images, and AI model weights
├── datasets/           # Raw & processed training data
├── docs/               # Architecture & milestone documentation
└── output/             # Generated system logs and video recordings
```

---

## 💻 2. Environment Setup & Installation Guide

### Recommended Python Version
* **Python 3.10.x** or **Python 3.11.x** (64-bit)

### Installation Commands (Windows)
```powershell
# 1. Clone the repository
git clone https://github.com/MahaManisha/Student-Drowsiness-Detection.git
cd Student-Drowsiness-Detection

# 2. Create isolated virtual environment
python -m venv .venv

# 3. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt
```

---

## 📦 3. Dependency Rationale

1. **`opencv-python` (>=4.8.0)**: Reads live video streams from webcam or RTSP sources, decodes BGR frames, computes FPS timestamps, and renders overlay badges.
2. **`mediapipe` (>=0.10.9)**: Extracts 468 3D facial landmark points per face in real-time.
3. **`numpy` (>=1.24.0)** & **`scipy` (>=1.10.0)**: Perform vector calculations for landmark Euclidean distances.
4. **`pandas` (>=2.0.0)** & **`matplotlib` (>=3.7.0)**: Structure session logs and generate alertness charts.
5. **`streamlit` (>=1.28.0)**: Powers the live monitoring dashboard web application.
6. **`pygame` / `playsound`**: Handles non-blocking audio alarm triggers.
7. **`pytest`**: Unit test execution framework.

---

## 🚀 4. How to Run the Application

Execute the main application driver:
```powershell
python main.py
```
* Press `q` or `ESC` inside the preview window to exit.
* System logs are saved automatically to `output/logs/system.log`.

---

##📊 5. Completed Tasks in Milestone 1

| Component | File Path | Status | Summary |
| :--- | :--- | :---: | :--- |
| **Config** | [config.py](file:///c:/Users/Maha%20Monisha/OneDrive/Desktop/Triton%20Labs/Student-Drowsiness-Detection/config.py) | ✅ | Single source of truth for resolution, paths, and thresholds. |
| **Logging** | [utils/logger.py](file:///c:/Users/Maha%20Monisha/OneDrive/Desktop/Triton%20Labs/Student-Drowsiness-Detection/utils/logger.py) | ✅ | Thread-safe logger with console + 5MB file rotation. |
| **Camera** | [camera/camera.py](file:///c:/Users/Maha%20Monisha/OneDrive/Desktop/Triton%20Labs/Student-Drowsiness-Detection/camera/camera.py) | ✅ | Hardware availability check, FPS calculation & context manager. |
| **Face Mesh** | [detection/face_mesh.py](file:///c:/Users/Maha%20Monisha/OneDrive/Desktop/Triton%20Labs/Student-Drowsiness-Detection/detection/face_mesh.py) | ✅ | MediaPipe 468-point 3D landmark extraction & mesh rendering. |
| **Main Loop** | [main.py](file:///c:/Users/Maha%20Monisha/OneDrive/Desktop/Triton%20Labs/Student-Drowsiness-Detection/main.py) | ✅ | Real-time driver loop integrating camera, face mesh, & preview. |

---

## 🔮 6. Future Milestone Roadmap

- **Milestone 2**: Eye Aspect Ratio (EAR), Mouth Aspect Ratio (MAR for yawning), and Head Pose tilt algorithm implementation.
- **Milestone 3**: Asynchronous audio/visual alert trigger system.
- **Milestone 4**: Streamlit monitoring dashboard & session report export system.
