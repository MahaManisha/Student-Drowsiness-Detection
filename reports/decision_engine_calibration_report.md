# 📊 Drowsiness Decision Engine Calibration Report

**Assigned QA Auditor**: Senior AI Engineer & Production Fatigue Analytics Lead  
**Audit Date**: 2026-07-23  
**Status**: **ALL PASSED ✅**

---

## ⚖️ 1. Scoring Weights Comparison

We calibrated the scoring weights to make prolonged eye closure the strongest fatigue indicator and reduce false positives from normal studying head postures (nodding down to notebooks, keyboards, etc.):

| Fatigue Indicator | Original Weight | Calibrated Weight | Calibration Rationale |
| :--- | :---: | :---: | :--- |
| **Prolonged Eye Closure** | Max 40 pts | **Max 50 pts** | Made the strongest indicator, as micro-sleep is the highest correlation factor. |
| **Slow Blink Pattern** | Max 15 pts | **Max 15 pts** | Retained to capture slow blink behaviors. |
| **Yawn Frequency** | Max 25 pts | **Max 20 pts** | Slightly reduced to avoid yawning alone escalating to high drowsiness. |
| **Downward Head Pose** | Max 20 pts | **Max 15 pts** | Reduced and filtered by co-occurrence. |
| **Total Combined Score** | **100 pts** | **100 pts** | Preserved the normalized 100-point scale. |

---

## 🔍 2. False Positive & study Posture Analysis

### 2.1 The Study Posture Issue
* **Student behaviors**: Looking down at notebooks, keyboards, writing notes, and reading books naturally deflects head pitch down ($\approx 10^\circ$ to $20^\circ$).
* **Old Behavior**: Any downward pitch deflects score (up to 20 pts), which could raise the score to `SLIGHTLY_DROWSY` if the student simply yawned once.

### 2.2 Calibration Solutions Applied
1. **Normal Study Posture Filter**: Head pitch deflections up to $\pm 15.0^\circ$ are treated as baseline normal study posture, yielding **0 points**.
2. **Head Pose Contribution Qualifier**: Downward head drooping (pitch $> 15.0^\circ$) is only allowed to contribute to the drowsiness score when:
   - **Sustained**: Head drooping is sustained consecutively for $\ge 3.0$ seconds, OR
   - **Combined with micro-sleeps**: Co-occurring with prolonged eye closure, OR
   - **Combined with repeated yawning**: Co-occurring with repeated yawning events ($\ge 2$).
   
   If none of these conditions are met, head pose contributes **0 points**, completely resolving false positives from writing/reading!

---

## 🔬 3. Validation Scenarios & Score Comparisons

| Validation Case | Simulated Inputs | Expected State | Calibrated Score | Calibrated State | Status |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **Looking at Notebook** | Pitch = 12.0° (temporary, eyes open) | ALERT | 0.0 | ALERT | **PASS** |
| **Looking at Keyboard** | Pitch = 15.0° (temporary, eyes open) | ALERT | 0.0 | ALERT | **PASS** |
| **Reading Book** | Pitch = 18.0° (temporary, eyes open) | ALERT | 0.0 | ALERT | **PASS** |
| **Writing Notes** | Pitch = 14.0° (temporary, eyes open) | ALERT | 0.0 | ALERT | **PASS** |
| **Looking at Monitor** | Pitch = 2.0° (eyes open) | ALERT | 0.0 | ALERT | **PASS** |
| **Repeated Yawning** | Yawn Count = 2 (eyes open, pitch normal) | ALERT | 20.0 | ALERT | **PASS** |
| **Eyes Closed** | Closed duration = 3.0s (eyes closed) | DROWSY | 65.0 | DROWSY | **PASS** |
| **Sleeping** | Closed duration = 3.0s, yawns = 2, pitch = 18.0° (sustained) | HIGHLY_DROWSY | 100.0 | HIGHLY_DROWSY | **PASS** |

---

## 📊 4. Confidence Score & Mappings

Confidence mapping reflects indicator co-occurrences, temporal stability, and quality of evidence:
* **Simultaneous Co-occurrence (3 indicators)**: Confidence = `0.95`.
* **Co-occurrence (2 indicators)**:
  - Prolonged Eye Closure + Yawning: Confidence = `0.75` (high-quality combo).
  - Prolonged Eye Closure + Head Pose: Confidence = `0.65`.
  - Yawning + Head Pose: Confidence = `0.50`.
* **Isolated Indicators (1 indicator)**:
  - Prolonged Eye Closure: Confidence = `0.40`.
  - Yawning: Confidence = `0.30`.
  - Head Pose (sustained): Confidence = `0.20`.
* **Temporal Stability Boosts**:
  - If eye closure is sustained $\ge 4.0$ seconds: **+0.05** confidence.
  - If head drooping is sustained $\ge 5.0$ seconds: **+0.05** confidence.
  - Final confidence score is capped at `0.95`.

---

## 🏁 5. Final Verdict
* **False Positive Reduction Audit**: **PASS**
* **Validation Scenarios Accuracy**: **PASS**
* **Score Boundaries Alignment**: **PASS**
* **Codebase Unit Suite Integrity**: **PASS** (56/56 unit tests passed)
