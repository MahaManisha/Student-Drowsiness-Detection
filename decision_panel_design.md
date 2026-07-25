# 🧠 Student Drowsiness Detection System: AI Decision Card Design Specification (Phase D5)

## 1. Executive Summary & Design Objective

Phase D5 establishes the technical design specification, visual component blueprints, animated gauges, typographic scale, and color-coded state tracking for the **AI Decision Card** in the **Student Drowsiness Detection System Dashboard**.

The AI Decision Card acts as the central intelligence hub of the monitoring dashboard. It synthesizes real-time inputs from eye tracking, mouth dynamics, and head pose estimation into an overall Drowsiness Risk Score ($0 \to 100$), decision confidence level, multi-modal co-occurrence signal indicators, and a natural language decision explanation.

As strictly mandated, the **Decision Engine backend (`StudentDrowsinessDecisionEngine` in `detection/decision_engine.py`), scoring rules, co-occurrence matrices, and explanation algorithms remain 100% untouched**.

---

## 2. Card Overview & Structural Wireframe

### 2.1 Component Wireframe

```
+-------------------------------------------------------------------+
| [🧠 ICON] Decision Engine                               [ ALERT ] |  <- Header + State Badge
+-------------------------------------------------------------------+
|                                                                   |
|   DROWSINESS RISK SCORE:   12 / 100                               |  <- Large Typography
|   +-----------------------------------------------------------+   |
|   |====-------------------------------------------------------|   |  <- Animated Score Bar
|   +-----------------------------------------------------------+   |
|                                                                   |
|   Decision Confidence: 98%                                        |
|   +-----------------------------------------------------------+   |
|   |=======================================================----|   |  <- Confidence Bar
|   +-----------------------------------------------------------+   |
|                                                                   |
|   Active Co-occurrences:                                          |
|   [ EYE: OFF ]       [ MOUTH: OFF ]       [ POSE: OFF ]           |  <- Signal Badges
|                                                                   |
|   Primary Decision Reason:                                        |
|   +-----------------------------------------------------------+   |
|   | "Student alert. All telemetry metrics (EAR: 0.285,        |   |  <- Reason Section
|   |  MAR: 0.180, Pose: 2.1°) within nominal bounds."          |   |
|   +-----------------------------------------------------------+   |
+-------------------------------------------------------------------+
```

---

## 3. Typography & Metric Display Architecture

The card leverages a high-contrast typographic scale to make safety-critical scores immediately readable at a glance.

### 3.1 Typographic Scale & Hierarchy

| UI Element | CSS Class | Font Size | Weight | Font Stack | Visual Role |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Card Header Title** | `.title-text` | `14px` | `700` (Bold) | `--font-sans` | Card section label |
| **Alert State Badge** | `.badge-state` | `12px` | `700` (Bold) | `--font-sans` | Top-right severity pill |
| **Score Value Display**| `.score-number`| `28px` | `800` (ExtraBold)| `--font-mono` | Prominent risk score |
| **Score Label** | `.score-label` | `12px` | `600` (SemiBold)| `--font-sans` | Label above score bar |
| **Confidence Readout** | `.confidence-val`| `13px` | `700` (Bold) | `--font-mono` | Confidence percentage |
| **Signal Badge Text** | `.signal-text` | `11px` | `700` (Bold) | `--font-sans` | Co-occurrence badge text |
| **Explanation Text** | `.reason-text` | `12px` | `400` (Regular)| `--font-sans` | Natural language explanation |

---

## 4. Animated Score Bar & Confidence Gauge Engine

### 4.1 Drowsiness Risk Score Bar
* **Range**: $0$ (Fully Alert) to $100$ (Critically Drowsy).
* **Track Height**: $12\text{px}$ with `border-radius: 6px`.
* **Fill Color Mapping**:
  - Score $0 \to 25$: Emerald Teal (`#10B981`)
  - Score $26 \to 50$: Amber Gold (`#F59E0B`)
  - Score $51 \to 75$: Vivid Orange (`#F97316`)
  - Score $76 \to 100$: Crimson Red (`#EF4444`)
* **Smooth Fill Animation**:
  ```css
  .score-fill-bar {
    height: 100%;
    border-radius: 6px;
    transition: width 0.35s cubic-bezier(0.4, 0.0, 0.2, 1), background-color 0.3s ease;
    will-change: width, background-color;
  }
  ```

