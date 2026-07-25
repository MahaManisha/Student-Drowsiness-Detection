# 📈 Student Drowsiness Detection System: Comprehensive Session Analytics Guide (Phase S7)

## 1. Executive Summary & Objective

Phase S7 completes the visual analytics layer of the **Streamlit Web Dashboard**, introducing 8 Top KPI metric cards, 5 interactive Plotly charts, a Session Summary metadata panel, and an export-ready data schema (`CSV`/`PDF`/`JSON`).

As strictly mandated, the **AI backend detection engine (`detection/`, `analytics/`, `alerts/`, `camera/`, `logging/`, `models/`, `utils/`) remains 100% untouched and protected**.

---

## 2. Visual Component & Chart Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│ 📊 TOP 8 KEY PERFORMANCE INDICATOR (KPI) CARDS                   │
│ ⏱️ Duration  👁️ Blinks  👄 Yawns  🔥 Peak Score                   │
│ 📊 Avg EAR   📏 Avg MAR  ⏳ Max Close 🚨 Total Alerts            │
└──────────────────────────────────────────────────────────────────┘
            │
            ├───────────────────────┬───────────────────────┐
            ▼                       ▼                       ▼
 ┌───────────────────────┐ ┌───────────────────────┐ ┌───────────────────────┐
 │ 👁️ EAR Trend Line    │ │ 👄 MAR Trend Line    │ │ 🧠 Risk Score Trend   │
 │ Time vs EAR (Spline)  │ │ Time vs MAR (Spline)  │ │ Time vs Score (Area)  │
 └───────────────────────┘ └───────────────────────┘ └───────────────────────┘
            │                                               │
            ├───────────────────────┬───────────────────────┘
            ▼                       ▼
 ┌───────────────────────┐ ┌───────────────────────┐
 │ ⚡ Blink Frequency Bar│ │ 📊 Alert State Pie   │
 │ Time vs Blink Count   │ │ Donut Distribution    │
 └───────────────────────┘ └───────────────────────┘
            │
            ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │ 📋 SESSION SUMMARY & EXPORT METADATA SCHEMAS                    │
 └─────────────────────────────────────────────────────────────────┘
```

---

## 3. Top KPI Metric Cards Matrix

| KPI Metric Card | Telemetry Source Key | Format / Unit | Color Accent |
| :--- | :--- | :--- | :--- |
| **Session Duration** | `session_stats.total_session_time` | Monospaced (`01:24:15`) | Off-White `#F9FAFB` |
| **Total Blink Count** | `session_stats.blink_count` | Integer (`142 blinks`) | Sky Cyan `#38BDF8` |
| **Total Yawn Count** | `session_stats.yawn_count` | Integer (`2 yawns`) | Magenta `#EC4899` |
| **Highest Risk Score** | `session_stats.highest_score` | Score (`12 / 100`) | Emerald Green / Red |
| **Average EAR** | `session_stats.average_ear` | Decimal (`0.285`) | Mint Green `#10B981` |
| **Average MAR** | `session_stats.average_mar` | Decimal (`0.180`) | Pink `#EC4899` |
| **Max Eye Closure** | `session_stats.longest_eye_closure`| Seconds (`0.00s`) | Emerald / Red |
| **Total Alerts Triggered**| Derived event count | Integer (`3 alerts`) | Crimson Red `#EF4444` |

---

## 4. Plotly Interactive Charts

1. **EAR Trend Chart**:
   - X-axis: Time (`HH:MM:SS`)
   - Y-axis: EAR ratio ($0.0 \to 0.5$)
   - Threshold Marker: Red dashed line at $0.21$

2. **MAR Trend Chart**:
   - X-axis: Time (`HH:MM:SS`)
   - Y-axis: MAR ratio ($0.0 \to 1.0$)
   - Threshold Marker: Amber dashed line at $0.55$

3. **Drowsiness Score Progression**:
   - X-axis: Time (`HH:MM:SS`)
   - Y-axis: Risk Score ($0 \to 100$)
   - Fill: Cyan translucent area fill (`rgba(56, 189, 248, 0.15)`)

4. **Blink Frequency Stream**:
   - X-axis: Time (`HH:MM:SS`)
   - Y-axis: Blink Count per minute

5. **Alert State Distribution**:
   - Donut pie chart representing % time spent in `Normal`, `Warning`, `Drowsy`, and `Highly Drowsy` states.

---

## 5. Export-Ready Data Payload Schema

The `build_export_payload()` utility constructs a clean dictionary structure compatible with downstream CSV, PDF, or JSON exporters:

```json
{
  "session_summary": {
    "monitoring_started": "09:24:00",
    "monitoring_status": "ACTIVE",
    "total_runtime": "01:24:15",
    "longest_continuous_alert": "0.00s",
    "average_confidence": "98%",
    "peak_score": "12 / 100",
    "average_fps": "30.0 FPS"
  },
  "telemetry_records_count": 300,
  "telemetry_records": [
    {"timestamp": "09:24:01", "ear": 0.285, "mar": 0.180, "score": 12.0, "blinks": 142, "yawns": 2, "state": "ALERT"}
  ]
}
```

---

## 6. Decoupling & Zero-Backend-Modification Verification

| Backend Module | File Path | Status | Verification Detail |
| :--- | :--- | :--- | :--- |
| **Session Statistics** | `analytics/session_statistics.py` | **UNTOUCHED** | Stat accumulator logic unmodified. |
| **Decision Engine** | `analytics/decision_engine.py` | **UNTOUCHED** | Scoring rules unmodified. |
| **EAR Calculator** | `detection/ear_calculator.py` | **UNTOUCHED** | EAR math unmodified. |
| **MAR Calculator** | `detection/mar_calculator.py` | **UNTOUCHED** | MAR math unmodified. |
| **Session Logger** | `logging/session_logger.py` | **UNTOUCHED** | JSON Lines schema unmodified. |
