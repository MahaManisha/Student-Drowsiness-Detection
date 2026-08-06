"""
Windows Camera Backend Comparison Script: CAP_DSHOW vs CAP_MSMF
Measures VideoCapture.read() latency, reported FPS, buffer behavior, and motion latency.
"""

import cv2
import time
import sys
import numpy as np

def benchmark_backend(backend_id, backend_name, num_frames=100):
    print(f"\n--- Testing Backend: {backend_name} ---")
    cap = cv2.VideoCapture(0, backend_id)
    if not cap.isOpened():
        print(f"FAILED to open camera with {backend_name}")
        return None

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    reported_fps = cap.get(cv2.CAP_PROP_FPS)
    buf_size = cap.get(cv2.CAP_PROP_BUFFERSIZE)

    print(f"Opened: {actual_w}x{actual_h} | Reported FPS: {reported_fps} | BUFFERSIZE: {buf_size}")

    # Warmup
    for _ in range(10):
        cap.read()

    read_durations = []
    t_start_total = time.perf_counter()

    for i in range(num_frames):
        t1 = time.perf_counter()
        ret, frame = cap.read()
        t2 = time.perf_counter()

        if ret and frame is not None:
            read_durations.append((t2 - t1) * 1000.0)

    t_end_total = time.perf_counter()
    total_time = t_end_total - t_start_total
    actual_fps = len(read_durations) / total_time if total_time > 0 else 0.0

    cap.release()

    if not read_durations:
        print("No valid frames read.")
        return None

    arr = np.array(read_durations)
    print(f"Read Duration — Median: {np.median(arr):.2f} ms | P95: {np.percentile(arr, 95):.2f} ms | Max: {np.max(arr):.2f} ms")
    print(f"Actual Measured Rate: {actual_fps:.1f} FPS")

    return {
        "backend": backend_name,
        "median_ms": np.median(arr),
        "p95_ms": np.percentile(arr, 95),
        "max_ms": np.max(arr),
        "fps": actual_fps
    }

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("Benchmarking Windows Camera Backends for Motion-to-Capture Latency...")
    res_dshow = benchmark_backend(cv2.CAP_DSHOW, "CAP_DSHOW (DirectShow)")
    time.sleep(1.0)
    res_msmf = benchmark_backend(cv2.CAP_MSMF, "CAP_MSMF (Media Foundation)")
    time.sleep(1.0)
    res_any = benchmark_backend(cv2.CAP_ANY, "CAP_ANY (Default)")

    print("\n================ BACKEND COMPARISON SUMMARY ================")
    for res in [res_dshow, res_msmf, res_any]:
        if res:
            print(f"{res['backend']:25s} | Read Median: {res['median_ms']:6.2f} ms | Read P95: {res['p95_ms']:6.2f} ms | Actual FPS: {res['fps']:5.1f}")
    print("============================================================")
