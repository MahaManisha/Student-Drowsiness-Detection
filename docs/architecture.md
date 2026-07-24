# 🏛️ Student Drowsiness Detection System: System Architecture Reference

## 1. Architectural Overview

The **Student Drowsiness Detection System** is an enterprise-grade, real-time computer vision and machine learning application designed to monitor, analyze, evaluate, alert, and log student attentiveness and drowsiness during educational sessions.

The system is constructed following strict **SOLID design principles**, a modular component hierarchy, and a decoupled event-driven data pipeline to guarantee high frame throughput ($30.0 \text{ FPS}$), zero frame drops, and zero memory degradation.

```
+-----------------------------------------------------------------------------------+
|                                 VIDEO CAPTURE LAYER                               |
|                              [ CameraStream (OpenCV) ]                            |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                              FACIAL MESH DETECTOR LAYER                           |
|                       [ FaceMeshDetector (MediaPipe 478 pts) ]                    |
+-----------------------------------------------------------------------------------+
                                         |
                     +-------------------+-------------------+
                     |                                       |
                     v                                       v
+------------------------------------------+ +--------------------------------------+
|           EYE TRACKING PIPELINE          | |       MOUTH TRACKING PIPELINE        |
|  [ EyeLandmarkExtractor (6 pts/eye) ]    | |  [ MouthLandmarkExtractor (8 inner) ]|
|                    |                     | |                   |                  |
|                    v                     | |                   v                  |
|      [ EARCalculator (Ratio formula) ]   | |    [ MARCalculator (Inner lip formula)]|
|                    |                     | |                   |                  |
|                    v                     | |                   v                  |
|  [ EyeStateClassifier (Thresh EAR) ]     | |  [ YawnDetector (Temporal Window) ]  |
|                    |                     | +--------------------------------------+
|                    v                     |                         |
|   [ TemporalEyeAnalyzer (Window/Blink) ] |                         |
+------------------------------------------+                         |
                     |                                               |
                     +-------------------+---------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                             HEAD POSE ESTIMATOR LAYER                             |
|              [ HeadPoseEstimator (solvePnP & Euler Angles Pitch/Yaw/Roll) ]       |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                             DECISION ENGINE LAYER                                 |
|               [ StudentDrowsinessDecisionEngine (0-100 Score & Mappings) ]        |
+-----------------------------------------------------------------------------------+
                                         |
             +---------------------------+---------------------------+
             |                           |                           |
             v                           v                           v
+------------------------+  +------------------------+  +---------------------------+
|      ALERT SYSTEM      |  |     SESSION LOGGER     |  |    SESSION STATISTICS     |
| [ AlertManager ]       |  | [ SessionLogger ]      |  | [SessionStatisticsTracker]|
|  ├─ HUDAlertChannel    |  |  └─ JSON Lines Log     |  |  └─ Telemetry & JSON Export|
|  └─ AudioAlertChannel  |  +------------------------+  +---------------------------+
+------------------------+                                           |
             |                                                       |
             +---------------------------+---------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                               RENDERING & REPORTING                               |
|        [ HUDVisualizer ]                             [ ReportGenerator ]          |
|    (Dual HUD Overlay Display)                     (Markdown Session Report)        |
+-----------------------------------------------------------------------------------+
```

---

## 2. Component Design & Responsibilities

