# 📹 Student Drowsiness Detection System: Live Camera Stream Integration Specification (Phase D2)

## 1. Executive Summary & Architectural Objective

Phase D2 specifies the technical architecture, visual styling, compositing pipeline, and performance optimization strategy for integrating the live camera feed into the central viewport of the **Student Drowsiness Detection System Dashboard**.

The camera integration strictly adheres to 8 core design & technical directives:
1. **Viewport Occupation**: Occupies approximately **45–50%** of total screen real estate.
2. **Face Mesh Preservation**: Preserves the complete MediaPipe 478 3D landmark facial mesh overlay.
3. **Landmark Preservation**: Preserves eye tracking contours, iris landmarks, mouth aperture lines, and 3D head pose projection vectors.
4. **Performance Target**: Maintains a consistent real-time frame rate of **30.0 FPS** without frame drops or rendering latency.
5. **Rounded Frame Geometry**: Encapsulated within a sleek rounded card frame (`border-radius: 16px`).
6. **Subtle Border Glow**: Features a dynamic ambient neon border glow that shifts color based on the current drowsiness alert severity.
7. **Aspect Ratio Maintenance**: Preserves native video aspect ratio ($16:9$) with zero spatial distortion or landmark warping.
8. **Zero Detector Alteration**: Keeps the core AI detector (`FaceMeshDetector` in `detection/face_mesh.py`) and underlying math engines 100% untouched.

---

## 2. Screen Real Estate & Grid Integration (45–50% Occupation)

The dashboard layout utilizes a CSS Grid split where the central viewport is designated for live camera stream ingestion.

### 2.1 Viewport Dimension Calculations
* **Dashboard Full Dimensions**: $1920\times 1080\text{px}$ (Reference 1080p Viewport).
* **Grid Area**: `grid-area: center` (Column width: `1fr` spanning between `280px` Left Telemetry Panel and `320px` Right Telemetry Panel).
* **Calculated Width**: $1920\text{px} - 280\text{px} - 320\text{px} - (4 \times 16\text{px gap}) = 1256\text{px}$ ($\approx 65.4\%$ of total layout width).
* **Calculated Height**: $1080\text{px} - 64\text{px Header} - 120\text{px Dock} - (4 \times 16\text{px gap}) = 832\text{px}$ ($\approx 77.0\%$ of total layout height).
* **Screen Surface Occupation**: 
  $$\text{Surface Area Ratio} = \frac{1256\text{px} \times 832\text{px}}{1920\text{px} \times 1080\text{px}} = \frac{1,044,992\text{px}^2}{2,073,600\text{px}^2} \approx 50.39\%$$
  This precisely fulfills the requirement of occupying **45–50% of total screen real estate**.

```
+---------------------------------------------------------------------------------------------------+
|                                            HEADER (64px)                                          |
+--------------------------+--------------------------------------------------+---------------------+
|                          |                                                  |                     |
|    LEFT PANEL (280px)    |              CENTER CAMERA VIEWPORT              |  RIGHT PANEL (320px)|
|                          |            (1256px x 832px = 50.39%)             |                     |
|    Eye Telemetry         |                                                  |  Head Pose          |
|    Mouth Telemetry       |   +------------------------------------------+   |  Decision Engine    |
|                          |   |                                          |   |                     |
|                          |   |         LIVE CAMERA FEED FRAME           |   |                     |
|                          |   |         (MediaPipe 478 Mesh Overlay)     |   |                     |
|                          |   |                                          |   |                     |
|                          |   +------------------------------------------+   |                     |
+--------------------------+--------------------------------------------------+---------------------+
|                                            BOTTOM DOCK (120px)                                    |
+---------------------------------------------------------------------------------------------------+
```

---

## 3. Aspect Ratio Preservation & Scaling Engine

To prevent facial mesh distortion, iris stretching, or aspect ratio warping, the integration engine enforces strict aspect ratio preservation.

