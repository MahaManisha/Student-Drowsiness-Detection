# 📊 Student Drowsiness Detection System: Telemetry Cards Design Specification (Phase D3)

## 1. Executive Summary & Design Objective

Phase D3 establishes the technical design system, visual component blueprints, color coding standards, and UI slot bindings for the **Left Panel Modern Telemetry Cards** in the **Student Drowsiness Detection System Dashboard**.

The telemetry cards transform complex real-time facial analytics (Eye Aspect Ratio, Mouth Aspect Ratio, temporal closure tracking, and yawn frequencies) into intuitive visual metrics.

As strictly mandated, the **backend detection logic, mathematical calculators (`EARCalculator`, `MARCalculator`), and analytics engines remain 100% untouched**.

---

## 2. Card Design System Specifications

### 2.1 Universal Geometry & Styling Tokens

| Styling Attribute | CSS Token / Value | Visual Application Scope |
| :--- | :--- | :--- |
| **Card Outer Radius** | `border-radius: 12px` (`--radius-card`) | Outer border curve for all telemetry cards |
| `--bg-card` Surface | `#1A1D28` / `rgba(26, 29, 40, 0.85)` | Card background surface with backdrop blur |
| `--border-subtle` | `1px solid #2E3446` | Subtle charcoal card outline stroke |
| **Internal Padding** | `padding: 16px` | Uniform 8pt spatial grid card internal margin |
| **Element Row Gap** | `gap: 12px` | Vertical spacing between sub-widgets |
| **Progress Track Radius**| `border-radius: 6px` (`--radius-track`) | Rounded ends for progress bar tracks & meters |
| **Status Pill Radius** | `border-radius: 9999px` (`--radius-pill`) | Full pill geometry for active state badges |
| **Elevation Shadow** | `0 8px 24px -4px rgba(0, 0, 0, 0.4)` | Card depth drop shadow |

### 2.2 Color Coding Palette & State Severity Mapping

Element accents, progress bar meters, state pills, and telemetry highlights dynamically adapt based on four severity states:

```
[ ALERT / NORMAL ] ----> [ SLIGHTLY DROWSY ] ----> [ DROWSY ] ----> [ HIGHLY DROWSY (CRITICAL) ]
  Emerald (#10B981)        Amber (#F59E0B)         Orange (#F97316)        Crimson (#EF4444)
```

| Severity State | Accent Color | Hex Token | RGB Value | Card Accent Scope |
| :--- | :--- | :--- | :--- | :--- |
| **`ALERT` (Normal)** | Emerald Teal | `#10B981` | `rgb(16, 185, 129)` | Progress bar meter, state badge background, nominal values |
| **`SLIGHTLY DROWSY`**| Amber Gold | `#F59E0B` | `rgb(245, 158, 11)` | Progress bar warning meter, cautionary state badge |
| **`DROWSY`** | Vivid Orange | `#F97316` | `rgb(249, 115, 22)` | Elevated risk progress meter, orange state badge |
| **`HIGHLY DROWSY`** | Crimson Red | `#EF4444` | `rgb(239, 68, 68)` | Threshold breach meter, pulsing red badge, closure warning |

---

## 3. Card 1: 👁️ Eye Analysis Telemetry Card

The **Eye Analysis Card** provides real-time monitoring of Eye Aspect Ratio (EAR), eye open/closed classification, total blink count, and continuous eye closure duration.

### 3.1 Structural Component Wireframe

```
+-------------------------------------------------------------------+
| [👁️ ICON] Eye Analysis                         [ OPEN (NORMAL) ] |  <- Header + State Badge
+-------------------------------------------------------------------+
|  Left EAR: 0.280   Right EAR: 0.290             Avg EAR: 0.285    |  <- Numeric Readouts
|  +-------------------------------------------------------------+  |
|  |=========================|-----------------------------------|  |  <- Progress Bar
|  +-------------------------------------------------------------+  |
|                            ^ Threshold: 0.21                      |  <- Threshold Line
+-------------------------------------------------------------------+
|  Blink Count: 142 blinks                    Closed Time: 0.0s     |  <- Temporal Analytics
+-------------------------------------------------------------------+
```

