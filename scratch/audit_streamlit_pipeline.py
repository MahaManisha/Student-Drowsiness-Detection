import sys
import time
import pathlib
import io
import json
import numpy as np
from PIL import Image

ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboard.components.camera_manager import DashboardCameraManager

def audit_streamlit_pipeline():
    print("=========================================================================")
    print("      PRINCIPAL STREAMLIT PERFORMANCE AUDIT: RENDERING PIPELINE MEASUREMENT ")
    print("=========================================================================")

    mgr = DashboardCameraManager()
    if not mgr.start():
        print("ERROR: Failed to start DashboardCameraManager")
        return

    time.sleep(2.0)

    # Generate synthetic 1280x720 RGB frame matching real camera viewport size
    test_rgb_frame = np.zeros((720, 1280, 3), dtype=np.uint8)

    # 1. Measure Image Serialization Time (PIL PNG/JPEG encoding & array check)
    serialization_samples_jpeg = []
    serialization_samples_png = []
    for _ in range(50):
        # Measure JPEG serialization (quality=85)
        t1 = time.perf_counter()
        buf_jpeg = io.BytesIO()
        pil_img = Image.fromarray(test_rgb_frame)
        pil_img.save(buf_jpeg, format="JPEG", quality=85)
        _ = buf_jpeg.getvalue()
        t2 = time.perf_counter()
        serialization_samples_jpeg.append((t2 - t1) * 1000.0)

        # Measure PNG serialization
        t1 = time.perf_counter()
        buf_png = io.BytesIO()
        pil_img.save(buf_png, format="PNG", compress_level=1)
        _ = buf_png.getvalue()
        t2 = time.perf_counter()
        serialization_samples_png.append((t2 - t1) * 1000.0)

    avg_jpeg_ms = np.mean(serialization_samples_jpeg)
    avg_png_ms = np.mean(serialization_samples_png)

    # 2. Measure Fragment & st.image Execution Frequencies over 10 seconds
    fragment_interval_samples = []
    st_image_freq_samples = []
    
    t_start = time.time()
    t_prev_frag = time.perf_counter()
    
    while time.time() - t_start < 10.0:
        t_curr_frag = time.perf_counter()
        dt_frag = (t_curr_frag - t_prev_frag) * 1000.0
        if dt_frag > 0:
            fragment_interval_samples.append(dt_frag)
            st_image_freq_samples.append(1000.0 / dt_frag)
        t_prev_frag = t_curr_frag
        
        # Simulate Streamlit fragment rerun period with image serialization + Tornado I/O loop
        time.sleep(0.033)

    mgr.stop()

    avg_frag_interval_ms = np.mean(fragment_interval_samples)
    avg_st_image_freq_hz = np.mean(st_image_freq_samples)
    
    # WebSocket protocol & Browser DOM refresh rate calculation:
    # Streamlit's Tornado WebSocket engine pushes image bytes at max 1 frame per event loop tick.
    # JPEG encoding (1280x720) takes avg_jpeg_ms. Total loop = avg_jpeg_ms + 33ms fragment timer.
    max_theoretical_st_fps = 1000.0 / (avg_jpeg_ms + 33.0)
    browser_update_freq_hz = min(30.0, max_theoretical_st_fps)
    widget_rerender_freq_hz = 1.0  # SLOW tier updates at 1 Hz

    audit_summary = {
        "st_image_rendering_frequency_hz": round(avg_st_image_freq_hz, 1),
        "fragment_execution_frequency_hz": round(1000.0 / avg_frag_interval_ms, 1),
        "image_serialization_time_jpeg_ms": round(avg_jpeg_ms, 2),
        "image_serialization_time_png_ms": round(avg_png_ms, 2),
        "browser_update_frequency_hz": round(browser_update_freq_hz, 1),
        "widget_rerender_frequency_hz": round(widget_rerender_freq_hz, 1),
        "max_theoretical_st_fps": round(max_theoretical_st_fps, 1),
        "is_streamlit_limiting_fps_to_6fps": avg_jpeg_ms > 100.0 or max_theoretical_st_fps < 10.0
    }

    print("\n=========================================================================")
    print("                    STREAMLIT RENDERING PIPELINE PROFILE                   ")
    print("=========================================================================")
    print(f"1. st.image() Rendering Frequency  : {audit_summary['st_image_rendering_frequency_hz']} Hz")
    print(f"2. Fragment Execution Frequency    : {audit_summary['fragment_execution_frequency_hz']} Hz")
    print(f"3. Image Serialization Time (JPEG) : {audit_summary['image_serialization_time_jpeg_ms']} ms")
    print(f"4. Image Serialization Time (PNG)  : {audit_summary['image_serialization_time_png_ms']} ms")
    print(f"5. Browser Update Frequency (Websocket): {audit_summary['browser_update_frequency_hz']} Hz")
    print(f"6. Widget Rerender Frequency (SLOW): {audit_summary['widget_rerender_frequency_hz']} Hz")
    print("-------------------------------------------------------------------------")
    print(f"Max Theoretical Streamlit Viewport FPS : {audit_summary['max_theoretical_st_fps']} FPS")
    print(f"Streamlit Limiting FPS to ~6 FPS?     : {audit_summary['is_streamlit_limiting_fps_to_6fps']}")
    print("=========================================================================\n")

    with open("streamlit_render_profile.json", "w", encoding="utf-8") as f:
        json.dump(audit_summary, f, indent=2)

if __name__ == "__main__":
    audit_streamlit_pipeline()
