"""
Student Drowsiness Detection System - Clean AI Visualizer Module

This module provides the HUDVisualizer class to render a clean, unobscured AI visualization
on camera frames. All numeric and textual telemetry overlays have been moved exclusively to the
Streamlit dashboard. The OpenCV camera stream displays only the raw frame, facial landmarks,
and optional 3D head pose projection axes.
"""

from typing import Any, Dict, Optional, Tuple
import cv2
import numpy as np


class HUDVisualizer:
    """
    Clean AI Visualizer rendering unobscured camera frames and optional 3D pose axis.
    Telemetry values (EAR, MAR, Blinks, Score, Alerts) are rendered exclusively in Streamlit.
    """

    def __init__(self) -> None:
        # Accent colors preserved for color mapping queries
        self.color_bg = (20, 20, 24)
        self.color_border = (60, 60, 68)
        self.color_text = (240, 240, 245)
        self.color_muted = (140, 140, 150)

        self.color_alert = (170, 230, 20)      # Mint/Teal
        self.color_slightly = (0, 215, 255)    # Yellow
        self.color_drowsy = (0, 140, 255)      # Orange
        self.color_highly = (80, 80, 250)      # Red

        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale_labels = 0.45
        self.font_scale_values = 0.45
        self.thickness = 1
        self.line_height = 20

    def get_state_color(self, state_str: str) -> Tuple[int, int, int]:
        """Maps drowsiness state string to color tuple."""
        clean_state = state_str.upper().replace(" ", "_")
        if "HIGHLY" in clean_state:
            return self.color_highly
        elif "DROWSY" in clean_state and "SLIGHTLY" not in clean_state:
            return self.color_drowsy
        elif "SLIGHTLY" in clean_state:
            return self.color_slightly
        else:
            return self.color_alert

    def draw_pose_axis(
        self,
        frame: np.ndarray,
        rvec: Optional[np.ndarray],
        tvec: Optional[np.ndarray]
    ) -> np.ndarray:
        """
        Projects 3D head orientation axes (X: Red, Y: Green, Z: Blue) originating
        from the nose tip onto the 2D image plane.
        """
        if rvec is None or tvec is None:
            return frame

        h, w = frame.shape[:2]
        focal_length = w
        center = (w / 2.0, h / 2.0)
        camera_matrix = np.array([
            [focal_length, 0.0, center[0]],
            [0.0, focal_length, center[1]],
            [0.0, 0.0, 1.0]
        ], dtype=np.float64)
        dist_coeffs = np.zeros((4, 1), dtype=np.float64)

        # 3D axis points: Nose origin (0,0,0), X (red - right), Y (green - down), Z (blue - forward)
        axis_3d = np.array([
            (0.0, 0.0, 0.0),
            (60.0, 0.0, 0.0),    # X-axis (Red)
            (0.0, 60.0, 0.0),    # Y-axis (Green)
            (0.0, 0.0, -60.0)    # Z-axis (Blue)
        ], dtype=np.float64)

        try:
            img_pts, _ = cv2.projectPoints(axis_3d, rvec, tvec, camera_matrix, dist_coeffs)
            img_pts = img_pts.reshape(-1, 2).astype(int)

            nose = tuple(img_pts[0])
            x_axis = tuple(img_pts[1])
            y_axis = tuple(img_pts[2])
            z_axis = tuple(img_pts[3])

            cv2.line(frame, nose, x_axis, (0, 0, 255), 2, cv2.LINE_AA)   # Red: X-axis
            cv2.line(frame, nose, y_axis, (0, 255, 0), 2, cv2.LINE_AA)   # Green: Y-axis
            cv2.line(frame, nose, z_axis, (255, 0, 0), 2, cv2.LINE_AA)   # Blue: Z-axis
        except Exception:
            pass

        return frame

    def draw(self, frame: np.ndarray, metrics: Dict[str, Any]) -> np.ndarray:
        """
        Renders clean AI visualization overlay onto frame.
        All numerical/textual HUD panels have been removed.

        Args:
            frame (np.ndarray): Video frame (BGR format).
            metrics (Dict[str, Any]): Telemetry payload.

        Returns:
            np.ndarray: Frame with optional 3D pose axis overlay.
        """
        head_pose = metrics.get("head_pose", {})
        if isinstance(head_pose, dict) and head_pose.get("valid", False):
            rvec = head_pose.get("rvec")
            tvec = head_pose.get("tvec")
            frame = self.draw_pose_axis(frame, rvec, tvec)

        return frame