### 2.1 Video Capture & Detector Core
* **`CameraStream` ([camera/camera.py](file:///c:/Users/Maha%20Monisha/OneDrive/Desktop/Triton%20Labs/Student-Drowsiness-Detection/camera/camera.py))**:
  Encapsulates OpenCV `cv2.VideoCapture` stream management, double-buffering, FPS timing calculation, frame resizing, and camera resource initialization.
* **`FaceMeshDetector` ([detection/face_mesh.py](file:///c:/Users/Maha%20Monisha/OneDrive/Desktop/Triton%20Labs/Student-Drowsiness-Detection/detection/face_mesh.py))**:
  Executes MediaPipe Face Mesh solver to infer 478 3D landmark coordinates in pixel-space, rendering cyan mesh tessellations and iris landmark connections.

### 2.2 Eye Tracking Subsystem
* **`EyeLandmarkExtractor` ([detection/eye_landmarks.py](file:///c:/Users/Maha%20Monisha/OneDrive/Desktop/Triton%20Labs/Student-Drowsiness-Detection/detection/eye_landmarks.py))**:
  Isolates 6 key landmark coordinates per eye (`RIGHT_EYE_LANDMARK_INDICES` & `LEFT_EYE_LANDMARK_INDICES`).
* **`EARCalculator` ([detection/ear_calculator.py](file:///c:/Users/Maha%20Monisha/OneDrive/Desktop/Triton%20Labs/Student-Drowsiness-Detection/detection/ear_calculator.py))**:
  Calculates the Eye Aspect Ratio (EAR) using Euclidean distances:
  $$\text{EAR} = \frac{\|P_2 - P_6\| + \|P_3 - P_5\|}{2 \cdot \|P_1 - P_4\|}$$
* **`EyeStateClassifier` ([detection/eye_state_classifier.py](file:///c:/Users/Maha%20Monisha/OneDrive/Desktop/Triton%20Labs/Student-Drowsiness-Detection/detection/eye_state_classifier.py))**:
  Classifies left, right, and overall eye states into `EyeState.OPEN` or `EyeState.CLOSED` using thresholding with step-spike filtering.
* **`TemporalEyeAnalyzer` ([detection/temporal_eye_analyzer.py](file:///c:/Users/Maha%20Monisha/OneDrive/Desktop/Triton%20Labs/Student-Drowsiness-Detection/detection/temporal_eye_analyzer.py))**:
  Maintains sliding frame buffer history, debounce filtering (`min_blink_duration`), valid blink counting (`OPEN -> CLOSED -> OPEN`), and consecutive closure duration metrics.

### 2.3 Mouth & Yawn Subsystem
* **`MouthLandmarkExtractor` ([detection/mouth_landmark_extractor.py](file:///c:/Users/Maha%20Monisha/OneDrive/Desktop/Triton%20Labs/Student-Drowsiness-Detection/detection/mouth_landmark_extractor.py))**:
  Extracts inner lip (8-point) and outer lip (8-point) landmark subsets.
* **`MARCalculator` ([detection/mar_calculator.py](file:///c:/Users/Maha%20Monisha/OneDrive/Desktop/Triton%20Labs/Student-Drowsiness-Detection/detection/mar_calculator.py))**:
  Computes Mouth Aspect Ratio (MAR) using normalized inner lip aperture:
  $$\text{MAR} = \frac{\|P_{81} - P_{178}\| + \|P_{13} - P_{14}\| + \|P_{311} - P_{402}\|}{3.0 \cdot \|P_{308} - P_{78}\|}$$
* **`YawnDetector` ([detection/yawn_detector.py](file:///c:/Users/Maha%20Monisha/OneDrive/Desktop/Triton%20Labs/Student-Drowsiness-Detection/detection/yawn_detector.py))**:
  Tracks mouth aperture state transitions (`CLOSED -> OPEN -> CLOSED`) over temporal frame buffers to record complete yawn events without double-counting.

### 2.4 Head Pose Subsystem
* **`HeadPoseEstimator` ([detection/head_pose_estimator.py](file:///c:/Users/Maha%20Monisha/OneDrive/Desktop/Triton%20Labs/Student-Drowsiness-Detection/detection/head_pose_estimator.py))**:
  Maps 6 2D facial landmarks (nose tip, chin, eye outer corners, mouth outer corners) against a 3D canonical facial model using OpenCV `cv2.solvePnP` to decompose rotation matrices into Euler angles:
  - `Pitch` (Downward head tilt / nodding)
  - `Yaw` (Sideways head rotation)
  - `Roll` (Head tilt)

### 2.5 Drowsiness Decision Engine
* **`StudentDrowsinessDecisionEngine` ([detection/drowsiness_decision_engine.py](file:///c:/Users/Maha%20Monisha/OneDrive/Desktop/Triton%20Labs/Student-Drowsiness-Detection/detection/drowsiness_decision_engine.py))**:
  Fuses multi-modal indicators into a unified 0-100 drowsiness score:
  - Eye closure duration: Max 50 pts
  - Slow blink behavior: Max 15 pts
  - Yawn activity: Max 20 pts
  - Downward posture slumping: Max 15 pts
  
  Score state mapping:
  - $0.0 - 29.9$: `ALERT`
  - $30.0 - 49.9$: `SLIGHTLY_DROWSY`
  - $50.0 - 79.9$: `DROWSY`
  - $80.0 - 100.0$: `HIGHLY_DROWSY`

### 2.6 Alert & Dashboard Subsystems
* **`AlertManager` ([alerts/alert_manager.py](file:///c:/Users/Maha%20Monisha/OneDrive/Desktop/Triton%20Labs/Student-Drowsiness-Detection/alerts/alert_manager.py))**:
  Routes decisions to registered `AlertChannel` objects with state-wise cooldown suppression.
  - `HUDAlertChannel`: Updates active visual HUD warning messages and severity (`subtle`, `strong`, `critical`).
  - `AudioAlertChannel`: Asynchronously spawns background threads to play `alarm.wav` on `HIGHLY_DROWSY` state without blocking main frame capture.
* **`HUDVisualizer` ([dashboard/hud.py](file:///c:/Users/Maha%20Monisha/OneDrive/Desktop/Triton%20Labs/Student-Drowsiness-Detection/dashboard/hud.py))**:
  Renders live telemetry panels, dual progress bars (Score & EAR), state color badges, eye/mouth status, and warning overlays.

### 2.7 Logging & Reporting Infrastructure
* **`SessionLogger` ([logging/session_logger.py](file:///c:/Users/Maha%20Monisha/OneDrive/Desktop/Triton%20Labs/Student-Drowsiness-Detection/logging/session_logger.py))**:
  Appends structured state transition events to JSON Lines formatted log file (`output/logs/drowsiness_session_log.json`).
* **`SessionStatisticsTracker` ([analytics/session_statistics.py](file:///c:/Users/Maha%20Monisha/OneDrive/Desktop/Triton%20Labs/Student-Drowsiness-Detection/analytics/session_statistics.py))**:
  Aggregates session duration, running EAR/MAR averages, state time distribution, and exports pretty-printed JSON (`output/reports/session_statistics.json`).
* **`ReportGenerator` ([reports/report_generator.py](file:///c:/Users/Maha%20Monisha/OneDrive/Desktop/Triton%20Labs/Student-Drowsiness-Detection/reports/report_generator.py))**:
  Parses telemetry statistics and event logs to generate Markdown session reports (`output/reports/session_summary_report.md`).

---

## 3. SOLID Design Principles Compliance

1. **Single Responsibility Principle (SRP)**:
   Each module performs exactly one dedicated role. For example, `EARCalculator` computes mathematical ratio formulas, `TemporalEyeAnalyzer` tracks time-series frame state buffers, and `HUDVisualizer` handles display rendering.
2. **Open/Closed Principle (OCP)**:
   Subsystems use modular registries (e.g., `AlertManager.register_channel()`), allowing developers to add new alert channels (SMS, Email, Push) without modifying existing alert routing logic.
3. **Liskov Substitution Principle (LSP)**:
   Concrete alert channels inherit from `AlertChannel` ABC and strictly adhere to the `trigger(result: DrowsinessResult)` signature.
4. **Interface Segregation Principle (ISP)**:
   Components communicate via minimal primitive dictionaries or specialized Data Transfer Objects (DTOs) rather than monolithic base classes.
5. **Dependency Inversion Principle (DIP)**:
   High-level modules (e.g., `StudentDrowsinessApp`) depend on abstract interfaces and component contracts rather than concrete hardware bindings.
