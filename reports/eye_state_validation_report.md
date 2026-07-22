# 📊 Eye State Classification Validation Report

**Date**: 2026-07-22  
**Target Classifier Module**: `EyeStateClassifier` ([eye_state_classifier.py](file:///c:/Users/akash/OneDrive/Desktop/TritonLab/Student-Drowsiness-Detection/detection/eye_state_classifier.py))  
**Active Classification Threshold**: `0.250`  
**Status**: ALL PASSED ✅

---

## 🔍 Validation Summary

| Test Case | Scenario Description | Tested Metrics | Oscillations | Status |
| :--- | :--- | :--- | :---: | :---: |
| **S1** | Eyes Fully Open | Stable EAR, state remains `OPEN` | 0 | PASS |
| **S2** | Natural Blinking | Proper state transition `OPEN` -> `CLOSED` -> `OPEN` | 2 | PASS |
| **S3** | Eyes Intentionally Closed | Stable EAR, state remains `CLOSED` | 0 | PASS |
| **S4** | Low Lighting (Noisy Landmarks) | Landmark coordinate noise resilience | 0 | PASS |
| **S5** | Different Distances (Scales) | Scale-invariance of EAR ratios | 0 | PASS |

---

## 📝 Detailed Scenario Analysis

### 1. Eyes Fully Open (S1)
* **Description**: Simulates 50 continuous frames of static open eyes.
* **Mean EAR**: `0.4000` (Standard Deviation: `0.0000`)
* **Classification State**: Correctly classified as `OPEN` for all 50 frames.
* **Oscillation Verification**: `0` state transitions detected.

### 2. Natural Blinking (S2)
* **Description**: Simulates a standard blink sequence (rapid eye closure and reopening within a few frames).
* **State Transition Log**: `OPEN, OPEN, OPEN, OPEN, CLOSED, CLOSED, OPEN, OPEN`
* **Verification**: The state correctly transitioned from `OPEN` to `CLOSED` and cleanly back to `OPEN`.
* **Oscillation Verification**: Exactly `2` clean transitions detected (re-entry to open state is clean with no rapid oscillation).

### 3. Eyes Intentionally Closed (S3)
* **Description**: Simulates 50 continuous frames of stationary closed eyes.
* **Mean EAR**: `0.0200` (Standard Deviation: `0.0000`)
* **Classification State**: Correctly classified as `CLOSED` for all 50 frames.
* **Oscillation Verification**: `0` state transitions detected.

### 4. Low Lighting / Noise Resilience (S4)
* **Description**: Simulates landmark coordinate jitter caused by weak lighting. Random Gaussian noise (std = 0.3 pixels) is added to coordinates over 100 frames.
* **Mean EAR**: `0.4069` (Standard Deviation: `0.0347`)
* **Classification State**: Due to the high margin of the open eye EAR (~0.40) over the threshold (0.25), the state remains stable as `OPEN`.
* **Oscillation Verification**: `0` rapid state oscillations detected under normal noise.

### 5. Different Distances / Scale Invariance (S5)
* **Description**: Simulates subjects sitting closer or further from the camera by scaling landmark coordinates by factors of 0.5x, 1.0x, and 2.5x.
* **Calculated EAR Ratios**:
  * **Scale 0.5x** (Far/Close): Open EAR = `0.4000` (State: `EyeState.OPEN`), Closed EAR = `0.0200` (State: `EyeState.CLOSED`), Invariant = `True`
  * **Scale 1.0x** (Far/Close): Open EAR = `0.4000` (State: `EyeState.OPEN`), Closed EAR = `0.0200` (State: `EyeState.CLOSED`), Invariant = `True`
  * **Scale 2.5x** (Far/Close): Open EAR = `0.4000` (State: `EyeState.OPEN`), Closed EAR = `0.0200` (State: `EyeState.CLOSED`), Invariant = `True`

* **Verification**: Because the EAR is a ratio of distances:
  $$\text{EAR} = \frac{\|P_2 - P_6\| + \|P_3 - P_5\|}{2.0 \cdot \|P_1 - P_4\|}$$
  Scaling coordinates scaling-factors out perfectly, making the classifier strictly **scale-invariant**.