### 3.2 Detailed Field Specifications

1. **Card Header**:
   - **Vector Icon**: `👁️` Eye icon (Emerald Teal fill `#10B981`).
   - **Section Title**: `Eye Analysis` (14px Bold, `--font-sans`, Color `#F3F4F6`).
   - **State Badge**: Dynamic status pill badge aligned to the top-right:
     - `OPEN (NORMAL)` (Emerald Teal background `rgba(16, 185, 129, 0.20)`, Text `#10B981`).
     - `CLOSED` (Crimson Red background `rgba(239, 68, 68, 0.25)`, Text `#EF4444`).

2. **EAR Metric Readout & Gauge**:
   - **Numerical Readouts**:
     - `Left EAR`: Monospaced 12px text (`0.280`).
     - `Right EAR`: Monospaced 12px text (`0.290`).
     - `Avg EAR`: Monospaced 20px Bold text (`0.285`).
   - **Progress Gauge Meter**:
     - Track Height: `10px`, Track Color `#2A2F40`, Radius `6px`.
     - Fill Level: Mapped to $\text{EAR}$ range ($0.00 \to 0.50$). $\text{Fill Ratio} = \frac{\text{Avg EAR}}{0.50} \times 100\%$.
     - Fill Color: Emerald Teal `#10B981` when $\text{EAR} \ge 0.21$; Crimson Red `#EF4444` when $\text{EAR} < 0.21$.
     - **Threshold Marker**: Dashed vertical white indicator line at $\text{EAR} = 0.21$ ($\text{Ratio} = 42\%$).

3. **Temporal Eye Metrics**:
   - **Blink Count**: `Blink Count: 142` (Monospaced 13px SemiBold `#F3F4F6` with counter badge).
   - **Closed Duration**: `Closed Time: 0.0s` (Highlights red if duration exceeds $1.5\text{s}$).

### 3.3 HTML / Component Template Spec (`EyeAnalysisCard.html`)

```html
<div class="telemetry-card eye-card" data-state="ALERT">
  <div class="card-header">
    <div class="header-title">
      <span class="card-icon">👁️</span>
      <span class="title-text">Eye Analysis</span>
    </div>
    <div class="state-badge badge-open">OPEN (NORMAL)</div>
  </div>

  <div class="metric-section">
    <div class="ear-readouts">
      <span class="sub-metric">Left EAR: <strong class="mono">0.280</strong></span>
      <span class="sub-metric">Right EAR: <strong class="mono">0.290</strong></span>
      <span class="primary-metric">Avg EAR: <strong class="mono-lg">0.285</strong></span>
    </div>

    <!-- Progress Bar with Threshold Marker -->
    <div class="progress-container">
      <div class="progress-track">
        <div class="progress-fill fill-emerald" style="width: 57%;"></div>
        <div class="threshold-line" style="left: 42%;" title="Threshold: 0.21"></div>
      </div>
      <div class="progress-labels">
        <span>0.00</span>
        <span class="thresh-label">Thresh: 0.21</span>
        <span>0.50</span>
      </div>
    </div>
  </div>

  <div class="temporal-footer">
    <div class="temporal-item">
      <span class="label">Blink Count</span>
      <span class="value mono">142</span>
    </div>
    <div class="temporal-item">
      <span class="label">Closed Time</span>
      <span class="value mono alert-closed">0.0s</span>
    </div>
  </div>
</div>
```

---

## 4. Card 2: 👄 Mouth Analysis Telemetry Card

The **Mouth Analysis Card** tracks Mouth Aspect Ratio (MAR), yawning aperture states, total yawn frequencies, and continuous mouth open duration.

### 4.1 Structural Component Wireframe

