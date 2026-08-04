# FPS Trace Report: Displayed vs. Runtime FPS Discrepancy Analysis

**Role:** Senior Python Runtime Debugger  
**Target:** Top-Right Header Displayed FPS Counter (`⚡ 6.7 FPS`)  

---

### Executive Summary

While live runtime performance instrumentation confirms that the **Camera Producer**, **AI Worker**, and **Streamlit Render Pipeline** operate at **25.0 – 30.0 FPS**, the top-right header of the Streamlit application displays **6.7 FPS**.

This report traces the exact files, functions, variables, and architectural execution flow responsible for computing and rendering this displayed FPS value.

---

### 1. Source Trace & Calculation Pipeline

```
[camera/camera.py]
  CameraStream._producer_loop() ──> Calculates self._current_fps = 1.0 / dt
  CameraStream.get_fps()       ──> Returns round(self._current_fps, 1)
                                         │
                                         ▼
[dashboard/components/camera_manager.py]
  DashboardCameraManager._ai_worker_loop() ──> Attaches telemetry["fps"] = self.camera.get_fps()
                                                     │
                                                     ▼
[dashboard/app.py]
  render_live_dashboard() (Outer Page) ──> Calls snapshot = camera_mgr.get_latest_snapshot()
                                       ──> Calls render_header(telemetry)
                                                     │
                                                     ▼
[dashboard/components/header.py]
  render_header() ──> Renders HTML <div>⚡ {fps_str} FPS</div> in top-right header
```

---

### 2. Detailed Technical Breakdown

#### 1. File Computing the Displayed FPS:
- **`camera/camera.py`** (computes raw value in `CameraStream._producer_loop` and `CameraStream.get_fps`)
- **`dashboard/components/camera_manager.py`** (maps it to `telemetry["fps"]` at line 438)
- **`dashboard/components/header.py`** (formats and renders HTML at line 55)

#### 2. Function Computing the Displayed FPS:
- **`CameraStream._producer_loop`** (`camera/camera.py:235-238`)
- **`CameraStream.get_fps`** (`camera/camera.py:308-309`)
- **`render_header`** (`dashboard/components/header.py:15-60`)

#### 3. Variables Used:
- `now = time.time()` (`camera/camera.py:232`)
- `self._prev_time` (`camera/camera.py:235-238`)
- `dt = now - self._prev_time` (`camera/camera.py:235`)
- `self._current_fps = 1.0 / dt` (`camera/camera.py:237`)
- `telemetry["fps"]` (`dashboard/components/camera_manager.py:438`)
- `fps_val = telemetry_data.get("fps", 30.0)` (`dashboard/components/header.py:20`)
- `fps_str = safe_float(fps_val, precision=1, default="30.0")` (`dashboard/components/header.py:23`)

#### 4. What the Displayed Metric Measures:
- It measures **instantaneous single-frame Camera Producer loop interval** ($\frac{1.0}{\Delta t}$) at the moment of camera stream initialization.
- It does **NOT** measure Streamlit UI Render FPS, Browser Display FPS, or AI Worker processing speed.

#### 5. Mathematical Formula Used:

$$\text{FPS} = \text{round}\left(\frac{1.0}{t_{\text{now}} - t_{\text{prev}}}, 1\right)$$

---

### 3. Discrepancy Analysis: Why Displayed FPS (6.7) Does Not Match Runtime FPS (30.0)

| Metric | Measured Value | Location | Reason for Discrepancy |
| :--- | :---: | :--- | :--- |
| **Real Producer FPS** | **`30.0 FPS`** | `camera/camera.py` | Active steady-state camera frame rate |
| **Real AI Worker FPS** | **`30.0 FPS`** | `camera_manager.py` | Active steady-state AI processing rate |
| **Real UI Render FPS** | **`25.0 – 30.0 FPS`** | `dashboard/app.py` | Active Streamlit `@st.fragment` rerun rate |
| **Displayed Header FPS** | **`6.7 FPS`** | `header.py:55` | **FROZEN / UNUPDATED STATIC RENDER** |

#### Root Cause 1: Outer Page Scope (Outside `@st.fragment`)
In `dashboard/app.py`, `render_header(telemetry)` is called directly inside `render_live_dashboard()` on the **outer page layout script**:

```python
# dashboard/app.py line 123
def render_live_dashboard(camera_mgr) -> None:
    snapshot = camera_mgr.get_latest_snapshot()
    telemetry = snapshot.telemetry

    # Render Header (Outer Page) - EXECUTED ONCE ON INITIAL PAGE LOAD
    render_header(telemetry)
    ...
    # Trigger FAST Tier Fragment (30 FPS)
    render_fast_tier(...)
```

In Streamlit, when `@st.fragment(run_every="0.033s")` or `@st.fragment(run_every="1.0s")` re-runs, **ONLY the fragment functions (`render_fast_tier` and `render_slow_tier`) are re-executed**. 
The outer page script (`render_live_dashboard` and `render_header`) is **NEVER re-executed** during fragment updates.

#### Root Cause 2: Initial Startup Sampling
When the outer page loads on initial boot, `render_header()` calls `camera_mgr.get_latest_snapshot()` while `CameraStream` is completing its hardware initialization phase (where frame reads initially took ~150ms / 6.7 FPS). 

Because `render_header()` is outside any fragment, the top-right HTML container is rendered ONCE with `⚡ 6.7 FPS` on page load and **remains permanently frozen at 6.7 FPS**, even after the camera and AI worker accelerate to a steady-state 30.0 FPS.

---

### 4. Conclusion

The 6.7 FPS displayed in the top-right header is a **stale, frozen UI artifact from initial page boot**. The active application runtime pipelines (Camera Producer, AI Worker, Streamlit Render, and Browser Display) are operating cleanly at **25.0 – 30.0 FPS**.
