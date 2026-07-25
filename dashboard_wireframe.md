# 📐 Student Drowsiness Detection System: Dashboard Wireframe (Phase D1)

## 1. Executive Summary & Layout Grid Overview

The **Student Drowsiness Detection System Monitoring Dashboard** is engineered as a high-density, real-time telemetry control panel. It presents real-time facial analytics, eye closure dynamics, mouth/yawn metrics, head pose spatial orientation, and decision engine risk assessments in a structured, ergonomic layout.

The overall interface follows a **5-Zone CSS Grid Architecture**:
1. **HEADER BAR**: System identification, session timer, pipeline FPS performance, and high-visibility alert status badge.
2. **LEFT TELEMETRY PANEL**: Dedicated analytical cards for Eye Telemetry (EAR) and Mouth Telemetry (MAR).
3. **CENTER VIEWPORT**: Prominent live camera preview with HUD mesh overlay, tracking reticle, and stream telemetry badges.
4. **RIGHT TELEMETRY PANEL**: Dedicated cards for Head Pose (Pitch/Yaw/Roll crosshair) and the Decision Engine (Drowsiness Score, Confidence, Co-occurrence, and Reason).
5. **BOTTOM DOCK**: Real-time Event Timeline log stream and System Status channel readiness indicators.

---

## 2. High-Level ASCII Structural Wireframe

```
+-------------------------------------------------------------------------------------------------------------------+
|                                                  HEADER BAR                                                       |
|  [📷 ICON] Student Drowsiness Detection System    [● LIVE]        ⏱️ Session: 01:24:15   ⚡ FPS: 30.0   [ STATE: ALERT ]|
+-------------------------------------------------------------------------------------------------------------------+
|                                      |                                         |                                  |
|         LEFT PANEL (280px)           |           CENTER VIEWPORT (1fr)         |        RIGHT PANEL (320px)        |
|                                      |                                         |                                  |
| +----------------------------------+ | +-------------------------------------+ | +------------------------------+ |
| | 👁️ EYE TELEMETRY                 | | | 📹 LIVE CAMERA FEED                 | | | 👤 HEAD POSE ESTIMATION      | |
| |                                  | | |                                     | | |                              | |
| |  Left EAR: 0.28   Right EAR: 0.29| | |  +-------------------------------+  | | |    +-------------------+     | |
| |  Avg EAR: 0.285                  | | |  |                               |  | | |    |         |         |     | |
| |  [====================|--------] | | |  |       FACIAL MESH VIEW        |  | | |    |-----( + )---------|     | |
| |  Threshold: 0.21                 | | |  |    (MediaPipe 478 Mesh)       |  | | |    |         |         |     | |
| |                                  | | |  |                               |  | | |    +-------------------+     | |
| |  Eye State:  [ OPEN (NORMAL) ]   | | |  +-------------------------------+  | | |  Pitch: +2.1°   Yaw: -1.4°   | |
| |  Total Blinks: 142               | | |                                     | | |  Roll:  +0.8°                | |
| |  Closed Duration: 0.0s           | | |  RES: 1280x720 | BUF: OPTIMAL | LATCH   | | |  Status: [ POSE LATCHED ]    | |
| +----------------------------------+ | +-------------------------------------+ | +------------------------------+ |
|                                      |                                         |                                  |
| +----------------------------------+ |                                         | +------------------------------+ |
| | 👄 MOUTH TELEMETRY               | |                                         | | 🧠 DECISION ENGINE           | |
| |                                  | |                                         | |                              | |
| |  MAR Value: 0.18                 | |                                         | |  Drowsiness Risk Score: 12   | |
| |  [========|--------------------] | |                                         | |  [==-----------------------] | |
| |  Threshold: 0.55                 | |                                         | |  Confidence: [ 98% ]         | |
| |                                  | |                                         | |                              | |
| |  Mouth State: [ CLOSED ]         | |                                         | |  Active Co-occurrences:      | |
| |  Total Yawns: 2                  | |                                         | |  [ EYE ] [ MOUTH ] [ POSE ]  | |
| |  Open Duration: 0.0s             | |                                         | |                              | |
| |                                  | |                                         | |  Explanation:                | |
| |                                  | |                                         | |  "Student alert. All metrics | |
| |                                  | |                                         | |   within normal parameters." | |
| +----------------------------------+ |                                         | +------------------------------+ |
+-------------------------------------------------------------------------------------------------------------------+
|                                                  BOTTOM DOCK                                                      |
| +-------------------------------------------------------------------+ +-----------------------------------------+ |
| | 📜 EVENT TIMELINE                                                 | | 🖥️ SYSTEM STATUS                       | |
| | [09:24:12] INFO: Session initialization complete.                 | | HUD: [ ACTIVE ]  Audio: [ READY ]     | |
| | [09:24:14] WARN: Brief EAR dip detected (0.20s).                  | | Logger: [ LOGGING ]                   | |
| +-------------------------------------------------------------------+ +-----------------------------------------+ |
+-------------------------------------------------------------------------------------------------------------------+
```