### 4.2 Decision Engine Confidence Meter
* **Range**: $0\%$ to $100\%$.
* **Track Height**: $8\text{px}$ with `border-radius: 4px`.
* **Fill Styling**: Cyan-blue gradient fill (`linear-gradient(90deg, #0284C7, #38BDF8)`).

---

## 5. Color-Coded State Severity System

The card's background border, top badge, progress fill, and ambient glow dynamically update based on four drowsiness states:

```
[ ALERT / NORMAL ] ----> [ SLIGHTLY DROWSY ] ----> [ DROWSY ] ----> [ HIGHLY DROWSY (CRITICAL) ]
  Teal (#10B981)           Amber (#F59E0B)         Orange (#F97316)        Crimson (#EF4444)
```

| Drowsiness State | Score Range | Primary Hex Code | RGB Value | Card Glow & Border Effect |
| :--- | :--- | :--- | :--- | :--- |
| **`ALERT` (Normal)** | $0 - 25$ | `#10B981` | `rgb(16, 185, 129)` | Subtle Teal border glow |
| **`SLIGHTLY DROWSY`**| $26 - 50$ | `#F59E0B` | `rgb(245, 158, 11)` | Warm Amber border highlight |
| **`DROWSY`** | $51 - 75$ | `#F97316` | `rgb(249, 115, 22)` | Deep Orange alert border |
| **`HIGHLY DROWSY`** | $76 - 100$ | `#EF4444` | `rgb(239, 68, 68)` | Pulsing Crimson Red warning stroke |

---

## 6. Multi-Modal Co-occurrence Signal Badges

To provide immediate visibility into which facial telemetry channels triggered a state escalation, the card displays 3 rectangular co-occurrence signal blocks:

1. **`[ EYE ]` Badge**: Lights up when Eye Aspect Ratio (EAR) closure threshold is breached.
2. **`[ MOUTH ]` Badge**: Lights up when Mouth Aspect Ratio (MAR) yawn threshold is breached.
3. **`[ POSE ]` Badge**: Lights up when Head Pose pitch/yaw deflection threshold is breached.

```
Active Co-occurrences:
+-------------------+  +-------------------+  +-------------------+
|  [👁️ EYE: ACTIVE] |  |  [👄 MOUTH: OFF]  |  |  [👤 POSE: OFF]   |
+-------------------+  +-------------------+  +-------------------+
 (Lit Red/Orange)        (Dim Charcoal)         (Dim Charcoal)
```

---

## 7. Primary Decision Reason Container

The **Decision Reason Section** is styled as a prominent glassmorphic text box that displays the real-time natural language explanation generated by the decision engine.

* **Styling**: `background: rgba(20, 22, 31, 0.70)`, `border-left: 3px solid var(--state-color)`, `padding: 12px`, `border-radius: 6px`.
* **Example Explanations**:
  - *Alert State*: `"Student alert. All telemetry metrics (EAR: 0.285, MAR: 0.180, Pose: 2.1°) within nominal bounds."*
  - *Drowsy State*: `"Elevated drowsiness risk (Score: 68/100). Co-occurring EAR closure (0.18s) and head pitch deflection detected."*

---

## 8. HTML / CSS Component Specifications (`DecisionEngineCard.html`)

