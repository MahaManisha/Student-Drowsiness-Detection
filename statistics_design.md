# 📈 Student Drowsiness Detection System: Session Statistics Dashboard Specification (Phase D7)

## 1. Executive Summary & Design Objective

Phase D7 establishes the technical design specification, component layout grid, typography scale, visual micro-badges, and telemetry slot bindings for the **Session Statistics Panel** in the **Student Drowsiness Detection System Dashboard**.

The Session Statistics Panel aggregates session-wide diagnostics into **9 Professional Telemetry Cards**, presenting long-term session performance, facial aperture averages, peak risk events, and attentiveness time distributions.

As strictly mandated, the **Session Statistics backend (`SessionStatisticsTracker` in `analytics/session_statistics.py`) and JSON log exporter remain 100% untouched**.

---

## 2. Session Statistics Grid Architecture

The statistics panel uses a responsive **3-Column Grid Layout** (`grid-template-columns: repeat(3, 1fr)`, `gap: 16px`).

### 2.1 Panel Wireframe & Card Placement

```
+---------------------------------------------------------------------------------------------------+
| 📈 SESSION STATISTICS SUMMARY                                                                     |
+-----------------------------------+-----------------------------------+---------------------------+
| ⏱️ SESSION DURATION                | 👁️ BLINK COUNT                     | 👄 YAWN COUNT             |
| 01:24:15                          | 142 blinks                        | 2 yawns                   |
| Status: ACTIVE MONITORING         | Rate: 16.8 blinks/min             | Frequency: 1.4 yawns/hr   |
+-----------------------------------+-----------------------------------+---------------------------+
| 📊 AVERAGE EAR                    | 📏 AVERAGE MAR                    | 🔥 HIGHEST SCORE          |
| 0.285                             | 0.180                             | 12 / 100                  |
| Baseline: 0.21 (Thresh)           | Baseline: 0.55 (Thresh)           | Peak Severity: NOMINAL    |
+-----------------------------------+-----------------------------------+---------------------------+
| ⏳ LONGEST EYE CLOSURE            | 🛡️ TIME IN ALERT                  | ⚠️ TIME IN DROWSY         |
| 0.00s                             | 01:20:00 (95.2%)                  | 00:04:15 (4.8%)           |
| Threshold: < 1.5s                 | [=======================-------] | [==---------------------] |
+-----------------------------------+-----------------------------------+---------------------------+
```

---

## 3. Card-by-Card Detailed Specifications

### 3.1 Card 1: ⏱️ Session Duration
* **Icon Header**: `⏱️ Session Duration` (14px Bold `--font-sans`).
* **Primary Metric**: `01:24:15` (Monospaced 24px Bold `--font-mono`, `#F3F4F6`).
* **Sub-Badge**: `[ ● LIVE SESSION ]` (Green status pill badge `#10B981`).
* **Data Source**: Calculated as `current_time - session_start_time`.

### 3.2 Card 2: 👁️ Blink Count
* **Icon Header**: `👁️ Blink Count` (14px Bold `--font-sans`).
* **Primary Metric**: `142 blinks` (Monospaced 24px Bold `--font-mono`, `#F3F4F6`).
* **Sub-Badge**: `Rate: 16.8 / min` (Cyan metric badge `#38BDF8`).
* **Data Source**: Synchronized directly from `SessionStatisticsTracker.blink_count`.

### 3.3 Card 3: 👄 Yawn Count
* **Icon Header**: `👄 Yawn Count` (14px Bold `--font-sans`).
* **Primary Metric**: `2 yawns` (Monospaced 24px Bold `--font-mono`, `#F3F4F6`).
* **Sub-Badge**: `Freq: 1.4 / hr` (Subtle grey text `#9CA3AF`).
* **Data Source**: Synchronized directly from `SessionStatisticsTracker.yawn_count`.

### 3.4 Card 4: 📊 Average EAR
* **Icon Header**: `📊 Average EAR` (14px Bold `--font-sans`).
* **Primary Metric**: `0.285` (Monospaced 24px Bold `--font-mono`, `#38BDF8`).
* **Sub-Badge**: `Threshold: 0.21` (Dashed indicator baseline).
* **Data Source**: Running session average $\sum(\text{avg\_ear}) / N$.

### 3.5 Card 5: 📏 Average MAR
* **Icon Header**: `📏 Average MAR` (14px Bold `--font-sans`).
* **Primary Metric**: `0.180` (Monospaced 24px Bold `--font-mono`, `#38BDF8`).
* **Sub-Badge**: `Threshold: 0.55` (Dashed indicator baseline).
* **Data Source**: Running session average $\sum(\text{mar}) / N$.

