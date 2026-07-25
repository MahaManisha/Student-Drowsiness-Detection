# 🏗️ Student Drowsiness Detection System: Layout Architecture & Data Matrix (Phase D1)

## 1. Architectural Layout & Grid Overview

The **Layout Design Document** defines the technical structural grid, responsive layout engine, component tree, and backend telemetry binding matrix for the **Student Drowsiness Detection System Dashboard**.

The layout is built upon a high-performance **CSS Grid + Flexbox Hybrid Framework** designed to maximize viewport space, guarantee visual balance across widescreen display monitors, and prevent content overlap under fast telemetry updates ($30\text{ FPS}$).

---

## 2. Technical CSS Grid Architecture

### 2.1 Grid Container Definition
The outer dashboard application layout is declared as a 5-zone grid container using standard CSS Grid syntax:

```css
.dashboard-container {
  display: grid;
  width: 100vw;
  height: 100vh;
  padding: 16px;
  gap: 16px;
  box-sizing: border-box;
  background-color: var(--bg-base);

  /* Grid Layout Areas */
  grid-template-columns: 280px 1fr 320px;
  grid-template-rows: 64px 1fr 120px;
  grid-template-areas:
    "header  header  header"
    "left    center  right"
    "bottom  bottom  bottom";
}
```

```
+-----------------------------------------------------------------------------+
|                                HEADER AREA                                  |
+------------------------------+-------------------------------+--------------+
|          LEFT AREA           |          CENTER AREA          |  RIGHT AREA  |
|       (Eye & Mouth)          |     (Live Camera Feed)        | (Pose & Score|
+------------------------------+-------------------------------+--------------+
|                                BOTTOM AREA                                  |
|                      (Event Timeline & System Status)                       |
+-----------------------------------------------------------------------------+
```

---

## 3. Structural Breakdown of Grid Zones

### 3.1 Zone 1: Header Area (`grid-area: header`)
* **Dimensions**: Full width (`100%`), fixed height (`64px`).
* **Display**: Flexbox row (`justify-content: space-between`, `align-items: center`).
* **Sub-components**:
  - `HeaderBrandWidget`: System title, icon, and active pulse indicator.
  - `SessionTimerWidget`: Elapsed time counter formatted as `HH:MM:SS`.
  - `FPSCounterWidget`: Real-time pipeline processing rate.
  - `AlertStatusWidget`: Color-coded state badge (`ALERT`, `SLIGHTLY DROWSY`, `DROWSY`, `HIGHLY DROWSY`).

### 3.2 Zone 2: Left Telemetry Panel (`grid-area: left`)
* **Dimensions**: Fixed width (`280px`), vertical flex height (`100%`).
* **Display**: Flexbox column (`flex-direction: column`, `gap: 16px`).
* **Sub-components**:
  - `EyeTelemetryCard`:
    - EAR left, right, and average values.
    - EAR threshold progress bar (`threshold: 0.21`).
    - Eye state indicator (`OPEN` / `CLOSED`).
    - Temporal blink analytics (Total blinks, continuous closed time).
  - `MouthTelemetryCard`:
    - MAR numerical readout.
    - MAR threshold progress bar (`threshold: 0.55`).
    - Mouth state indicator (`CLOSED` / `YAWNING`).
    - Temporal yawn analytics (Total yawns, continuous open duration).

### 3.3 Zone 3: Center Viewport (`grid-area: center`)
* **Dimensions**: Flexible width (`1fr`), flex height (`100%`).
* **Display**: Flexbox container (`position: relative`, `overflow: hidden`).
* **Sub-components**:
  - `LiveCameraStream`: Primary OpenCV video element displaying facial mesh annotations.
  - `HUDOverlayBadges`: Stream resolution, latency gauge, latch status overlay.

### 3.4 Zone 4: Right Telemetry Panel (`grid-area: right`)
* **Dimensions**: Fixed width (`320px`), vertical flex height (`100%`).
* **Display**: Flexbox column (`flex-direction: column`, `gap: 16px`).
* **Sub-components**:
  - `HeadPoseCard`:
    - Pitch/Yaw deflection target reticle visualizer.
    - Roll axis angle tilt indicator line.
    - Numerical degrees readout and pose valid status badge.
  - `DecisionEngineCard`:
    - Drowsiness Risk Score gauge (`0 - 100`).
    - Decision confidence progress bar (`0 - 100%`).
    - Co-occurrence multi-modal trigger badges (`EYE`, `MOUTH`, `POSE`).
    - Dynamic natural language decision explanation text box.

### 3.5 Zone 5: Bottom Dock (`grid-area: bottom`)
* **Dimensions**: Full width (`100%`), fixed height (`120px`).
* **Display**: Flexbox row (`display: flex`, `gap: 16px`).
* **Sub-components**:
  - `EventTimelineStream` (`flex: 1`): Real-time event log list.
  - `SystemStatusCard` (`width: 320px`): Channel status indicators (HUD, Audio, Logger).

---

## 4. Telemetry Payload Binding Matrix

The dashboard layout decouples UI rendering from backend telemetry computation. Below is the mapping matrix connecting backend dictionary keys to UI layout slots:

