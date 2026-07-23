# 📊 Temporal Eye Analyzer Validation Report

**Date**: 2026-07-23  
**Target Module**: `TemporalEyeAnalyzer` ([temporal_eye_analyzer.py](file:///c:/Users/akash/OneDrive/Desktop/TritonLab/Student-Drowsiness-Detection/detection/temporal_eye_analyzer.py))  
**Camera FPS Target**: `30.0 Hz`  
**Blink Boundaries**: `[2, 15]` frames (`0.067s` to `0.500s`)  
**Status**: ALL SCENARIOS PASSED ✅

---

## 🔍 Validation Summary

| Test Case | Scenario Description | Expected Blinks | Actual Blinks | Max Closed Duration | Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **S1** | Normal Blinking | 1 | 1 | 0.133 s | PASS |
| **S2** | Rapid Blinking | 3 | 3 | 0.000 s | PASS |
| **S3** | Long Eye Closure | 0 | 0 | 0.833 s | PASS |
| **S4** | Slow Blinking | 1 | 1 | 0.333 s | PASS |
| **S5** | Looking Away (UNKNOWN) | 0 | 0 | 0.000 s | PASS |
| **S6** | Face Lost Nested | 1 | 1 | 0.133 s | PASS |

---

## 📝 Detailed Scenario Analysis

### 1. Normal Blinking (S1)
* **Description**: Simulates a standard blink consisting of 10 open frames, 4 closed frames, and 10 open frames.
* **Peak Closure frames**: `4` (`0.133 s`).
* **Blink Counting**: Correctly registered exactly `1` blink upon reopening.
* **Counter Reset Behavior**: Frame counters and durations correctly reset to `0` once the eyes reopened.

### 2. Rapid Blinking (S2)
* **Description**: Simulates rapid successive blinks (closed for 2 frames, open for 3 frames, repeated 3 times).
* **Blink Counting**: Correctly registered exactly `3` blinks, confirming accuracy under high-frequency transitions.

### 3. Long Eye Closure / Microsleep (S3)
* **Description**: Simulates prolonged eye closure of 25 frames, exceeding the maximum allowed blink threshold of 15 frames.
* **Peak Closure duration**: `25 frames` (`0.833 s`).
* **Blink Counting**: Registered `0` blinks (correctly filtered out as a drowsiness/microsleep signature rather than a blink).
* **Reset Behavior**: Reset to `0` closed frames on eye opening.

### 4. Slow Blinking (S4)
* **Description**: Simulates a slow but valid blink of 10 closed frames.
* **Peak Closure duration**: `10 frames` (`0.333 s`).
* **Blink Counting**: Registered `1` blink upon reopening (since duration falls within the `[2, 15]` frame boundary).

### 5. Looking Away / UNKNOWN States (S5)
* **Description**: Simulates looking away from the camera for 15 frames (yielding `UNKNOWN` states).
* **State Verification**: The analyzer correctly ignored the `UNKNOWN` states, keeping closed frames at `0` and preserving the open frames count (`10`).
* **Blink Counting**: Registered `0` blinks.

### 6. Face Temporarily Lost during Closure (S6)
* **Description**: Simulates a face being lost for 3 frames (nested within a closure sequence of 2 closed frames before and 2 closed frames after).
* **State Verification**: The analyzer ignored the intermediate `UNKNOWN` states and successfully accumulated a total of `4 closed frames` (`0.133 s`).
* **Blink Counting**: Correctly registered exactly `1` blink upon eye reopening, confirming robustness to face mesh tracking dropout.

---

## 🏁 Final Verdict

* **Blink Count Accuracy**: **PASS**
* **Closed Frame Counting**: **PASS**
* **Duration Calculation**: **PASS**
* **Counter Reset Behavior**: **PASS**
* **Stability under Noisy/UNKNOWN Inputs**: **PASS**