### 3.6 Card 6: 🔥 Highest Score
* **Icon Header**: `🔥 Highest Score` (14px Bold `--font-sans`).
* **Primary Metric**: `12 / 100` (Monospaced 24px Bold `--font-mono`, `#10B981` in nominal, `#EF4444` if $>75$).
* **Sub-Badge**: `Peak Severity: NOMINAL` (Dynamic alert severity label).
* **Data Source**: Tracked peak $\max(\text{highest\_score}, \text{score})$.

### 3.7 Card 7: ⏳ Longest Eye Closure
* **Icon Header**: `⏳ Longest Eye Closure` (14px Bold `--font-sans`).
* **Primary Metric**: `0.00s` (Monospaced 24px Bold `--font-mono`, `#F3F4F6`).
* **Sub-Badge**: `Threshold: < 1.5s` (Highlights red if peak duration $> 1.5\text{s}$).
* **Data Source**: Tracked peak $\max(\text{longest\_eye\_closure}, \text{consecutive\_closed\_duration})$.

### 3.8 Card 8: 🛡️ Time in ALERT
* **Icon Header**: `🛡️ Time in ALERT` (14px Bold `--font-sans`).
* **Primary Metric**: `01:20:00` (Monospaced 20px Bold `--font-mono`, `#10B981`).
* **Percentage Badge & Bar**: `95.2%` session ratio + Emerald Teal ratio progress meter.
* **Data Source**: Accumulated duration spent in `DrowsinessState.ALERT`.

### 3.9 Card 9: ⚠️ Time in DROWSY
* **Icon Header**: `⚠️ Time in DROWSY` (14px Bold `--font-sans`).
* **Primary Metric**: `00:04:15` (Monospaced 20px Bold `--font-mono`, `#F97316`).
* **Percentage Badge & Bar**: `4.8%` session ratio + Orange/Crimson ratio progress meter.
* **Data Source**: Accumulated duration spent in `SLIGHTLY_DROWSY`, `DROWSY`, and `HIGHLY_DROWSY` states.

---

## 4. Universal Card Styling Tokens & Geometry

```css
/* Card Container */
.stat-card {
  background: rgba(26, 29, 40, 0.85);
  backdrop-filter: blur(12px);
  border: 1px solid #2E3446;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 12px;
  box-shadow: 0 8px 24px -4px rgba(0, 0, 0, 0.4);
  transition: border-color 0.3s ease, transform 0.2s ease;
}

.stat-card:hover {
  border-color: #454E69;
  transform: translateY(-2px);
}

/* Header */
.stat-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-sans);
  font-size: 13px;
  font-weight: 700;
  color: #9CA3AF;
}

/* Metric Display */
.stat-value {
  font-family: var(--font-mono);
  font-size: 24px;
  font-weight: 800;
  color: #F3F4F6;
  line-height: 1.1;
}

.stat-value-emerald { color: #10B981; }
.stat-value-cyan    { color: #38BDF8; }
.stat-value-orange  { color: #F97316; }
.stat-value-crimson { color: #EF4444; }

/* Sub-Badge Footer */
.stat-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
  color: #6B7280;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.stat-ratio-bar {
  height: 6px;
  background: #2A2F40;
  border-radius: 4px;
  overflow: hidden;
  margin-top: 4px;
}
```

---

## 5. HTML Component Blueprint (`SessionStatisticsPanel.html`)

