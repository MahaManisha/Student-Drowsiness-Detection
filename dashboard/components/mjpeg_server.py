"""
Student Drowsiness Detection System - High-Performance Threaded MJPEG Video Server

Provides a zero-latency, zero-overhead HTTP MJPEG video streaming server.
Eliminates Streamlit React DOM garbage collection, Base64 string parsing,
iframe collapses, HTTP 404 purges, and video frame freezing permanently.
"""

import sys
import time
import base64
import cv2
import threading
import http.server
import socketserver
import pathlib
from typing import Optional, Any

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from utils.logger import get_logger
    logger = get_logger(__name__)
except Exception:
    import logging
    logger = logging.getLogger(__name__)


_SERVER_INSTANCE: Optional[socketserver.TCPServer] = None
_SERVER_THREAD: Optional[threading.Thread] = None
_CAMERA_MANAGER_REF: Optional[Any] = None
_MJPEG_PORT = 8089


class MJPEGStreamHandler(http.server.BaseHTTPRequestHandler):
    """
    Handles streaming MJPEG frames over standard HTTP GET /video_feed.
    Chrome renders this natively in C++ graphics pipeline without JavaScript or Streamlit DOM overhead.
    """
    def log_message(self, format, *args):
        # Suppress noisy HTTP GET access logging
        pass

    def do_GET(self):
        if self.path == '/video_feed' or self.path == '/':
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache, private, no-store, must-revalidate, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()

            last_sent_frame_id = -1

            while True:
                try:
                    if _CAMERA_MANAGER_REF is None:
                        time.sleep(0.03)
                        continue

                    # Consume newest raw camera frame directly (independent of MediaPipe / AI Worker delay)
                    target_frame = None
                    frame_id = 0
                    if hasattr(_CAMERA_MANAGER_REF, "get_latest_raw_frame"):
                        target_frame, frame_id = _CAMERA_MANAGER_REF.get_latest_raw_frame()

                    # Fallback to AI snapshot if raw frame buffer is not populated yet
                    if target_frame is None:
                        snapshot = _CAMERA_MANAGER_REF.get_latest_snapshot()
                        if snapshot is not None and getattr(snapshot, "rgb_frame", None) is not None:
                            img = snapshot.rgb_frame
                            target_frame = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                            frame_id = getattr(snapshot, "frame_id", 0)

                    if target_frame is None:
                        time.sleep(0.02)
                        continue

                    if frame_id > 0 and frame_id == last_sent_frame_id:
                        time.sleep(0.005)
                        continue
                    last_sent_frame_id = frame_id

                    # Encode BGR directly to JPEG
                    is_ok, jpeg_buf = cv2.imencode('.jpg', target_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                    if not is_ok:
                        time.sleep(0.005)
                        continue

                    jpeg_bytes = jpeg_buf.tobytes()

                    # Write MJPEG boundary frame
                    header = (
                        b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n'
                        b'Content-Length: ' + str(len(jpeg_bytes)).encode('utf-8') + b'\r\n\r\n'
                    )
                    self.wfile.write(header + jpeg_bytes + b'\r\n')
                    self.wfile.flush()

                    time.sleep(0.005)
                except (BrokenPipeError, ConnectionResetError, OSError):
                    break
                except Exception:
                    break
        else:
            self.send_error(404, "Not Found")


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def start_mjpeg_stream_server(camera_manager: Any, port: int = 8089) -> int:
    """
    Starts singleton background MJPEG HTTP streaming server thread on port 8089.
    """
    global _SERVER_INSTANCE, _SERVER_THREAD, _CAMERA_MANAGER_REF, _MJPEG_PORT
    _CAMERA_MANAGER_REF = camera_manager
    _MJPEG_PORT = port

    if _SERVER_THREAD is not None and _SERVER_THREAD.is_alive():
        return _MJPEG_PORT

    for p in range(port, port + 10):
        try:
            server = ThreadedTCPServer(('0.0.0.0', p), MJPEGStreamHandler)
            _SERVER_INSTANCE = server
            _MJPEG_PORT = p
            t = threading.Thread(target=server.serve_forever, daemon=True, name=f"MJPEG-Streamer-{p}")
            t.start()
            _SERVER_THREAD = t
            logger.info(f"[MJPEG SERVER] Started live MJPEG HTTP video stream on http://localhost:{p}/video_feed")
            return p
        except Exception as e:
            logger.warning(f"[MJPEG SERVER] Port {p} unavailable ({e}), trying next port...")

    return _MJPEG_PORT


def get_mjpeg_stream_port() -> int:
    global _MJPEG_PORT
    return _MJPEG_PORT