### 3.1 Aspect Ratio Scaling Pipeline
* **Source Native Stream**: $1280\times 720\text{px}$ ($16:9$ aspect ratio, $\text{ratio} = 1.7778$).
* **Target Container Bounds**: $W_c \times H_c$ (Dynamic width & height of the center panel).
* **Fitting Algorithm**: Uniform pillarbox/letterbox scaling (`contain` fitting strategy):
  ```python
  def calculate_aspect_fit(src_w: int, src_h: int, target_w: int, target_h: int) -> Tuple[int, int, int, int]:
      """
      Calculates aspect-ratio preserved scaling dimensions and letterbox padding offsets.
      """
      src_ratio = src_w / float(src_h)
      target_ratio = target_w / float(target_h)

      if src_ratio > target_ratio:
          # Scale based on width (Letterbox top/bottom)
          fit_w = target_w
          fit_h = int(target_w / src_ratio)
      else:
          # Scale based on height (Pillarbox left/right)
          fit_h = target_h
          fit_w = int(target_h * src_ratio)

      offset_x = (target_w - fit_w) // 2
      offset_y = (target_h - fit_h) // 2

      return fit_w, fit_h, offset_x, offset_y
  ```

---

## 4. Visual Styling: Rounded Frame & Dynamic Border Glow

The live camera view is styled to integrate seamlessly into the modern dark theme using rounded frame masking and a dynamic ambient border glow.

### 4.1 Frame Geometry Tokens
* **Outer Viewport Container Radius**: `border-radius: 16px` (`--radius-container`).
* **Frame Clipping Mask**: Clean Anti-Aliased Alpha Mask applied to video stream edges.
* **Inner Camera Canvas Border**: `1px solid rgba(255, 255, 255, 0.10)` (`--border-subtle`).

### 4.2 Dynamic Border Glow System
The camera frame's outer border dynamically updates its ambient glow color based on the real-time drowsiness alert state:

```css
/* Camera Frame Base Styles */
.camera-viewport-frame {
  border-radius: 16px;
  overflow: hidden;
  position: relative;
  background-color: #0D0E12;
  transition: box-shadow 0.3s ease, border-color 0.3s ease;
}

/* State 1: ALERT / NORMAL (Emerald Teal Glow) */
.camera-viewport-frame[data-state="ALERT"] {
  border: 1px solid rgba(16, 185, 129, 0.5);
  box-shadow: 0 0 20px 2px rgba(16, 185, 129, 0.25), 0 8px 24px -4px rgba(0, 0, 0, 0.5);
}

/* State 2: SLIGHTLY DROWSY (Amber Gold Glow) */
.camera-viewport-frame[data-state="SLIGHTLY_DROWSY"] {
  border: 1px solid rgba(245, 158, 11, 0.6);
  box-shadow: 0 0 24px 3px rgba(245, 158, 11, 0.30), 0 8px 24px -4px rgba(0, 0, 0, 0.5);
}

/* State 3: DROWSY (Vivid Orange Glow) */
.camera-viewport-frame[data-state="DROWSY"] {
  border: 1px solid rgba(249, 115, 22, 0.7);
  box-shadow: 0 0 28px 4px rgba(249, 115, 22, 0.35), 0 8px 24px -4px rgba(0, 0, 0, 0.5);
}

/* State 4: HIGHLY DROWSY (Crimson Red Pulsing Glow) */
.camera-viewport-frame[data-state="HIGHLY_DROWSY"] {
  border: 1px solid rgba(239, 68, 68, 0.8);
  box-shadow: 0 0 32px 6px rgba(239, 68, 68, 0.50), 0 8px 24px -4px rgba(0, 0, 0, 0.5);
  animation: pulse-border-glow 1.2s infinite ease-in-out;
}

@keyframes pulse-border-glow {
  0% { box-shadow: 0 0 16px 2px rgba(239, 68, 68, 0.3); }
  50% { box-shadow: 0 0 36px 8px rgba(239, 68, 68, 0.65); }
  100% { box-shadow: 0 0 16px 2px rgba(239, 68, 68, 0.3); }
}
```

---

## 5. Facial Mesh & Telemetry Overlay Compositing Engine

