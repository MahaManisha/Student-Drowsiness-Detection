# 👤 Student Drowsiness Detection System: Head Pose Card Design Specification (Phase D4)

## 1. Executive Summary & Design Objective

Phase D4 establishes the technical design specification, visual component blueprints, circular compass mechanics, smooth motion interpolation, and color-coded state tracking for the **Modern Head Pose Telemetry Card** in the **Student Drowsiness Detection System Dashboard**.

The Head Pose Card visualizes 3D spatial orientation (Pitch, Yaw, Roll) derived from MediaPipe facial landmark solvePnP projections, providing real-time detection of head nodding, side slumping, or distraction.

As strictly mandated, the **Head Pose Estimator backend (`HeadPoseEstimator` in `detection/head_pose_estimator.py`), 3D facial model points, and solvePnP algorithms remain 100% untouched**.

---

## 2. Card Overview & Structural Wireframe

### 2.1 Component Wireframe

```
+-------------------------------------------------------------------+
| [👤 ICON] Head Pose Estimation                  [ POSE LATCHED ] |  <- Header + Status Badge
+-------------------------------------------------------------------+
|                                                                   |
|                      +---------------------+                      |
|                      |        +P (N)       |                      |
|                      |      /   |   \      |                      |
|                      |  -Y (W)--( + )--+Y(E)|  <- Mini Orientation|
|                      |      \   |   /      |     Compass Reticle  |
|                      |        -P (S)       |                      |
|                      +---------------------+                      |
|                                                                   |
|  Pitch (Tilt N/S): +2.1°   Yaw (Turn E/W): -1.4°   Roll: +0.8°    |  <- Numeric Metrics
+-------------------------------------------------------------------+
|  Status: Nominal Head Orientation (Within 5.0° Threshold)         |  <- Contextual Label
+-------------------------------------------------------------------+
```

---

## 3. Mini Orientation Compass & Circular Indicator

The card features a custom **$140\times 140\text{px}$ Graphical Mini Orientation Compass** combining pitch/yaw reticle crosshairs, concentric deflection rings, and roll tilt orientation lines.

### 3.1 Compass Structure Specifications
* **Outer Compass Diameter**: $140\text{px}$ (`border-radius: 50%`).
* **Crosshair Grid**:
  * Vertical Pitch Axis Line (Top: $+P$ Pitch Up, Bottom: $-P$ Pitch Down).
  * Horizontal Yaw Axis Line (Left: $-Y$ Yaw Left, Right: $+Y$ Yaw Right).
* **Concentric Deflection Rings**:
  * Inner Ring ($10^\circ$ Deflection Boundary - Radius: $35\text{px}$).
  * Outer Ring ($20^\circ$ Deflection Boundary - Radius: $65\text{px}$).
* **Cardinal Directional Labels**:
  * Top: `+P` (Pitch Up) | Bottom: `-P` (Pitch Down)
  * Left: `-Y` (Yaw Left) | Right: `+Y` (Yaw Right)

```
                       +P (Pitch Up)
                             |
                      +------+------+
                    /   10°  |  20°   \
                   |    +----+----+    |
     -Y (Yaw Left) |----|--( O )--|----| +Y (Yaw Right)
                   |    +----+----+    |
                    \        |        /
                      +------+------+
                             |
                       -P (Pitch Down)
```

---

## 4. Smooth Marker Movement & Coordinate Mapping Engine

The target marker dot $(x, y)$ moves smoothly within the circular compass, continuously reflecting real-time Pitch and Yaw deflections, while the active marker line tilts by the Roll angle.

### 4.1 2D Reticle Coordinate Mapping Formula
Assuming a max deflection of $20.0^\circ$ mapping to reticle radius $R = 65\text{px}$:

$$\Delta x = \left( \frac{\theta_{\text{yaw}}}{20.0^\circ} \right) \cdot R, \quad \Delta y = -\left( \frac{\theta_{\text{pitch}}}{20.0^\circ} \right) \cdot R$$

