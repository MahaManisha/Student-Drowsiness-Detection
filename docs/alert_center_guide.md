# 🚨 Student Drowsiness Detection System: Real-Time Alert Center & System Health Guide (Phase S6)

## 1. Executive Summary & Objective

Phase S6 introduces a **Real-Time Alert Center**, a **Chronological Alert History Stream**, an **Audio Alert Status Indicator**, and a **System Health Diagnostics Panel** to the **Streamlit Web Dashboard**.

As strictly mandated, the **AI backend detection engine (`detection/`, `analytics/`, `alerts/`, `camera/`, `logging/`, `models/`, `utils/`) remains 100% untouched and protected**.

---

## 2. Technical Visual Architecture

```
[Raw Telemetry Payload from CameraManager]
            │
            ├───────────────────────────────┐
            ▼                               ▼
┌───────────────────────────────┐ ┌───────────────────────────────┐
│ 🚨 REAL-TIME ALERT CENTER     │ │ ⚙️ SYSTEM HEALTH DIAGNOSTICS  │
│ [🔊 Alarm Active] 🟢 NORMAL   │ │ Camera Feed:       ● Connected│
│                               │ │ AI Engine:         ● Active   │
│ ACTIVE WARNING BANNER         │ │ Decision Engine:   ● Evaluating│
│ "System operating normally"   │ │ Telemetry Pipeline:● 30.0 FPS │
│ Timestamp: 09:24:14           │ └───────────────────────────────┘
│ Duration: 0.0s | Severity: low│ 
└───────────────────────────────┘ 
            │                     
            ▼                     
┌───────────────────────────────┐ 
│ 📜 ALERT EVENT HISTORY        │ 
│ 🚀 [09:24:00] Live stream act.│ 
│ 👁️ [09:24:12] Blink detected   │ 
│ 👄 [09:24:18] Yawn completed  │ 
└───────────────────────────────┘ 
```

---

## 3. Severity Level & Animation Matrix

| Severity Level | System State | Border Accent | Animation Keyframe | UI Application |
| :--- | :--- | :--- | :--- | :--- |
| **🟢 NORMAL** | `ALERT` | Emerald `#10B981` | Static solid | Nominal monitoring, green banner border |
| **🟡 WARNING** | `SLIGHTLY_DROWSY` | Amber `#F59E0B` | `@keyframes slow-pulse` | Cautionary state, amber banner border |
| **🟠 DROWSY** | `DROWSY` | Orange `#F97316` | `@keyframes orange-pulse` | High risk state, orange banner border |
| **🔴 HIGHLY DROWSY** | `CRITICAL` | Crimson `#EF4444` | `@keyframes red-flash` | Critical state, flashing red warning banner |

---

## 4. System Health Diagnostic Matrix

The System Health panel tracks 4 operational metrics in real time:

| Diagnostic Item | Evaluation Logic | Active Green Output | Inactive Red Output |
| :--- | :--- | :--- | :--- |
| **Camera Feed** | `camera_connected == True` | `● Connected` | `● Disconnected` |
| **AI Engine** | `camera_connected and fps > 0` | `● Active` | `● Inactive` |
| **Decision Engine** | `ai_running and score in payload` | `● Evaluating` | `● Idle` |
| **Telemetry Pipeline** | `fps >= 10.0` | `● 30.0 FPS` | `● Stalled` |

---

## 5. Decoupling & Zero-Backend-Modification Verification

| Backend Module | File Path | Status | Verification Detail |
| :--- | :--- | :--- | :--- |
| **Alert Manager** | `alerts/alert_manager.py` | **UNTOUCHED** | Alert dispatch rules unmodified. |
| **Decision Engine** | `analytics/decision_engine.py` | **UNTOUCHED** | Drowsiness scoring rules unmodified. |
| **Camera Stream** | `camera/camera.py` | **UNTOUCHED** | OpenCV video capture unmodified. |
| **Session Logger** | `logging/session_logger.py` | **UNTOUCHED** | Event log schema unmodified. |