---

## 3. Zone-by-Zone Component Specifications

### 3.1 Header Bar Zone
* **Layout**: Full-width header spanning top grid boundary (`height: 64px`, `border-radius: 12px`, `padding: 12px 24px`).
* **Components**:
  * **Brand Title Section**: System icon (Eye/Shield symbol), main title `Student Drowsiness Detection System`, and a live status pulsing dot badge (`● MONITORING ACTIVE`).
  * **Telemetry Metric Group**:
    * **Session Timer**: Monospaced timestamp counter (`01:24:15`) formatted as `HH:MM:SS`.
    * **FPS Monitor**: Real-time processing speed readout (`30.0 FPS`) with green metric indicator.
    * **Alert Status Pill**: Large right-aligned pill badge displaying current system state with dynamic background fill:
      - `ALERT` (Emerald Teal `#10B981`)
      - `SLIGHTLY DROWSY` (Amber Gold `#F59E0B`)
      - `DROWSY` (Deep Orange `#F97316`)
      - `HIGHLY DROWSY` (Crimson Red `#EF4444` with subtle pulse animation)

```markdown
+-------------------------------------------------------------------------------------------------------------------+
| [📷] Student Drowsiness Detection System  [● LIVE]        ⏱️ Session: 01:24:15   ⚡ FPS: 30.0   [ STATE: ALERT ]|
+-------------------------------------------------------------------------------------------------------------------+
```

---

### 3.2 Left Telemetry Panel
* **Width**: Fixed `280px` column (`flex-direction: column`, `gap: 16px`).
* **Component 1: Eye Telemetry Card (`EyeTelemetryCard`)**:
  * **Header**: `👁️ Eye Telemetry` (14px Bold, Slate white `#F3F4F6`).
  * **Metric Readouts**:
    * Left EAR: `0.28` | Right EAR: `0.29`
    * Average EAR: `0.285` (Large 22px monospaced typography).
  * **Progress Gauge**:
    * Horizontal bar container (Track color: `#262B38`).
    * Dynamic fill level mapped to EAR (Fill range: 0.0 to 0.50).
    * Vertical dashed threshold line indicator at `EAR = 0.21`.
  * **Eye State Badge**:
    * `[ OPEN (NORMAL) ]` badge in green or `[ CLOSED ]` in red.
  * **Temporal Analytics**:
    * Total Blinks: `142`
    * Closed Duration: `0.0s` (Highlights if duration > 1.5s).

* **Component 2: Mouth Telemetry Card (`MouthTelemetryCard`)**:
  * **Header**: `👄 Mouth Telemetry` (14px Bold, Slate white `#F3F4F6`).
  * **Metric Readouts**:
    * Mouth Aspect Ratio (MAR): `0.18` (Large 22px monospaced typography).
  * **Progress Gauge**:
    * Horizontal bar container (Track color: `#262B38`).
    * Dynamic fill level mapped to MAR (Fill range: 0.0 to 1.00).
    * Vertical dashed threshold line indicator at `MAR = 0.55`.
  * **Mouth State Badge**:
    * `[ CLOSED ]` badge in green or `[ YAWNING ]` in magenta.
  * **Yawn Analytics**:
    * Total Yawn Count: `2`
    * Open Duration: `0.0s` (Tracks continuous open mouth window).

```markdown
+------------------------------------+
| 👁️ EYE TELEMETRY                  |
| Left: 0.28  Right: 0.29  Avg: 0.285|
| [====================|-----------] |
| Threshold: 0.21                    |
| State: [ OPEN (NORMAL) ]           |
| Total Blinks: 142   Closed: 0.0s   |
+------------------------------------+
| 👄 MOUTH TELEMETRY                 |
| MAR Value: 0.18                    |
| [========|-----------------------] |
| Threshold: 0.55                    |
| State: [ CLOSED ]                  |
| Total Yawns: 2      Open: 0.0s     |
+------------------------------------+
```

---

### 3.3 Center Viewport (Live Camera View)
* **Width**: Flexible `1fr` main viewport (`min-height: 480px`, `border-radius: 16px`, `overflow: hidden`).
* **Features**:
  * **Main Camera Feed Viewport**: Full-bleed live video preview displaying facial mesh tessellation, iris tracking points, and eye/mouth landmarks.
  * **Overlaid HUD Accents**:
    * **Top-Left Badge**: Stream Resolution (`1280x720 @ 30fps`).
    * **Top-Right Badge**: Processing Latency (`<12ms`).
    * **Bottom-Left Overlay**: Tracking Latch Status (`FACE MESH LATCHED - 478 PTS`).
    * **Bottom-Right Overlay**: Active Camera Device (`Camera ID: 0 (Built-in WebCam)`).

