# 📹 Student Drowsiness Detection System: Live Camera Streamlit Integration Guide (Phase S3)

## 1. Executive Summary & Objective

Phase S3 integrates the real-time webcam video stream (`CameraStream` in `camera/camera.py`) and MediaPipe face mesh landmarks into the central viewport of the **Streamlit Web Dashboard**.

As strictly mandated, the **AI backend detection engine (`detection/`, `analytics/`, `alerts/`, `camera/`, `logging/`, `models/`, `utils/`) remains 100% untouched and protected**.

---

## 2. Technical Architecture & Lifecycle Management

### 2.1 Session-State Camera Persistence (`DashboardCameraManager`)
In standard Streamlit execution, every user interaction causes the script to re-run from top to bottom. To prevent the camera device from being repeatedly opened and closed on every refresh cycle:
1. `DashboardCameraManager` encapsulates `CameraStream` and MediaPipe landmark solvers.
2. The manager instance is initialized once and stored inside Streamlit's persistent session state (`st.session_state.camera_manager`).
3. `camera_manager.start()` is called once on startup or when the user clicks the **"🔄 Retry Camera Connection"** button.

```
[Streamlit app.py Execution]
            │
            ▼
   [st.session_state check]
      ├── Instance exists? ──► [Reuse camera_manager]
      └── Instance missing? ─► [Instantiate DashboardCameraManager]
            │
            ▼
   [camera_manager.get_processed_frame()]
      ├── Frame capture success? ─► Convert BGR to RGB ──► st.image() render ──► st.rerun() loop
      └── Frame capture failure? ─► Render error banner ──► Display "Retry Camera" button
```

---

## 3. Preserved Landmark & Overlay Layers

The live camera view composite preserves all core MediaPipe tracking overlays:
1. **MediaPipe 478-Point 3D Face Mesh**: Cyan mesh tessellation lines connecting facial landmarks.
2. **Eye Landmarks & EAR Contours**: 6 key points per eye, iris tracking dots, and active eye state badge (`OPEN` / `CLOSED`).
3. **Mouth Landmarks & MAR Aperture**: 8 inner lip contour points, vertical distance aperture lines, and mouth state badge (`CLOSED` / `YAWNING`).
4. **Head Pose Projection**: 3D nose vector line, pitch/yaw deflection target dot, and roll axis tilt indicator.

---

## 4. Error Handling & Recovery UI

The camera integration handles all common hardware and permission errors gracefully without crashing the dashboard:

| Error Condition | Cause | Streamlit UI Response |
| :--- | :--- | :--- |
| **Camera Unavailable** | Webcam locked by another app (e.g. Teams/Zoom) | Displays Red Alert Banner: *"Camera source is unavailable or currently in use"* + Retry Button |
| **Permission Denied** | OS camera permission revoked | Displays Error Message + Prompt to grant camera access in OS settings |
| **Frame Read Failure** | USB webcam unplugged during streaming | Sets `is_connected = False` + Triggers error state UI without crashing app |
| **Stream Interruption**| Transient OpenCV buffer frame drop | Uses fallback telemetry dictionary to keep right panel metrics alive |

---

## 5. Performance Engineering & 30.0 FPS Loop Target

To maintain real-time frame rates without introduce stutter or high memory overhead:
1. **In-Place OpenCV Overlay**: Overlays are drawn directly onto captured numpy arrays prior to RGB conversion.
2. **Regulated `time.sleep(0.03)` Delay**: Smooth $\approx 30.0\text{ FPS}$ refresh cycle managed via `st.rerun()`.
3. **Clean Resource Release**: Calling `camera_manager.stop()` releases `cv2.VideoCapture` resources cleanly upon application exit.

---

## 6. Decoupling & Zero-Backend-Modification Verification

| Code Module | Path | Status | Verification Detail |
| :--- | :--- | :--- | :--- |
| **Face Mesh Detector** | `detection/face_mesh.py` | **UNTOUCHED** | 478 3D landmark solver unmodified. |
| **EAR Calculator** | `detection/ear_calculator.py` | **UNTOUCHED** | Euclidean EAR ratio math unmodified. |
| **MAR Calculator** | `detection/mar_calculator.py` | **UNTOUCHED** | Inner lip MAR ratio math unmodified. |
| **Head Pose Estimator** | `detection/head_pose_estimator.py` | **UNTOUCHED** | solvePnP 3D pose projection unmodified. |
| **Decision Engine** | `analytics/decision_engine.py` | **UNTOUCHED** | Drowsiness scoring & rules unmodified. |
| **Camera Stream** | `camera/camera.py` | **UNTOUCHED** | OpenCV stream capture class unmodified. |