To prevent out-of-bounds clipping when head deflection exceeds $20^\circ$:

$$d = \sqrt{\Delta x^2 + \Delta y^2}$$

$$\text{If } d > R \implies \Delta x_{\text{clamped}} = \frac{\Delta x}{d} \cdot R, \quad \Delta y_{\text{clamped}} = \frac{\Delta y}{d} \cdot R$$

### 4.2 Marker Rendering & Motion Interpolation
* **Target Dot Position**:
  $$\text{Target Center} = \left( X_{\text{center}} + \Delta x_{\text{clamped}}, \, Y_{\text{center}} + \Delta y_{\text{clamped}} \right)$$
* **Roll Axis Indicator Line**:
  A line segment of length $L = 16\text{px}$ centered on the target dot and rotated by Roll angle $\theta_{\text{roll}}$:
  $$\Delta x_{\text{line}} = \frac{L}{2} \cdot \sin(\theta_{\text{roll}}), \quad \Delta y_{\text{line}} = \frac{L}{2} \cdot \cos(\theta_{\text{roll}})$$
* **Smooth CSS Motion Interpolation**:
  ```css
  .compass-target-marker {
    transition: transform 0.15s cubic-bezier(0.25, 0.1, 0.25, 1.0);
    will-change: transform;
  }
  ```

---

## 5. Color-Coded Status & Severity Threshold System

The tracking status badge, compass rings, and marker colors dynamically adapt according to head pose stability and tracking state:

```
[ POSE LATCHED ] ----> [ MODERATE DEFLECTION ] ----> [ SEVERE TILT ] ----> [ SEARCHING... ]
  Emerald (#10B981)        Amber (#F59E0B)           Orange (#F97316)       Crimson (#EF4444)
```

| Tracking / Deflection State | Pitch / Yaw Deflection | Status Pill Text | Marker Color | Compass Ring Stroke |
| :--- | :--- | :--- | :--- | :--- |
| **Nominal Latched Pose** | $\|P\|, \|Y\| \le 10^\circ$ | `[ POSE LATCHED ]` | `#10B981` (Teal) | `rgba(16, 185, 129, 0.4)` |
| **Moderate Head Turn/Nod**| $10^\circ < \|P\|, \|Y\| \le 18^\circ$ | `[ MODERATE NOD ]` | `#F59E0B` (Amber) | `rgba(245, 158, 11, 0.5)` |
| **Severe Downward Nod** | $\|P\|, \|Y\| > 18^\circ$ | `[ SEVERE TILT ]` | `#F97316` (Orange) | `rgba(249, 115, 22, 0.6)` |
| **Pose Lost / Searching** | Pose invalid (`valid=False`)| `[ SEARCHING... ]` | `#EF4444` (Red 'X')| `rgba(239, 68, 68, 0.6)` |

---

## 6. HTML / CSS Component Specifications (`HeadPoseCard.html`)