```markdown
+-------------------------------------------------------------+
| [📷 1280x720 @ 30FPS]                      [⚡ LATENCY: 12ms] |
|                                                             |
|                                                             |
|                    LIVE VIDEO FEED ZONE                     |
|                 (MediaPipe Face Mesh HUD)                   |
|                                                             |
|                                                             |
| [● MESH LATCHED - 478 PTS]            [📹 CAM: Integrated]  |
+-------------------------------------------------------------+
```

---

### 3.4 Right Telemetry Panel
* **Width**: Fixed `320px` column (`flex-direction: column`, `gap: 16px`).
* **Component 1: Head Pose Card (`HeadPoseCard`)**:
  * **Header**: `👤 Head Pose Estimation`.
  * **Reticle Visualizer**:
    * Square $120\times 120\text{px}$ crosshair target box.
    * Pitch (vertical deflection) & Yaw (horizontal deflection) mapped to target dot position $(x, y)$.
    * Roll angle rendered as a tilted directional axis line.
    * Out-of-bounds / Pose failure displays red cross `[ SEARCHING ]`.
  * **Numerical Deflection**:
    * Pitch: `+2.1°` | Yaw: `-1.4°` | Roll: `+0.8°`.
  * **Pose Latch Status**: `[ POSE LATCHED ]` badge.

* **Component 2: Decision Engine Card (`DecisionEngineCard`)**:
  * **Header**: `🧠 Decision Engine`.
  * **Drowsiness Risk Gauge**:
    * Score range: `0` to `100` (Monospaced display + dynamic color fill).
  * **Engine Confidence Bar**:
    * Decision confidence level (`98%`).
  * **Co-occurrence Indicators**:
    * 3 rectangular badges representing multi-modal signals:
      - `[ EYE ]` (Lit if EAR < 0.21 for extended frames)
      - `[ MOUTH ]` (Lit if MAR > 0.55 for extended frames)
      - `[ POSE ]` (Lit if head pitch/yaw exceeds threshold)
  * **Wrapped Decision Reason**:
    * Natural language text box explaining active evaluation:
      *"Student alert. All metrics within normal parameters."*

```markdown
+-----------------------------------+
| 👤 HEAD POSE ESTIMATION           |
|   +---------------------------+   |
|   |             |             |   |
|   |----------( + )------------|   |
|   |             |             |   |
|   +---------------------------+   |
| Pitch: +2.1°  Yaw: -1.4°  Roll: 0.8°|
| Status: [ POSE LATCHED ]          |
+-----------------------------------+
| 🧠 DECISION ENGINE                |
| Drowsiness Risk Score: 12 / 100   |
| [==-----------------------------] |
| Confidence: 98%                   |
| Signals: [ EYE ] [ MOUTH ] [ POSE]|
| Explanation:                      |
| "Student alert. All metrics within|
|  normal parameters."              |
+-----------------------------------+
```

---

### 3.5 Bottom Dock (Event Timeline & System Status)
* **Height**: `120px` bottom dock container divided into a 2-column flex area (`gap: 16px`).
* **Component 1: Event Timeline Stream (Flex 1)**:
  * **Header**: `📜 Event Timeline`.
  * **Chronological Log Feed**: Scrollable/streaming log list displaying events with timestamp, severity level, and description:
    * `[09:24:12] INFO: Session initialization complete.`
    * `[09:24:14] WARN: Brief EAR dip detected (0.20s).`
    * `[09:24:28] INFO: Blink rate nominal (14 blinks/min).`
* **Component 2: System Status Readiness (Width: 320px)**:
  * **Header**: `🖥️ System Status`.
  * **Channel Status Pills**:
    * HUD Overlay: `[ ACTIVE ]` (Green)
    * Audio Synthesizer: `[ READY ]` (Blue)
    * Session Logger: `[ LOGGING ]` (Green)
  * **Warning Banner Zone**: Flashes warning strip if alert state escalates to `HIGHLY_DROWSY`.

```markdown
+-------------------------------------------------------------------------------------------------------------------+
| 📜 EVENT TIMELINE                                                 | 🖥️ SYSTEM STATUS                             |
| [09:24:12] INFO: Session initialization complete.                 | HUD Overlay:        [ ACTIVE ]            |
| [09:24:14] WARN: Brief EAR dip detected (0.20s).                  | Audio Synthesizer:  [ READY ]             |
| [09:24:28] INFO: Blink rate nominal (14 blinks/min).              | Session Logger:     [ LOGGING ]           |
+-------------------------------------------------------------------------------------------------------------------+
```

---

## 4. Spacing & Card Layout Rules
1. **Container Margin & Padding**: `16px` uniform outer padding.
2. **Card Outer Radius**: `12px` for standard panels, `16px` for main camera viewport and header container.
3. **Card Inter-Element Gap**: `16px` between main columns, `12px` between stacked vertical cards.
4. **Card Shadow**: `0 10px 25px -5px rgba(0, 0, 0, 0.5)` for depth elevation.