```
+-------------------------------------------------------------------+
| [👄 ICON] Mouth Analysis                               [ CLOSED ] |  <- Header + State Badge
+-------------------------------------------------------------------+
|  Mouth Aspect Ratio (MAR):                          0.180         |  <- Numeric Readout
|  +-------------------------------------------------------------+  |
|  |=========|---------------------------------------------------|  |  <- Progress Bar
|  +-------------------------------------------------------------+  |
|            ^ Threshold: 0.55                                      |  <- Threshold Line
+-------------------------------------------------------------------+
|  Yawn Count: 2 yawns                         Open Time: 0.0s      |  <- Temporal Analytics
+-------------------------------------------------------------------+
```

### 4.2 Detailed Field Specifications

1. **Card Header**:
   - **Vector Icon**: `👄` Mouth icon (Teal fill `#10B981` in closed state, Magenta `#EC4899` in yawn state).
   - **Section Title**: `Mouth Analysis` (14px Bold, `--font-sans`, Color `#F3F4F6`).
   - **State Badge**: Dynamic status pill badge aligned to top-right:
     - `CLOSED` (Emerald Teal background `rgba(16, 185, 129, 0.20)`, Text `#10B981`).
     - `YAWNING` (Magenta/Crimson background `rgba(236, 72, 153, 0.25)`, Text `#EC4899` with pulse glow).

2. **MAR Metric Readout & Gauge**:
   - **Numerical Readout**:
     - `Mouth Aspect Ratio (MAR)`: Monospaced 20px Bold text (`0.180`).
   - **Progress Gauge Meter**:
     - Track Height: `10px`, Track Color `#2A2F40`, Radius `6px`.
     - Fill Level: Mapped to $\text{MAR}$ range ($0.00 \to 1.00$). $\text{Fill Ratio} = \frac{\text{MAR}}{1.00} \times 100\%$.
     - Fill Color: Emerald Teal `#10B981` when $\text{MAR} \le 0.55$; Magenta `#EC4899` when $\text{MAR} > 0.55$.
     - **Threshold Marker**: Dashed vertical white indicator line at $\text{MAR} = 0.55$ ($\text{Ratio} = 55\%$).

3. **Temporal Yawn Metrics**:
   - **Yawn Count**: `Yawn Count: 2` (Monospaced 13px SemiBold `#F3F4F6` with counter badge).
   - **Open Duration**: `Open Time: 0.0s` (Tracks continuous open mouth window).

### 4.3 HTML / Component Template Spec (`MouthAnalysisCard.html`)

```html
<div class="telemetry-card mouth-card" data-state="CLOSED">
  <div class="card-header">
    <div class="header-title">
      <span class="card-icon">👄</span>
      <span class="title-text">Mouth Analysis</span>
    </div>
    <div class="state-badge badge-closed">CLOSED</div>
  </div>

  <div class="metric-section">
    <div class="mar-readout">
      <span class="label">Mouth Aspect Ratio (MAR)</span>
      <span class="primary-metric mono-lg">0.180</span>
    </div>

    <!-- Progress Bar with Threshold Marker -->
    <div class="progress-container">
      <div class="progress-track">
        <div class="progress-fill fill-emerald" style="width: 18%;"></div>
        <div class="threshold-line" style="left: 55%;" title="Threshold: 0.55"></div>
      </div>
      <div class="progress-labels">
        <span>0.00</span>
        <span class="thresh-label">Thresh: 0.55</span>
        <span>1.00</span>
      </div>
    </div>
  </div>

  <div class="temporal-footer">
    <div class="temporal-item">
      <span class="label">Yawn Count</span>
      <span class="value mono">2</span>
    </div>
    <div class="temporal-item">
      <span class="label">Open Time</span>
      <span class="value mono">0.0s</span>
    </div>
  </div>
</div>
```

---

## 5. CSS Component Styling Rules