```html
<div class="statistics-panel-grid">
  <!-- Card 1: Session Duration -->
  <div class="stat-card">
    <div class="stat-card-header">
      <span class="stat-title">⏱️ Session Duration</span>
      <span class="badge-pill badge-emerald">LIVE</span>
    </div>
    <div class="stat-value mono">01:24:15</div>
    <div class="stat-footer">
      <span>Started at 08:00:00</span>
      <span class="text-emerald">ACTIVE</span>
    </div>
  </div>

  <!-- Card 2: Blink Count -->
  <div class="stat-card">
    <div class="stat-card-header">
      <span class="stat-title">👁️ Blink Count</span>
      <span class="badge-tag">16.8 / min</span>
    </div>
    <div class="stat-value mono">142 <span class="unit">blinks</span></div>
    <div class="stat-footer">
      <span>Temporal Window: 30s</span>
      <span class="text-cyan">NOMINAL</span>
    </div>
  </div>

  <!-- Card 3: Yawn Count -->
  <div class="stat-card">
    <div class="stat-card-header">
      <span class="stat-title">👄 Yawn Count</span>
      <span class="badge-tag">1.4 / hr</span>
    </div>
    <div class="stat-value mono">2 <span class="unit">yawns</span></div>
    <div class="stat-footer">
      <span>Completed Yawns</span>
      <span>NORMAL</span>
    </div>
  </div>

  <!-- Card 4: Average EAR -->
  <div class="stat-card">
    <div class="stat-card-header">
      <span class="stat-title">📊 Average EAR</span>
      <span class="badge-tag">Baseline: 0.21</span>
    </div>
    <div class="stat-value stat-value-cyan mono">0.285</div>
    <div class="stat-footer">
      <span>Session Mean EAR</span>
      <span class="text-cyan">STABLE</span>
    </div>
  </div>

  <!-- Card 5: Average MAR -->
  <div class="stat-card">
    <div class="stat-card-header">
      <span class="stat-title">📏 Average MAR</span>
      <span class="badge-tag">Baseline: 0.55</span>
    </div>
    <div class="stat-value stat-value-cyan mono">0.180</div>
    <div class="stat-footer">
      <span>Session Mean MAR</span>
      <span class="text-cyan">STABLE</span>
    </div>
  </div>

  <!-- Card 6: Highest Score -->
  <div class="stat-card">
    <div class="stat-card-header">
      <span class="stat-title">🔥 Highest Score</span>
      <span class="badge-tag">Peak Risk</span>
    </div>
    <div class="stat-value stat-value-emerald mono">12 <span class="max-denom">/ 100</span></div>
    <div class="stat-footer">
      <span>Max Drowsiness Score</span>
      <span class="text-emerald">LOW RISK</span>
    </div>
  </div>

  <!-- Card 7: Longest Eye Closure -->
  <div class="stat-card">
    <div class="stat-card-header">
      <span class="stat-title">⏳ Longest Eye Closure</span>
      <span class="badge-tag">&lt; 1.5s Thresh</span>
    </div>
    <div class="stat-value mono">0.00s</div>
    <div class="stat-footer">
      <span>Peak Closure Window</span>
      <span>NORMAL</span>
    </div>
  </div>

  <!-- Card 8: Time in ALERT -->
  <div class="stat-card">
    <div class="stat-card-header">
      <span class="stat-title">🛡️ Time in ALERT</span>
      <span class="badge-ratio text-emerald">95.2%</span>
    </div>
    <div class="stat-value stat-value-emerald mono">01:20:00</div>
    <div class="stat-ratio-bar">
      <div class="fill-emerald" style="width: 95.2%;"></div>
    </div>
  </div>

  <!-- Card 9: Time in DROWSY -->
  <div class="stat-card">
    <div class="stat-card-header">
      <span class="stat-title">⚠️ Time in DROWSY</span>
      <span class="badge-ratio text-orange">4.8%</span>
    </div>
    <div class="stat-value stat-value-orange mono">00:04:15</div>
    <div class="stat-ratio-bar">
      <div class="fill-orange" style="width: 4.8%;"></div>
    </div>
  </div>
</div>
```

---

## 6. Telemetry Data Binding Matrix

| Backend Telemetry Field Key | Data Type | Target UI Component Slot | Visual Representation |
| :--- | :--- | :--- | :--- |
| `total_session_time` | `float` | `StatCard 1 -> Session Duration` | Monospaced Text (`01:24:15`) |
| `blink_count` | `int` | `StatCard 2 -> Blink Count` | Counter Text (`142 blinks`) |
| `yawn_count` | `int` | `StatCard 3 -> Yawn Count` | Counter Text (`2 yawns`) |
| `average_ear` | `float` | `StatCard 4 -> Average EAR` | Monospaced Ratio (`0.285`) |
| `average_mar` | `float` | `StatCard 5 -> Average MAR` | Monospaced Ratio (`0.180`) |
| `highest_score` | `float` | `StatCard 6 -> Highest Score` | Peak Score Metric (`12 / 100`) |
| `longest_eye_closure` | `float` | `StatCard 7 -> Longest Eye Closure`| Monospaced Timer (`0.00s`) |
| `state_times["ALERT"]` | `float` | `StatCard 8 -> Time in ALERT` | Duration + Percentage Meter |
| `state_times["DROWSY"]` | `float` | `StatCard 9 -> Time in DROWSY` | Duration + Percentage Meter |

---

## 7. Decoupling & Zero-Backend-Modification Verification

- **Analytics Core Protection**: `SessionStatisticsTracker` (`analytics/session_statistics.py`), state transition calculators, running sum accumulators, and JSON export file writers remain **100% untouched**.
- **Pure Presentational Contract**: The Session Statistics Panel acts purely as a presentational consumer of computed statistics dictionaries.
