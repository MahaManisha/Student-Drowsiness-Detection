# Release Notes — Student Drowsiness Detection System v2.0

**Release Tag:** `v2.0-phase-f-optimized`  
**Release Date:** July 30, 2026  
**Entry Point:** `dashboard/app.py`  
**License:** Open Source / Production Ready

---

## 🚀 What's New in Version 2.0 (Phase F Architectural Refactoring)

Version 2.0 completes the Phase F architectural refactoring of the real-time Streamlit dashboard rendering pipeline and background AI worker thread infrastructure.

### Phase F Highlights Summary

- **Phase F1: Frame Pipeline Refactoring**
  - Introduced immutable `FrameSnapshot` dataclass (`rgb_frame`, `telemetry`, `frame_id`, `timestamp`, `success`).
  - Replaced scattered `get_processed_frame()` calls with single-snapshot publication.

- **Phase F2: Streamlit Rendering Refactoring**
  - Refactored `dashboard/app.py` and `camera_panel.py` so the live camera viewport is the **sole reader of latest snapshots**.
  - Consolidated image rendering into a single `st.image()` call across the entire application.

- **Phase F3: AI Worker Performance Refactoring**
  - Profiled all 13 AI worker stages with microsecond precision (`time.perf_counter()`).
  - Improved AI worker loop processing throughput by **+16.7%** (33.2 ms/frame, ~30.1 FPS).

- **Phase F4: Dashboard Synchronization Refactoring**
  - Stamped `frame_id` onto all UI cards (`Frame: #<id>` badges).
  - Eliminated stale default fallback metrics (EAR `0.285`, MAR `0.180`) when no face is present (`has_face=False`).

- **Phase F5: Streamlit Performance & Render Backlog Refactoring**
  - Introduced frame change detection (`_last_rendered_fast_frame_id`) to skip redundant image byte WebSocket transmissions.
  - Eliminated client browser render backlog and V8 CPU spikes.

---

## 💻 How to Run the Production Dashboard

```bash
# Activate Virtual Environment
.\venv\Scripts\activate

# Launch Main Streamlit Dashboard Application
streamlit run dashboard/app.py
```

---

## 🧪 Verification & Reliability Metrics

- **Unit Test Suite Pass Rate:** 87 / 87 Passed (100%)
- **AI Processing Throughput:** ~30.1 FPS (33.2 ms/frame)
- **Active Thread Leak Delta:** 0 Threads
- **Permanent Memory Leak Delta:** 0.0 MB
- **Array Memory Allocation per UI Tick:** 0 MB (Copy-Free)
