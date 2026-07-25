# 📄 Student Drowsiness Detection System: Reports & Export Center Guide (Phase S8)

## 1. Executive Summary & Objective

Phase S8 implements the **Reports & Export Center** for the **Streamlit Web Dashboard**, allowing users to review completed student monitoring sessions, inspect 11 detailed result metrics, read AI natural language summaries, and download reports in CSV, JSON, and PDF formats.

As strictly mandated, the **AI backend detection engine (`detection/`, `analytics/`, `alerts/`, `camera/`, `logging/`, `models/`, `utils/`) remains 100% untouched and protected**.

---

## 2. Technical Component Architecture

```
[Session Telemetry Buffer]
            │
            ▼
┌────────────────────────────────────────────────────────────┐
│ 📋 SESSION REPORT OVERVIEW (SES_20260725_001)             │
│ Date: July 25, 2026 | Start: 09:24:00 | Duration: 00:18:15  │
│ Camera: Integrated WebCam (ID: 0)     | FPS: 30.0 FPS      │
└────────────────────────────────────────────────────────────┘
            │
            ▼
┌────────────────────────────────────────────────────────────┐
│ 📊 11 DETAILED SESSION RESULT METRICS                     │
│ Avg EAR  Avg MAR  Blinks  Yawns  Peak Score  Confidence    │
│ Alerts   Closure  Max Pitch  Max Yaw  Max Roll            │
└────────────────────────────────────────────────────────────┘
            │
            ▼
┌────────────────────────────────────────────────────────────┐
│ 🧠 AI EXECUTIVE SUMMARY NARRATIVE                          │
│ "The monitoring session lasted 18 minutes. The student... "│
└────────────────────────────────────────────────────────────┘
            │
            ▼
┌────────────────────────────────────────────────────────────┐
│ 📥 EXPORT CONTROLS                                         │
│ [ 📊 Export CSV ]   [ 📁 Export JSON ]   [ 📄 Export PDF ] │
└────────────────────────────────────────────────────────────┘
            │
            ▼
┌────────────────────────────────────────────────────────────┐
│ 📜 HISTORICAL SESSION REPORTS ARCHIVE                     │
│ Session 001 | July 25 | Duration: 01:24:15 | [Download]   │
│ Session 002 | July 24 | Duration: 00:45:10 | [Download]   │
└────────────────────────────────────────────────────────────┘
```

---

## 3. 11 Detailed Session Result Metrics Reference

| Result Metric | Source Key | Format / Unit | Description |
| :--- | :--- | :--- | :--- |
| **1. Average EAR** | `stats.average_ear` | Decimal (`0.285`) | Running average Eye Aspect Ratio |
| **2. Average MAR** | `stats.average_mar` | Decimal (`0.180`) | Running average Mouth Aspect Ratio |
| **3. Total Blinks** | `stats.blink_count` | Integer (`142 blinks`) | Cumulative blink count |
| **4. Total Yawns** | `stats.yawn_count` | Integer (`2 yawns`) | Cumulative yawn count |
| **5. Peak Risk Score** | `stats.highest_score` | Score (`12 / 100`) | Maximum drowsiness score reached |
| **6. Avg Confidence** | `decision_confidence`| Percentage (`98%`) | Average AI decision confidence |
| **7. Total Alerts** | Derived count | Integer (`3 alerts`) | Total alert warnings dispatched |
| **8. Max Closure** | `stats.longest_eye_closure`| Seconds (`0.00s`) | Longest continuous eye closure |
| **9. Max Pitch** | `head_pose_pitch` | Degrees (`+2.1°`) | Peak head pitch nod deflection |
| **10. Max Yaw** | `head_pose_yaw` | Degrees (`-1.4°`) | Peak head yaw turn deflection |
| **11. Max Roll** | `head_pose_roll` | Degrees (`+0.8°`) | Peak head roll tilt angle |

---

## 4. Download Export Format Specifications

Streamlit `st.download_button` triggers instant file downloads:
- **📊 Export CSV (`.csv`)**: Raw time-series telemetry table containing timestamps, EAR, MAR, risk scores, blinks, yawns, and states.
- **📁 Export JSON (`.json`)**: Structured hierarchical JSON document containing session metadata, result metrics, and event arrays.
- **📄 Export PDF (`.txt` / `.pdf`)**: Formatted plain text / PDF summary report formatted for print archiving.

---

## 5. Decoupling & Zero-Backend-Modification Verification

| Backend Module | File Path | Status | Verification Detail |
| :--- | :--- | :--- | :--- |
| **Session Logger** | `logging/session_logger.py` | **UNTOUCHED** | Log schema unmodified. |
| **Session Statistics** | `analytics/session_statistics.py` | **UNTOUCHED** | Stat accumulator logic unmodified. |
| **Decision Engine** | `analytics/decision_engine.py` | **UNTOUCHED** | Scoring rules unmodified. |
| **EAR Calculator** | `detection/ear_calculator.py` | **UNTOUCHED** | EAR math unmodified. |
| **MAR Calculator** | `detection/mar_calculator.py` | **UNTOUCHED** | MAR math unmodified. |
