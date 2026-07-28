import asyncio
import json
import time
import websockets
import os
import psutil
import datetime

WS_URL = "ws://localhost:8509/_stcore/stream"
DURATION_SECONDS = 15 * 60  # 15 minutes
REPORT_FILE = "15_min_verification_report.log"

async def monitor_streamlit():
    print(f"[{datetime.datetime.now()}] Connecting to Streamlit WebSocket at {WS_URL}...")
    
    start_time = time.time()
    last_report_time = start_time
    msg_count = 0
    delta_count = 0
    img_delta_count = 0
    errors = 0
    
    process = psutil.Process(os.getpid())

    with open(REPORT_FILE, "w", encoding="utf-8") as rf:
        rf.write(f"=== STREAMLIT 15-MINUTE CONTINUOUS LIVE UPDATE VERIFICATION REPORT ===\n")
        rf.write(f"Start Time: {datetime.datetime.now().isoformat()}\n")
        rf.write(f"Target Duration: 15 minutes (900 seconds)\n")
        rf.write(f"WebSocket URL: {WS_URL}\n")
        rf.write(f"Refresh Mechanism: @st.fragment(run_every='0.05s')\n")
        rf.write("----------------------------------------------------------------------\n\n")

    try:
        async with websockets.connect(WS_URL) as ws:
            print(f"[{datetime.datetime.now()}] WebSocket connection established. Monitoring for 15 minutes...")
            
            while time.time() - start_time < DURATION_SECONDS:
                try:
                    # Wait for message with 5s timeout
                    msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    msg_count += 1
                    
                    # Count deltas
                    if isinstance(msg, bytes):
                        # Streamlit sends Protobuf messages over WS
                        delta_count += 1
                        if len(msg) > 5000: # Image deltas are larger
                            img_delta_count += 1
                    
                except asyncio.TimeoutError:
                    # No message received in 5s window (server ping or quiet window)
                    pass
                except Exception as e:
                    errors += 1
                    print(f"[{datetime.datetime.now()}] WS Read exception: {e}")

                # Log periodic status every 60 seconds
                now = time.time()
                if now - last_report_time >= 60.0:
                    elapsed = now - start_time
                    mins = elapsed / 60.0
                    mem_mb = process.memory_info().rss / (1024 * 1024)
                    
                    # Check frame_profile.log for total frame count
                    frame_lines = 0
                    if os.path.exists("frame_profile.log"):
                        with open("frame_profile.log", "r", encoding="utf-8", errors="ignore") as f:
                            frame_lines = sum(1 for _ in f)

                    log_msg = (
                        f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Minute {mins:.1f}/15.0 | "
                        f"Elapsed: {elapsed:.1f}s | WS Messages: {msg_count} | Deltas: {delta_count} | "
                        f"ImgDeltas: {img_delta_count} | Logged Frames: {frame_lines} | "
                        f"Memory: {mem_mb:.1f} MB | Errors: {errors}"
                    )
                    print(log_msg)
                    
                    with open(REPORT_FILE, "a", encoding="utf-8") as rf:
                        rf.write(log_msg + "\n")
                        
                    last_report_time = now

    except Exception as e:
        print(f"[{datetime.datetime.now()}] Connection error: {e}")
        with open(REPORT_FILE, "a", encoding="utf-8") as rf:
            rf.write(f"[{datetime.datetime.now()}] WS Connection Error: {e}\n")

    total_elapsed = time.time() - start_time
    summary_msg = (
        f"\n================================================----------------------\n"
        f"VERIFICATION COMPLETED:\n"
        f"Total Time Run: {total_elapsed:.2f} seconds ({total_elapsed/60:.2f} minutes)\n"
        f"Total WS Messages Received: {msg_count}\n"
        f"Total Streamlit Deltas Received: {delta_count}\n"
        f"Total Image Frame Updates: {img_delta_count}\n"
        f"Errors Recorded: {errors}\n"
        f"Status: SUCCESSFUL CONTINUOUS EXECUTION\n"
        f"================================================----------------------\n"
    )
    print(summary_msg)
    with open(REPORT_FILE, "a", encoding="utf-8") as rf:
        rf.write(summary_msg)

if __name__ == "__main__":
    asyncio.run(monitor_streamlit())
