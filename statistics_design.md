# Session Statistics Tracking: Design Specification

This document details the architectural design and calculations behind the `SessionStatisticsTracker` module implemented in Phase 12.4.

---

## 📊 Tracked Metrics & Calculation Logic

The module accumulates raw tracking parameters from the video capture loop on a per-frame basis and aggregates them into high-level session diagnostics.

| Metric | Unit | Calculation Logic |
| :--- | :--- | :--- |
| **Total Session Time** | Seconds | Calculated as `current_time - session_start_time`. |
| **Average EAR** | Ratio | Running average: $\sum(\text{avg\_ear}) / \text{frame\_count}$. Frames with lost tracking are ignored. |
| **Average MAR** | Ratio | Running average: $\sum(\text{mar}) / \text{frame\_count}$. Frames with lost tracking are ignored. |
| **Blink Count** | Total Count | Synchronized directly from the `TemporalEyeAnalyzer` blink counter. |
| **Yawn Count** | Total Count | Synchronized directly from the `YawnDetector` completed yawn counter. |
| **Highest Score** | Score (0-100) | Maintained as: $\max(\text{highest\_score}, \text{current\_frame\_score})$. |
| **Longest Eye Closure** | Seconds | Maintained as: $\max(\text{longest\_eye\_closure}, \text{current\_consecutive\_closure\_duration})$. |
| **Number of Alerts** | Total Count | Increments by `1` when state transitions from `ALERT` to any warning state. |
| **Time Spent in Each State**| Seconds | Accumulates elapsed time in each specific state (ALERT, SLIGHTLY_DROWSY, DROWSY, HIGHLY_DROWSY) across transitions. |

---

## ⏱️ State Duration Math (Precision Tracking)
To prevent error accumulation due to FPS variations or system lag, the tracker uses **epoch timestamp tracking** rather than counting frame occurrences:
1. When a state transition occurs (e.g. from state $S_A$ to state $S_B$), the elapsed duration for $S_A$ is computed as:
   $$\Delta t = t_{\text{transition}} - t_{\text{entered\_}S_A}$$
   This $\Delta t$ is immediately added to the running sum for state $S_A$.
2. To provide accurate real-time queries, when `get_stats()` is called, the elapsed duration of the *currently active state* is dynamically added to the return dictionary:
   $$\text{temp\_duration\_active\_state} = t_{\text{current}} - t_{\text{entered\_active\_state}}$$
   This prevents active states from listing outdated durations.

---

## 💾 Output JSON Schema

Upon clean application exit, the statistics tracker compiles the session metrics and exports them to `output/reports/session_statistics.json`.

- **Output Path**: `output/reports/session_statistics.json`
- **Formatting**: Pretty-printed JSON, sorted keys.

### Example JSON Payload:
```json
{
    "average_ear": 0.2854,
    "average_mar": 0.3242,
    "blink_count": 24,
    "highest_score": 67.5,
    "longest_eye_closure": 1.45,
    "number_of_alerts": 2,
    "time_spent_in_states": {
        "ALERT": 245.32,
        "SLIGHTLY_DROWSY": 45.2,
        "DROWSY": 12.5,
        "HIGHLY_DROWSY": 0.0
    },
    "total_session_time": 303.02,
    "yawn_count": 1
}
```

---

## 🔄 Integration Architecture & Lifecycle

The statistics tracking lifecycle is tightly integrated into the central application lifecycle:

```
[StudentDrowsinessApp.__init__]
             │
             ▼
   [Instantiate Tracker]
             │
             ▼
   [StudentDrowsinessApp.start] ──► (Webcam Loop Processing Frame)
             │                                   │
             │                                   ▼
             │                      [stats_tracker.update()]
             │                                   │
             ▼                                   ▼
   [StudentDrowsinessApp.stop] ◄─── (Exit loop requested via 'q')
             │
             ▼
   [stats_tracker.save_stats()]
             │
             ▼
   [session_statistics.json written]
```

1. **Initialization**: Instantiated during app startup as `self.stats_tracker`.
2. **Webcam Loop Ingestion**: On every frame, `stats_tracker.update()` is fed current data (state, score, ear, mar, counts, and active closure duration) after the Decision Engine completes.
3. **Graceful Shutdown**: When the preview window receives a exit request, `self.stop()` calls `stats_tracker.save_stats()` to write the report before destroying resources, protecting data from loss.
