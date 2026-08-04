import sys
import time
import pathlib
import json

ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboard.components.camera_manager import DashboardCameraManager

def run_real_profile():
    print("[INSTRUMENTATION] Starting real runtime measurement...")
    mgr = DashboardCameraManager()
    if not mgr.start():
        print("Failed to start camera manager")
        return

    time.sleep(2.0)

    samples = []
    start_time = time.time()
    out_path = ROOT_DIR / "runtime_profile_60s.json"
    
    for i in range(120):
        t1_loop = time.perf_counter()
        snap = mgr.get_latest_snapshot()
        
        t1_st_img = time.perf_counter()
        if snap.rgb_frame is not None:
            try:
                import io
                from PIL import Image
                buf = io.BytesIO()
                pil_img = Image.fromarray(snap.rgb_frame)
                pil_img.save(buf, format="JPEG", quality=85)
                _ = buf.getvalue()
            except Exception as e:
                pass
        t2_st_img = time.perf_counter()
        t_st_img_ms = (t2_st_img - t1_st_img) * 1000.0

        t2_loop = time.perf_counter()
        loop_ms = (t2_loop - t1_loop) * 1000.0

        live_perf = snap.telemetry.get("live_perf", {})
        sample = {
            "timestamp": time.time(),
            "camera_fps": live_perf.get("camera_fps", 0.0),
            "producer_fps": live_perf.get("producer_fps", 0.0),
            "ai_worker_fps": live_perf.get("ai_worker_fps", 0.0),
            "streamlit_render_fps": round(1000.0 / (loop_ms + t_st_img_ms), 1) if (loop_ms + t_st_img_ms) > 0 else 30.0,
            "queue_len": live_perf.get("queue_len", 0),
            "latest_frame_id": live_perf.get("latest_frame_id", 0),
            "displayed_frame_id": snap.frame_id,
            "t_videocapture_read_ms": live_perf.get("t_videocapture_read_ms", 0.0),
            "t_facemesh_ms": live_perf.get("t_facemesh_ms", 0.0),
            "t_ear_ms": live_perf.get("t_ear_ms", 0.0),
            "t_mar_ms": live_perf.get("t_mar_ms", 0.0),
            "t_headpose_ms": live_perf.get("t_headpose_ms", 0.0),
            "t_hud_draw_ms": live_perf.get("t_hud_draw_ms", 0.0),
            "t_rgb_conversion_ms": live_perf.get("t_rgb_conversion_ms", 0.0),
            "t_streamlit_image_render_ms": t_st_img_ms
        }
        samples.append(sample)
        time.sleep(0.033)

    mgr.stop()

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2)
    print(f"[INSTRUMENTATION] Done! Wrote {len(samples)} samples to {out_path}")

if __name__ == "__main__":
    run_real_profile()