```html
<div class="telemetry-card pose-card" data-pose-status="LATCHED">
  <div class="card-header">
    <div class="header-title">
      <span class="card-icon">👤</span>
      <span class="title-text">Head Pose Estimation</span>
    </div>
    <div class="state-badge badge-latched">POSE LATCHED</div>
  </div>

  <!-- Mini Orientation Compass Visualizer -->
  <div class="compass-wrapper">
    <svg class="orientation-compass" width="140" height="140" viewBox="0 0 140 140">
      <!-- Background Circle & Deflection Rings -->
      <circle cx="70" cy="70" r="65" class="compass-ring outer-ring" />
      <circle cx="70" cy="70" r="35" class="compass-ring inner-ring" />

      <!-- Crosshair Axes -->
      <line x1="70" y1="5" x2="70" y2="135" class="axis-line" />
      <line x1="5" y1="70" x2="135" y2="70" class="axis-line" />

      <!-- Cardinal Direction Labels -->
      <text x="70" y="14" class="compass-label">P+</text>
      <text x="70" y="132" class="compass-label">P-</text>
      <text x="10" y="74" class="compass-label">Y-</text>
      <text x="130" y="74" class="compass-label">Y+</text>

      <!-- Dynamic Smooth Target Marker (Pitch: +2.1°, Yaw: -1.4°, Roll: +0.8°) -->
      <g class="compass-target-marker" style="transform: translate(65px, 63px);">
        <!-- Active Center Dot -->
        <circle cx="0" cy="0" r="4" class="marker-dot" />
        <!-- Roll Angle Tilt Line -->
        <line x1="-8" y1="0" x2="8" y2="0" class="marker-roll-line" style="transform: rotate(0.8deg);" />
      </g>
    </svg>
  </div>

  <!-- Numerical Telemetry Readouts -->
  <div class="pose-metrics-grid">
    <div class="metric-box">
      <span class="label">Pitch (Nod)</span>
      <span class="value mono">+2.1°</span>
    </div>
    <div class="metric-box">
      <span class="label">Yaw (Turn)</span>
      <span class="value mono">-1.4°</span>
    </div>
    <div class="metric-box">
      <span class="label">Roll (Tilt)</span>
      <span class="value mono">+0.8°</span>
    </div>
  </div>
</div>
```

---

## 7. CSS Styling Tokens

```css
/* Compass Container */
.compass-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 8px 0;
}

.orientation-compass {
  background: #14161F;
  border-radius: 50%;
  box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.6);
}

.compass-ring {
  fill: none;
  stroke: #2E3446;
  stroke-width: 1px;
}

.inner-ring {
  stroke-dasharray: 2, 2;
}

.axis-line {
  stroke: #2A2F40;
  stroke-width: 1px;
}

.compass-label {
  fill: #6B7280;
  font-family: var(--font-mono);
  font-size: 9px;
  text-anchor: middle;
  dominant-baseline: middle;
}

/* Dynamic Marker */
.marker-dot {
  fill: #10B981;
  box-shadow: 0 0 8px #10B981;
}

.marker-roll-line {
  stroke: #10B981;
  stroke-width: 2px;
  stroke-linecap: round;
}

/* Pose Metrics Grid */
.pose-metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.metric-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: rgba(20, 22, 31, 0.6);
  padding: 6px;
  border-radius: 6px;
}

.metric-box .label {
  font-family: var(--font-sans);
  font-size: 10px;
  color: #9CA3AF;
}

.metric-box .value {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 700;
  color: #F3F4F6;
}
```

---

## 8. Telemetry Data Binding Matrix

| Backend Telemetry Field Key | Data Type | Target UI Component Slot | Visual Representation |
| :--- | :--- | :--- | :--- |
| `head_pose_pitch` | `float` | `HeadPoseCard -> Pitch Metric & Y-Offset` | Monospaced Text (`+2.1°`) + Vertical Reticle Offset |
| `head_pose_yaw` | `float` | `HeadPoseCard -> Yaw Metric & X-Offset` | Monospaced Text (`-1.4°`) + Horizontal Reticle Offset |
| `head_pose_roll` | `float` | `HeadPoseCard -> Roll Metric & Line Tilt` | Monospaced Text (`+0.8°`) + Roll Axis Line Angle |
| `head_pose_valid` | `bool` | `HeadPoseCard -> Status Pill & Reticle Marker`| `[ POSE LATCHED ]` / `[ SEARCHING... ]` (Red 'X') |

---

## 9. Decoupling & Zero-Backend-Modification Verification

- **Pose Estimator Protection**: `HeadPoseEstimator` (`detection/head_pose_estimator.py`), MediaPipe FaceMesh landmark indices, 3D facial model points, and solvePnP math remain **100% untouched**.
- **Pure Presentational Contract**: The Head Pose Card strictly reads telemetry outputs and maps them visually to the compass reticle.
