# 🧠 Student Drowsiness Detection System: Explainable AI (XAI) Decision Panel Guide (Phase S5)

## 1. Executive Summary & Objective

Phase S5 introduces an **Explainable AI (XAI) Decision Panel** to the **Streamlit Web Dashboard**. The panel provides full transparency into *why* the AI engine made its current risk decision without altering any backend logic.

As strictly mandated, the **AI backend detection engine (`detection/`, `analytics/`, `alerts/`, `camera/`, `logging/`, `models/`, `utils/`) remains 100% untouched and protected**.

---

## 2. XAI Visual Architecture

```
[Raw Telemetry Payload from CameraManager]
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│ 🧠 AI DECISION ENGINE           [RISK: LOW]  🟢 ALERT       │
├─────────────────────────────────────────────────────────────┤
│               [ Plotly Circular Gauge: 12 / 100 ]           │
├─────────────────────────────────────────────────────────────┤
│ Decision Confidence: 98% [============================]     │
├─────────────────────────────────────────────────────────────┤
│ CONTRIBUTING AI SIGNALS                                     │
│  👁️ Eye Closure  [ ✖ ]         👄 Yawning  [ ✖ ]           │
│  👤 Head Pose    [ ✖ ]         ⚡ Blink Pattern [ ✖ ]       │
├─────────────────────────────────────────────────────────────┤
│ PRIMARY DECISION REASON                                     │
│  "Student alert. All telemetry metrics within nominal bounds"│
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Component Reference Table

| Visual Widget | Module File | Description | Dynamic Color Mapping |
| :--- | :--- | :--- | :--- |
| **Circular Gauge** | `gauge_component.py` | 2D Plotly gauge chart displaying Drowsiness Score ($0 \to 100$) | $<25$ Green, $25-50$ Amber, $50-75$ Orange, $>75$ Red |
| **Confidence Bar** | `confidence_bar.py` | Horizontal progress bar displaying decision confidence | Cyan gradient fill (`#0284C7` to `#38BDF8`) |
| **Risk Level Tag** | `decision_panel.py` | Automatic risk level classification badge | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| **Signal Indicators** | `signal_indicators.py` | 4-grid matrix for Eye Closure, Yawning, Head Pose, Blink Pattern | Active: Crimson highlight check (`✔`), Inactive: Grey cross (`✖`) |
| **Decision Reason** | `decision_panel.py` | Glassmorphic text box explaining current decision | Slate container with Emerald left border |

---

## 4. Risk Level & State Matrix

| System State | Score Range | Risk Level Tag | Badge Style | Primary Reason Focus |
| :--- | :--- | :--- | :--- | :--- |
| **`ALERT`** | $0 \to 24$ | `RISK: LOW` | 🟢 Emerald | Normal monitoring, metrics nominal |
| **`SLIGHTLY_DROWSY`**| $25 \to 49$ | `RISK: MEDIUM` | 🟡 Amber | Minor EAR dip or slight head turn |
| **`DROWSY`** | $50 \to 74$ | `RISK: HIGH` | 🟠 Orange | Extended closure or repeated yawns |
| **`HIGHLY_DROWSY`** | $75 \to 100$ | `RISK: CRITICAL` | 🔴 Crimson | Multi-modal co-occurrence alert |

---

## 5. Decoupling & Zero-Backend-Modification Verification

| Backend Module | File Path | Status | Verification Detail |
| :--- | :--- | :--- | :--- |
| **Decision Engine** | `analytics/decision_engine.py` | **UNTOUCHED** | Score rules & thresholds unmodified. |
| **EAR Calculator** | `detection/ear_calculator.py` | **UNTOUCHED** | EAR ratio math unmodified. |
| **MAR Calculator** | `detection/mar_calculator.py` | **UNTOUCHED** | MAR ratio math unmodified. |
| **Head Pose Estimator** | `detection/head_pose_estimator.py` | **UNTOUCHED** | Pose estimation math unmodified. |
| **Alert Manager** | `alerts/alert_manager.py` | **UNTOUCHED** | Alert channels unmodified. |