| Backend Telemetry Field Key | Data Type | Target UI Component Slot | Visual Representation |
| :--- | :--- | :--- | :--- |
| `session_time_str` | `str` | `HeaderArea -> SessionTimerWidget` | Monospaced Text (`01:24:15`) |
| `fps` | `float` | `HeaderArea -> FPSCounterWidget` | Metric Counter (`30.0 FPS`) |
| `drowsiness_state` | `str` | `HeaderArea -> AlertStatusWidget` | Colored Pill Badge (`ALERT`) |
| `left_ear` | `float` | `LeftPanel -> EyeTelemetryCard` | Monospaced Metric (`0.28`) |
| `right_ear` | `float` | `LeftPanel -> EyeTelemetryCard` | Monospaced Metric (`0.29`) |
| `avg_ear` | `float` | `LeftPanel -> EyeTelemetryCard` | Progress Fill Level + Text |
| `ear_threshold` | `float` | `LeftPanel -> EyeTelemetryCard` | Dashed Vertical Line (0.21) |
| `eye_state` | `str` | `LeftPanel -> EyeTelemetryCard` | Status Badge (`OPEN` / `CLOSED`) |
| `blink_count` | `int` | `LeftPanel -> EyeTelemetryCard` | Counter Badge (`142`) |
| `eye_closed_duration` | `float` | `LeftPanel -> EyeTelemetryCard` | Timer Metric (`0.0s`) |
| `mar` | `float` | `LeftPanel -> MouthTelemetryCard` | Progress Fill Level + Text |
| `mar_threshold` | `float` | `LeftPanel -> MouthTelemetryCard` | Dashed Vertical Line (0.55) |
| `mouth_state` | `str` | `LeftPanel -> MouthTelemetryCard` | Status Badge (`CLOSED`/`YAWN`)|
| `yawn_count` | `int` | `LeftPanel -> MouthTelemetryCard` | Counter Badge (`2`) |
| `mouth_open_duration` | `float` | `LeftPanel -> MouthTelemetryCard` | Timer Metric (`0.0s`) |
| `head_pose_pitch` | `float` | `RightPanel -> HeadPoseCard` | Reticle Y-Offset + Metric |
| `head_pose_yaw` | `float` | `RightPanel -> HeadPoseCard` | Reticle X-Offset + Metric |
| `head_pose_roll` | `float` | `RightPanel -> HeadPoseCard` | Reticle Line Tilt + Metric |
| `head_pose_valid` | `bool` | `RightPanel -> HeadPoseCard` | Reticle State / Badges |
| `drowsiness_score` | `float` | `RightPanel -> DecisionEngineCard`| Score Bar Gauge (`0 - 100`) |
| `decision_confidence` | `float` | `RightPanel -> DecisionEngineCard`| Confidence Fill Meter (`98%`)|
| `co_occurrences` | `dict` | `RightPanel -> DecisionEngineCard`| 3 Lit Signal Rectangles |
| `decision_reason` | `str` | `RightPanel -> DecisionEngineCard`| Wrapped Explanation Box |
| `event_logs` | `list` | `BottomDock -> EventTimelineStream`| Streaming Text Line Feed |
| `channel_status` | `dict` | `BottomDock -> SystemStatusCard` | Status Badges (HUD, Audio) |

---

## 5. Responsive Grid & Breakpoint Strategy

The layout provides graceful adaptation across common monitor resolutions:

```
[ UltraWide / 4K ]  ---->  [ Full HD Widescreen ]  ---->  [ Compact Laptop / Tablet ]
   (> 1920x1080)               (1920x1080 / 1440x900)             (1280x720 / 1024x768)
Full 3-Column Grid          Optimized Grid Standard            2-Column Collapsed Grid
```

### 5.1 Large Desktop Widescreen ($\ge 1920\times 1080\text{px}$)
* Full 3-column grid (`280px | 1fr | 320px`).
* Camera feed occupies maximum central area.

### 5.2 Standard Laptop Widescreen ($1366\times 768\text{px}$ to $1536\times 864\text{px}$)
* Compact 3-column grid (`240px | 1fr | 280px`).
* Card font sizes adjust slightly (`13px` headers, `20px` metrics).

### 5.3 Tablet / Low Resolution Viewports ($\le 1280\times 720\text{px}$)
* Media Query Breakpoint triggered (`@media (max-width: 1280px)`):
* Left and Right telemetry panels stack vertically into a 2-column layout:
```css
grid-template-columns: 300px 1fr;
grid-template-areas:
  "header  header"
  "left    center"
  "right   center"
  "bottom  bottom";
```

---

## 6. Strict AI & Backend Decoupling Guarantee

1. **Zero AI Code Alteration**: No logic inside `detection/` (`face_mesh.py`, `ear_calculator.py`, `mar_calculator.py`, `head_pose_estimator.py`, etc.) is altered.
2. **Zero Analytics Alteration**: Decision engine rules, threshold calculations, and statistics trackers in `analytics/` remain 100% untouched.
3. **Pure Presentational Contract**: The dashboard layout operates solely as a visual consumer of telemetry payloads produced by backend data structures.
