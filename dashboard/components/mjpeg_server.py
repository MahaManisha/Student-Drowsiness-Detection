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
                        time.sleep(0.05)
                        continue

                    snapshot = _CAMERA_MANAGER_REF.get_latest_snapshot()
                    if snapshot is None or getattr(snapshot, "rgb_frame", None) is None:
                        time.sleep(0.03)
                        continue

                    frame_id = getattr(snapshot, "frame_id", 0)
                    img = snapshot.rgb_frame

                    # Encode to JPEG
                    bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                    is_ok, jpeg_buf = cv2.imencode('.jpg', bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
                    if not is_ok:
                        time.sleep(0.03)
                        continue

                    jpeg_bytes = jpeg_buf.tobytes()

                    # Write MJPEG boundary frame
                    self.wfile.write(b'--frame\r\n')
                    self.wfile.write(b'Content-Type: image/jpeg\r\n')
                    self.wfile.write(f'Content-Length: {len(jpeg_bytes)}\r\n\r\n'.encode('utf-8'))
                    self.wfile.write(jpeg_bytes)
                    self.wfile.write(b'\r\n')
                    self.wfile.flush()

                    time.sleep(0.03)  # ~30 FPS target
                except (BrokenPipeError, ConnectionResetError):
                    break
                except Exception as ex:
                    time.sleep(0.05)
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
