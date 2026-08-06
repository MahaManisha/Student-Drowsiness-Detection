"""
Student Drowsiness Detection System - Isolated Windows Camera Backend & FOURCC Benchmark

Tests camera hardware acquisition latency across Windows backends and pixel formats:
1. DSHOW + default FOURCC (1280x720 @ 30 FPS)
2. DSHOW + MJPG (1280x720 @ 30 FPS)
3. MSMF + default FOURCC (1280x720 @ 30 FPS)
4. MSMF + MJPG (1280x720 @ 30 FPS)
5. Best combination @ 640x480 @ 30 FPS

Measures VideoCapture.read() duration, negotiated properties, actual FPS, and allows physical motion validation with cv2.imshow().
"""

import sys
import time
import pathlib
import cv2
import numpy as np
from typing import Dict, Any, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def decode_fourcc(val: float) -> str:
    try:
        ival = int(val)
        return "".join([chr((ival >> 8 * i) & 0xFF) for i in range(4)])
    except Exception:
        return "UNKNOWN"


def test_single_configuration(
    camera_id: int,
    backend_flag: int,
    backend_name: str,
    fourcc_str: Optional[str],
    width: int,
    height: int,
    fps_target: int,
    num_frames: int = 300,
    interactive: bool = True
) -> Dict[str, Any]:
    print(f"\n==================================================================================")
    print(f" TESTING: {backend_name} | FOURCC: {fourcc_str or 'Default'} | Request: {width}x{height} @ {fps_target} FPS")
    print(f"==================================================================================")

    t_open_start = time.perf_counter()
    cap = cv2.VideoCapture(camera_id, backend_flag)
    t_open_end = time.perf_counter()

    if not cap.isOpened():
        print(f"❌ RESULT: FAILED TO OPEN CAMERA with {backend_name}")
        return {
            "config": f"{backend_name} {fourcc_str or 'Default'}",
            "supported": False,
            "error": "Failed to open camera"
        }

    # 1. Apply properties in recommended order: FOURCC -> WIDTH -> HEIGHT -> FPS -> BUFFERSIZE
    if fourcc_str:
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*fourcc_str))

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_FPS, fps_target)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    # 2. Read back actual negotiated hardware properties
    actual_backend = cap.getBackendName() if hasattr(cap, "getBackendName") else backend_name
    act_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    act_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    act_fps = cap.get(cv2.CAP_PROP_FPS)
    act_buf = cap.get(cv2.CAP_PROP_BUFFERSIZE)
    act_fourcc_val = cap.get(cv2.CAP_PROP_FOURCC)
    act_fourcc_str = decode_fourcc(act_fourcc_val)

    print(f"Negotiated Properties:")
    print(f"  Backend Name : {actual_backend}")
    print(f"  Resolution   : {act_w}x{act_h}")
    print(f"  Reported FPS : {act_fps}")
    print(f"  Buffersize   : {act_buf}")
    print(f"  FOURCC Code  : {act_fourcc_str} ({act_fourcc_val})")

    # 3. Warmup (read 10 frames)
    for _ in range(10):
        cap.read()

    read_durations_ms = []
    t_loop_start = time.perf_counter()

    win_title = f"RAW PREVIEW — {backend_name} ({fourcc_str or 'DEF'}) {act_w}x{act_h}"

    for i in range(num_frames):
        t1 = time.perf_counter()
        ret, frame = cap.read()
        t2 = time.perf_counter()

        if not ret or frame is None:
            print(f"⚠️ Read failed at frame {i+1}")
            continue

        read_ms = (t2 - t1) * 1000.0
        read_durations_ms.append(read_ms)

        if interactive:
            # Add FPS / read timing overlay
            fps_text = f"Frame #{i+1} | Read: {read_ms:.1f} ms | {act_w}x{act_h} ({act_fourcc_str})"
            cv2.putText(frame, fps_text, (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow("RAW_CAMERA_BENCHMARK", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord('q'):  # ESC or q to exit early
                break

    t_loop_end = time.perf_counter()
    if interactive:
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass

    cap.release()

    if not read_durations_ms:
        print("❌ RESULT: NO VALID FRAMES READ")
        return {
            "config": f"{backend_name} {fourcc_str or 'Default'}",
            "supported": False,
            "error": "No frames read"
        }

    total_loop_sec = t_loop_end - t_loop_start
    achieved_fps = len(read_durations_ms) / total_loop_sec if total_loop_sec > 0 else 0.0

    arr = np.array(read_durations_ms)
    med_ms = float(np.median(arr))
    p95_ms = float(np.percentile(arr, 95))
    max_ms = float(np.max(arr))

    print(f"\nCaptured {len(read_durations_ms)} frames in {total_loop_sec:.2f} s")
    print(f"  Achieved FPS : {achieved_fps:.1f} FPS")
    print(f"  Read Median  : {med_ms:.2f} ms")
    print(f"  Read P95     : {p95_ms:.2f} ms")
    print(f"  Read Max     : {max_ms:.2f} ms")

    return {
        "config": f"{backend_name} + {fourcc_str or 'Default'}",
        "backend": actual_backend,
        "fourcc": act_fourcc_str,
        "resolution": f"{act_w}x{act_h}",
        "requested_res": f"{width}x{height}",
        "achieved_fps": achieved_fps,
        "med_ms": med_ms,
        "p95_ms": p95_ms,
        "max_ms": max_ms,
        "supported": True
    }


def run_all_benchmarks(camera_id: int = 0) -> Tuple[list, list]:
    print("==================================================================================")
    print("         PRINCIPAL WINDOWS OPENCV CAMERA BACKEND BENCHMARKING SUITE               ")
    print("==================================================================================")

    test_matrix = [
        (cv2.CAP_DSHOW, "DSHOW", None, 1280, 720, 30),
        (cv2.CAP_DSHOW, "DSHOW", "MJPG", 1280, 720, 30),
        (cv2.CAP_MSMF, "MSMF", None, 1280, 720, 30),
        (cv2.CAP_MSMF, "MSMF", "MJPG", 1280, 720, 30),
    ]

    results = []
    for backend_flag, name, fourcc, w, h, fps in test_matrix:
        res = test_single_configuration(
            camera_id=camera_id,
            backend_flag=backend_flag,
            backend_name=name,
            fourcc_str=fourcc,
            width=w,
            height=h,
            fps_target=fps,
            num_frames=200,
            interactive=False  # Headless mode for batch benchmarking; interactive mode available for manual check
        )
        results.append(res)
        time.sleep(1.0)  # Allow hardware handle cleanup between tests

    # Determine best backend & FOURCC from 1280x720 tests
    supported_results = [r for r in results if r.get("supported", False)]
    best_config = min(supported_results, key=lambda x: x["med_ms"]) if supported_results else None

    # Test 640x480 resolution with best backend / FOURCC
    if best_config:
        best_backend_flag = cv2.CAP_MSMF if "MSMF" in best_config["config"] else cv2.CAP_DSHOW
        best_backend_name = "MSMF" if "MSMF" in best_config["config"] else "DSHOW"
        best_fourcc = "MJPG" if "MJPG" in best_config["config"] else None

        print(f"\n[BENCHMARK] Testing lower resolution 640x480 using best combination: {best_config['config']}")
        res_640 = test_single_configuration(
            camera_id=camera_id,
            backend_flag=best_backend_flag,
            backend_name=best_backend_name,
            fourcc_str=best_fourcc,
            width=640,
            height=480,
            fps_target=30,
            num_frames=200,
            interactive=False
        )
        results.append(res_640)

    # Output Summary Table
    print("\n=========================================================================================================")
    print(f"{'Configuration':<22} | {'Resolution':<12} | {'Actual FPS':<11} | {'Median Read':<13} | {'P95 Read':<11} | {'Status':<10}")
    print("=========================================================================================================")

    for r in results:
        cfg = r.get("config", "Unknown")
        if not r.get("supported", False):
            print(f"{cfg:<22} | {'N/A':<12} | {'N/A':<11} | {'N/A':<13} | {'N/A':<11} | ❌ UNSUPPORTED")
        else:
            res_str = r.get("resolution", "Unknown")
            fps_val = f"{r.get('achieved_fps', 0.0):.1f} FPS"
            med_val = f"{r.get('med_ms', 0.0):.2f} ms"
            p95_val = f"{r.get('p95_ms', 0.0):.2f} ms"
            print(f"{cfg:<22} | {res_str:<12} | {fps_val:<11} | {med_val:<13} | {p95_val:<11} | ✅ OK")
    print("=========================================================================================================\n")

    return results


if __name__ == "__main__":
    run_all_benchmarks(0)
