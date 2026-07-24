# Student Drowsiness Detection System: Runtime Dashboard Design

This document details the visual and architectural design of the enhanced real-time runtime dashboard (HUD) implemented in Phase 12.2.

---

## 🎨 Design Philosophy & Aesthetics

The dashboard is designed to provide safety-critical monitoring data at a glance while maintaining high visual appeal and minimal performance overhead. It uses a **sleek dark mode overlay** to mimic advanced telemetry panels.

### 1. Color Palette (Sleek Dark Mode)
- **Background Panels**: Deep charcoal `(20, 20, 24)` with `80%` opacity to provide a high-contrast glassmorphic effect.
- **Borders & Dividers**: Charcoal-slate `(60, 60, 68)` for clean visual separation without distraction.
- **Labels & Captions**: Slate gray `(140, 140, 150)` for lower hierarchy text.
- **Value Readouts & Primary Text**: Soft off-white `(240, 240, 245)` for high readability.

### 2. State-Based Accent Colors
The system dynamically updates accent colors and widgets (pill badges, progress bars, and pose indicators) based on the current drowsiness state:
- **ALERT (Normal)**: Vivid Mint/Teal `(170, 230, 20)`
- **SLIGHTLY DROWSY**: Warm Yellow-Orange `(0, 215, 255)`
- **DROWSY**: Orange `(0, 140, 255)`
- **HIGHLY DROWSY (Critical)**: Crimson Red/Deep Coral `(80, 80, 250)`

---

## 📐 Layout Grid & Panel Segmentation

The layout is divided into four distinct screen zones, allowing all telemetry parameters to remain visible without clutter.

```
+---------------------------------------------------------------------------------+
|                                  HEADER PANEL                                   |
| [TITLE]                                             [SESSION TIME]   [FPS] [STATE]|
+---------------------------------------------------------------------------------+
|                               |                         |                       |
|                               |                         |                       |
|          LEFT PANEL           |                         |      RIGHT PANEL      |
|                               |                         |                       |
|   (Eyes & Mouth Telemetry)    |                         |  (Pose & Decision)    |
|   - EAR values                |     CAMERA PREVIEW      |  - Head Pose reticle  |
|   - EAR Progress Bar          |        FEED ZONE        |  - Drowsiness score   |
|   - Eye state & blinks        |                         |  - Confidence bar     |
|   - MAR values                |                         |  - Co-occurrence      |
|   - MAR Progress Bar          |                         |  - Wrapped reason     |
|   - Mouth state & yawns       |                         |                       |
|                               |                         |                       |
+---------------------------------------------------------------------------------+
|                                  FOOTER PANEL                                   |
| [EVENT LOG]                                                    [ALERTS STATUS]  |
+---------------------------------------------------------------------------------+
```

### 1. Header Panel
- **Dimensions**: Full width, height `60px`.
- **Left**: Core system title.
- **Right**: Active session timer (formatted as `MM:SS` or `HH:MM:SS`) and camera loop FPS.
- **Far Right**: A colored pill badge displaying the current drowsiness state.

### 2. Left Panel: Eyes & Mouth Telemetry
- **Dimensions**: Width `270px` (or `42%` of frame width on lower resolutions), height spans between header and footer.
- **Contents**:
  - Numerical readouts of Left, Right, and Average Eye Aspect Ratio (EAR).
  - Horizontal EAR progress bar with a vertical line marking the threshold.
  - Active eye state (Green `OPEN` / Red `CLOSED`) and temporal stats (Blink count, Closed duration).
  - Numerical Mouth Aspect Ratio (MAR).
  - Horizontal MAR progress bar with a vertical threshold line.
  - Active mouth state (Green `CLOSED` / Magenta `YAWNING`) and yawning stats (Yawn count, Open duration).

### 3. Right Panel: Pose & Decision Engine
- **Dimensions**: Symmetrical to the Left Panel, aligned to the right screen boundary.
- **Contents**:
  - **Head Pose Reticle**: A graphical crosshair target. A target dot moves in real-time mapping the pitch (vertical) and yaw (horizontal) deflections. A line tilted by the roll angle demonstrates tilt. Displays "SEARCHING" with a red 'X' if pose estimation is lost.
  - **Drowsiness Score Progress Bar**: A horizontal bar colored by state severity (0-100).
  - **Confidence Progress Bar**: Represents decision engine confidence.
  - **Co-occurrence Badges**: Three rectangular blocks that light up as active signals (eyes, mouth, pose) co-occur.
  - **Decision Explanation Box**: Displays the text explanation from the decision engine.

### 4. Footer Panel
- **Dimensions**: Full width, height `45px` at the bottom of the screen.
- **Left**: Latest event message recorded by the `AlertManager` (e.g. state transitions or alarm triggers).
- **Right**: Active channel statuses (HUD/Audio channels indicating `ACTIVE`, `READY`, or `DISABLED`).
- **Critical Warning Flashing**: If the state is `HIGHLY_DROWSY`, the footer panel background changes to warning red and border lines highlight to draw immediate attention.

---

## ⚡ Overlapping Prevention & Scaling

To guarantee readability across varying camera resolutions (e.g., 640x480, 1280x720):
1. **Dynamic Grid Coordinates**: Panel positions, margins, and sizes are calculated dynamically relative to `frame_width` and `frame_height`.
2. **Fixed Line Increments**: Values are drawn at sequential vertical offsets based on a constant line height (`20px`), guaranteeing text lines never overlap.
3. **Automated Text Wrapping**: Long strings (such as decision explanations) are automatically split using an OpenCV text measurement algorithm (`_wrap_text`) to fit within the width of the panel.

---

## 🚀 Performance & FPS Maintenance

To prevent rendering overhead from dropping the pipeline below the target 30 FPS:
1. **Single Blending Operation**: Instead of blending every panel individually, the visualizer creates panel boxes in a single pass and performs a single `cv2.addWeighted` call.
2. **No Deep Copies**: The visualizer performs drawing operations in-place on the input frame wherever possible, avoiding expensive memory allocation.
3. **No Heavy Calculations**: The visualizer only performs rendering. All metrics are calculated beforehand and passed as a prepared telemetry payload.