```html
<div class="telemetry-card decision-card" data-state="ALERT">
  <!-- Card Header -->
  <div class="card-header">
    <div class="header-title">
      <span class="card-icon">🧠</span>
      <span class="title-text">Decision Engine</span>
    </div>
    <div class="state-badge badge-alert">ALERT</div>
  </div>

  <!-- Large Drowsiness Risk Score Display -->
  <div class="score-display-wrapper">
    <div class="score-header">
      <span class="score-label">DROWSINESS RISK SCORE</span>
      <div class="score-number-group">
        <span class="score-number mono-xl">12</span>
        <span class="score-max">/ 100</span>
      </div>
    </div>

    <!-- Animated Score Progress Bar -->
    <div class="progress-track score-track">
      <div class="score-fill-bar fill-teal" style="width: 12%;"></div>
    </div>
  </div>

  <!-- Confidence Meter Bar -->
  <div class="confidence-wrapper">
    <div class="confidence-header">
      <span class="label">Decision Confidence</span>
      <span class="confidence-val mono">98%</span>
    </div>
    <div class="progress-track confidence-track">
      <div class="confidence-fill-bar" style="width: 98%;"></div>
    </div>
  </div>

  <!-- Multi-Modal Co-occurrence Badges -->
  <div class="cooccurrence-section">
    <span class="section-label">ACTIVE SIGNAL TRIGGERS</span>
    <div class="signal-badges-grid">
      <div class="signal-badge signal-off" id="sig-eye">
        <span class="sig-icon">👁️</span> EYE
      </div>
      <div class="signal-badge signal-off" id="sig-mouth">
        <span class="sig-icon">👄</span> MOUTH
      </div>
      <div class="signal-badge signal-off" id="sig-pose">
        <span class="sig-icon">👤</span> POSE
      </div>
    </div>
  </div>

  <!-- Primary Decision Reason Box -->
  <div class="reason-section">
    <span class="reason-header-label">PRIMARY DECISION REASON</span>
    <div class="reason-box">
      <p class="reason-text">
        "Student alert. All telemetry metrics (EAR: 0.285, MAR: 0.180, Pose: 2.1°) within nominal bounds."
      </p>
    </div>
  </div>
</div>
```

---

## 9. CSS Styling Tokens

```css
/* Score Typography */
.mono-xl {
  font-family: var(--font-mono);
  font-size: 28px;
  font-weight: 800;
  color: #F3F4F6;
  line-height: 1;
}

.score-max {
  font-family: var(--font-mono);
  font-size: 14px;
  color: #6B7280;
  margin-left: 4px;
}

.score-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 6px;
}

/* Progress Meters */
.score-track {
  height: 12px;
  background: #2A2F40;
  border-radius: 6px;
  overflow: hidden;
}

.confidence-track {
  height: 8px;
  background: #2A2F40;
  border-radius: 4px;
  overflow: hidden;
}

.confidence-fill-bar {
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, #0284C7, #38BDF8);
  transition: width 0.3s ease;
}

/* Co-occurrence Badges */
.signal-badges-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 4px;
}

.signal-badge {
  padding: 6px 8px;
  border-radius: 6px;
  font-family: var(--font-sans);
  font-size: 11px;
  font-weight: 700;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  transition: all 0.3s ease;
}

.signal-off {
  background: rgba(20, 22, 31, 0.6);
  color: #6B7280;
  border: 1px solid #2E3446;
}

.signal-active {
  background: rgba(239, 68, 68, 0.25);
  color: #EF4444;
  border: 1px solid rgba(239, 68, 68, 0.6);
  box-shadow: 0 0 10px rgba(239, 68, 68, 0.3);
}

/* Reason Box */
.reason-box {
  background: rgba(20, 22, 31, 0.75);
  border-left: 3px solid #10B981;
  border-radius: 4px 6px 6px 4px;
  padding: 10px 12px;
  margin-top: 4px;
}

.reason-text {
  font-family: var(--font-sans);
  font-size: 12px;
  line-height: 1.5;
  color: #D1D5DB;
  margin: 0;
}
```

---

## 10. Telemetry Data Binding Matrix

| Backend Telemetry Field Key | Data Type | Target UI Component Slot | Visual Representation |
| :--- | :--- | :--- | :--- |
| `drowsiness_score` | `float` | `DecisionCard -> Drowsiness Score` | Large Text (`12`) + Score Bar Fill |
| `drowsiness_state` | `str` | `DecisionCard -> State Badge & Borders`| Colored Badge (`ALERT`) + Accent Glow |
| `decision_confidence` | `float` | `DecisionCard -> Confidence Meter` | Percentage Text (`98%`) + Meter Fill |
| `co_occurrences` | `dict` | `DecisionCard -> Co-occurrence Badges` | Lit/Dim Badges (`EYE`, `MOUTH`, `POSE`) |
| `decision_reason` | `str` | `DecisionCard -> Reason Section` | Natural Language Paragraph Text |

---

## 11. Decoupling & Zero-Backend-Modification Verification

- **Decision Engine Protection**: `StudentDrowsinessDecisionEngine` (`detection/decision_engine.py`), state transition matrices, weight values, and explanation generators remain **100% untouched**.
- **Pure Presentational Contract**: The AI Decision Card strictly reads decision engine telemetry outputs and maps them visually to score meters, signal badges, and explanation boxes.