```css
/* Card Container */
.telemetry-card {
  background: rgba(26, 29, 40, 0.85);
  backdrop-filter: blur(12px);
  border: 1px solid #2E3446;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-shadow: 0 8px 24px -4px rgba(0, 0, 0, 0.4);
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
}

/* Card Header */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-sans);
  font-size: 14px;
  font-weight: 700;
  color: #F3F4F6;
}

/* Dynamic State Badge */
.state-badge {
  padding: 4px 10px;
  border-radius: 9999px;
  font-family: var(--font-sans);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.badge-open, .badge-closed {
  background: rgba(16, 185, 129, 0.18);
  color: #10B981;
  border: 1px solid rgba(16, 185, 129, 0.4);
}

.badge-yawning, .badge-closed-alert {
  background: rgba(239, 68, 68, 0.22);
  color: #EF4444;
  border: 1px solid rgba(239, 68, 68, 0.5);
  animation: pulse-badge 1.5s infinite;
}

/* Progress Bar & Threshold */
.progress-container {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.progress-track {
  position: relative;
  height: 10px;
  background: #2A2F40;
  border-radius: 6px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 6px;
  transition: width 0.15s ease-out, background-color 0.3s ease;
}

.fill-emerald { background-color: #10B981; }
.fill-amber   { background-color: #F59E0B; }
.fill-orange  { background-color: #F97316; }
.fill-crimson { background-color: #EF4444; }

.threshold-line {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background-color: #FFFFFF;
  box-shadow: 0 0 4px rgba(255, 255, 255, 0.8);
}

.progress-labels {
  display: flex;
  justify-content: space-between;
  font-family: var(--font-mono);
  font-size: 10px;
  color: #6B7280;
}

/* Temporal Footer */
.temporal-footer {
  display: flex;
  justify-content: space-between;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.temporal-item {
  display: flex;
  flex-direction: column;
}

.temporal-item .label {
  font-family: var(--font-sans);
  font-size: 11px;
  color: #9CA3AF;
}

.temporal-item .value {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
  color: #F3F4F6;
}
```

---

## 6. Telemetry Data Binding Matrix

The UI components bind directly to backend telemetry structures without altering any detection calculations:

| Telemetry Data Field | Data Source | UI Card Target | Rendering Format |
| :--- | :--- | :--- | :--- |
| `left_ear` | `EARCalculator` | `EyeAnalysisCard -> Left EAR` | `0.280` (3 decimals) |
| `right_ear` | `EARCalculator` | `EyeAnalysisCard -> Right EAR` | `0.290` (3 decimals) |
| `avg_ear` | `EARCalculator` | `EyeAnalysisCard -> Avg EAR` | `0.285` + Progress Fill |
| `ear_threshold` | `config.EAR_THRESHOLD` | `EyeAnalysisCard -> Threshold` | Dashed Line at `0.21` |
| `eye_state` | `EyeStateClassifier` | `EyeAnalysisCard -> State Badge` | `[ OPEN ]` / `[ CLOSED ]` |
| `blink_count` | `TemporalEyeAnalyzer` | `EyeAnalysisCard -> Blink Count`| Counter Number (`142`) |
| `eye_closed_duration` | `TemporalEyeAnalyzer` | `EyeAnalysisCard -> Closed Time` | Timer Format (`0.0s`) |
| `mar` | `MARCalculator` | `MouthAnalysisCard -> MAR` | `0.180` + Progress Fill |
| `mar_threshold` | `config.MAR_THRESHOLD` | `MouthAnalysisCard -> Threshold`| Dashed Line at `0.55` |
| `mouth_state` | `YawnDetector` | `MouthAnalysisCard -> State Badge`| `[ CLOSED ]` / `[ YAWN ]` |
| `yawn_count` | `YawnDetector` | `MouthAnalysisCard -> Yawn Count`| Counter Number (`2`) |
| `mouth_open_duration` | `YawnDetector` | `MouthAnalysisCard -> Open Time` | Timer Format (`0.0s`) |

---

## 7. Decoupling & Zero-Backend-Modification Verification

- **Detector Protection**: `EyeLandmarkExtractor`, `MouthLandmarkExtractor`, `EARCalculator`, `MARCalculator`, `EyeStateClassifier`, `TemporalEyeAnalyzer`, and `YawnDetector` remain **100% untouched**.
- **Pure Data Binding**: The telemetry cards act strictly as presentational consumers of computed telemetry fields.