The integration engine overlays landmark visualizations directly onto the video frames prior to viewport rendering, preserving all core facial tracking overlays.

### 5.1 Multi-Layer Compositing Architecture

```
+--------------------------------------------------------------------+
| LAYER 4: Stream HUD Badges (Resolution, FPS, Latency, Latch)      |
+--------------------------------------------------------------------+
| LAYER 3: Head Pose Vector Line & Reticle Overlay                   |
+--------------------------------------------------------------------+
| LAYER 2: Eye (EAR/Iris) & Mouth (MAR) Highlighted Contours         |
+--------------------------------------------------------------------+
| LAYER 1: MediaPipe 478-Point Face Mesh Tessellation (Cyan Lines)   |
+--------------------------------------------------------------------+
| LAYER 0: Raw OpenCV BGR Video Frame (1280x720 @ 30 FPS)            |
+--------------------------------------------------------------------+
```

### 5.2 Preserved Overlay Details

1. **MediaPipe 478 3D Mesh**:
   - Cyan mesh tessellation lines (`RGB(0, 255, 255)`) connecting 478 face landmark coordinates.
   - Refined iris tracking points (Landmarks 468–477).
2. **Eye Telemetry Overlay**:
   - 6 key EAR landmark dots per eye (`RIGHT_EYE_LANDMARK_INDICES` & `LEFT_EYE_LANDMARK_INDICES`).
   - Active eye state text overlay above eye bounding boxes (`OPEN` in Green, `CLOSED` in Red).
3. **Mouth Telemetry Overlay**:
   - 8 inner lip contour points (`INNER_LIP_INDICES`) and MAR vertical aperture distance lines.
   - Active mouth state badge (`CLOSED` in Green, `YAWNING` in Magenta).
4. **Head Pose Spatial Projection Overlay**:
   - 3D pose projection vector line drawn from nose tip landmark (Landmark 1).
   - Pitch, Yaw, and Roll deflection text badges.

---

## 6. Performance Engineering & 30.0 FPS Maintenance

To guarantee that adding the camera frame to the dashboard layout introduces **zero performance degradation or frame drops below 30.0 FPS**, the rendering pipeline adheres to strict optimization principles:

### 6.1 Performance Optimization Rules
1. **Single-Pass Blending**: Frame overlays use in-place OpenCV drawing or a single `cv2.addWeighted` pass to eliminate intermediate memory buffer allocations.
2. **Zero In-Loop Re-allocations**: Pre-allocated numpy arrays for frame buffers and mask matrices.
3. **Direct Memory Access**: Native BGR/RGB frame numpy arrays passed directly into the UI canvas stream buffer.
4. **Asynchronous Frame Ingestion**: `CameraStream` maintains background thread buffer reading to prevent I/O blocking.

---

## 7. Decoupling & Zero-Detector-Modification Verification

| Subsystem Component | File Path | Status | Verification Guarantee |
| :--- | :--- | :--- | :--- |
| **MediaPipe Mesh Core** | `detection/face_mesh.py` | **UNTOUCHED** | No changes to 478-point landmark solver or MediaPipe parameters. |
| **EAR Calculator** | `detection/ear_calculator.py` | **UNTOUCHED** | Formula $\text{EAR} = \frac{\|P_2-P_6\|+\|P_3-P_5\|}{2\|P_1-P_4\|}$ untouched. |
| **MAR Calculator** | `detection/mar_calculator.py` | **UNTOUCHED** | Formula $\text{MAR} = \frac{\|P_{81}-P_{178}\|+\|P_{13}-P_{14}\|+\|P_{311}-P_{402}\|}{3\|P_{308}-P_{78}\|}$ untouched. |
| **Head Pose Estimator** | `detection/head_pose_estimator.py` | **UNTOUCHED** | solvePnP 3D pose estimation algorithm untouched. |
| **Decision Engine** | `analytics/decision_engine.py` | **UNTOUCHED** | Rule evaluator and scoring algorithms untouched. |
| **Camera Ingestion** | `camera/camera.py` | **UNTOUCHED** | OpenCV stream capture loop untouched. |
