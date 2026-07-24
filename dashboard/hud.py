"""
Student Drowsiness Detection System - HUD Visualizer Module

This module provides the HUDVisualizer class to draw a premium, structured HUD overlay
on camera frames. Follows single responsibility principle (SRP) by separating rendering
concerns from calculation pipelines.
"""

import math
from typing import Any, Dict, List, Optional, Tuple
import cv2


class HUDVisualizer:
    """
    Renders telemetry data onto video frames as a professional HUD overlay.
    """

    def __init__(self) -> None:
        # Soft premium palette
        self.color_bg = (20, 20, 24)        # Deep charcoal
        self.color_border = (60, 60, 68)    # Medium charcoal-slate
        self.color_text = (240, 240, 245)   # Soft off-white
        self.color_muted = (140, 140, 150)  # Slate gray for labels
        
        # State-based accent colors
        self.color_alert = (170, 230, 20)      # Vivid Mint/Teal
        self.color_slightly = (0, 215, 255)    # Warm Yellow-Orange
        self.color_drowsy = (0, 140, 255)      # Orange
        self.color_highly = (80, 80, 250)      # Crimson Red/Deep Coral

        # Font configuration
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale_labels = 0.45
        self.font_scale_values = 0.45
        self.thickness = 1
        self.line_height = 20

    def draw_panel(
        self,
        frame: cv2.Mat,
        x: int,
        y: int,
        w: int,
        h: int,
        title: str,
        border_color: Tuple[int, int, int],
        alpha: float = 0.80
    ) -> None:
        """Draws a semi-transparent panel with a border and title header."""
        overlay = frame.copy()
        # Draw main box background
        cv2.rectangle(overlay, (x, y), (x + w, y + h), self.color_bg, -1)
        # Apply alpha blending
        cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0, frame)

        # Draw panel outline
        cv2.rectangle(frame, (x, y), (x + w, y + h), border_color, 1)

        # Draw panel header strip
        cv2.rectangle(frame, (x, y), (x + w, y + 25), self.color_bg, -1)
        cv2.rectangle(frame, (x, y), (x + w, y + 25), border_color, 1)

        # Title text
        cv2.putText(
            frame,
            title.upper(),
            (x + 10, y + 17),
            self.font,
            0.4,
            self.color_text,
            1,
            cv2.LINE_AA
        )

    def draw_progress_bar(
        self,
        frame: cv2.Mat,
        x: int,
        y: int,
        w: int,
        h: int,
        value: float,
        max_value: float,
        threshold: Optional[float] = None,
        color: Tuple[int, int, int] = (0, 255, 0)
    ) -> None:
        """Draws a horizontal progress bar with a threshold line."""
        # Draw background track
        cv2.rectangle(frame, (x, y), (x + w, y + h), (40, 40, 48), -1)

        # Draw fill level
        fill_ratio = min(1.0, max(0.0, float(value) / max_value))
        fill_w = int(w * fill_ratio)
        if fill_w > 0:
            cv2.rectangle(frame, (x, y), (x + fill_w, y + h), color, -1)

        # Draw border
        cv2.rectangle(frame, (x, y), (x + w, y + h), (80, 80, 88), 1)

        # Draw threshold marker if provided
        if threshold is not None and 0.0 < threshold < max_value:
            thresh_ratio = float(threshold) / max_value
            thresh_x = x + int(w * thresh_ratio)
            cv2.line(frame, (thresh_x, y), (thresh_x, y + h), (255, 255, 255), 1)

    def draw_pose_reticle(
        self,
        frame: cv2.Mat,
        x: int,
        y: int,
        size: int,
        yaw: float,
        pitch: float,
        roll: float,
        valid: bool,
        active_color: Tuple[int, int, int]
    ) -> None:
        """Draws a graphical crosshair reticle representing head pitch/yaw/roll."""
        center_x = x + size // 2
        center_y = y + size // 2
        radius = (size - 10) // 2

        # Draw reticle background and grid
        cv2.rectangle(frame, (x, y), (x + size, y + size), (30, 30, 36), -1)
        cv2.rectangle(frame, (x, y), (x + size, y + size), (60, 60, 68), 1)
        cv2.line(frame, (center_x, y + 4), (center_x, y + size - 4), (55, 55, 62), 1)
        cv2.line(frame, (x + 4, center_y), (x + size - 4, center_y), (55, 55, 62), 1)
        cv2.circle(frame, (center_x, center_y), radius, (55, 55, 62), 1)

        if valid:
            # Map degrees to pixels (Assume max deflection = 20 degrees maps to reticle radius)
            max_deflection = 20.0
            offset_x = int((yaw / max_deflection) * radius)
            offset_y = int((pitch / max_deflection) * radius)

            # Clamp offset to reticle boundaries
            dist = math.sqrt(offset_x**2 + offset_y**2)
            if dist > radius:
                offset_x = int((offset_x / dist) * radius)
                offset_y = int((offset_y / dist) * radius)

            target_x = center_x + offset_x
            target_y = center_y + offset_y

            # Draw roll tilt line inside target dot
            rad = math.radians(roll)
            line_len = 10
            rx = int(math.sin(rad) * line_len)
            ry = int(math.cos(rad) * line_len)
            cv2.line(
                frame,
                (target_x - rx, target_y + ry),
                (target_x + rx, target_y - ry),
                active_color,
                2
            )

            # Draw active target indicator dot
            cv2.circle(frame, (target_x, target_y), 4, active_color, -1)
        else:
            # Draw Red 'X' inside reticle for search/failure status
            cv2.line(
                frame,
                (center_x - 8, center_y - 8),
                (center_x + 8, center_y + 8),
                (0, 0, 255),
                2
            )
            cv2.line(
                frame,
                (center_x + 8, center_y - 8),
                (center_x - 8, center_y + 8),
                (0, 0, 255),
                2
            )

    def _wrap_text(self, text: str, max_width: int) -> List[str]:
        """Wraps text into lines that do not exceed the specified pixel width."""
        words = text.split(" ")
        lines = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            (w, _), _ = cv2.getTextSize(
                test_line, self.font, self.font_scale_labels, self.thickness
            )
            if w <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)
        return lines

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

    def draw(self, frame: cv2.Mat, metrics: Dict[str, Any]) -> cv2.Mat:
        """
        Assembles and renders all HUD elements onto the given frame.

        Args:
            frame (cv2.Mat): Input image array (usually BGR format).
            metrics (Dict[str, Any]): Dictionary of telemetry parameters.

        Returns:
            cv2.Mat: Modified image array with overlay applied.
        """
        height, width = frame.shape[:2]

        # 1. Gather metrics safely
        session_time_str = metrics.get("session_time", "00:00")
        fps = metrics.get("fps", 0.0)
        drowsiness_state = metrics.get("drowsiness_state", "ALERT")
        state_color = self.get_state_color(drowsiness_state)

        # 2. Render Header Panel
        header_h = 60
        header_overlay = frame.copy()
        cv2.rectangle(header_overlay, (0, 0), (width, header_h), self.color_bg, -1)
        cv2.addWeighted(header_overlay, 0.85, frame, 0.15, 0, frame)
        cv2.line(frame, (0, header_h), (width, header_h), self.color_border, 1)

        # Header Title
        cv2.putText(
            frame,
            "STUDENT DROWSINESS DETECTION SYSTEM",
            (15, 36),
            self.font,
            0.55,
            self.color_text,
            2,
            cv2.LINE_AA
        )

        # Session Time & FPS
        time_fps_text = f"SESSION: {session_time_str}  |  FPS: {fps:.1f}"
        (tf_w, tf_h), _ = cv2.getTextSize(
            time_fps_text, self.font, 0.45, 1
        )
        
        # State Pill Badge
        state_badge_text = f" {drowsiness_state.replace('_', ' ')} "
        (sb_w, sb_h), _ = cv2.getTextSize(
            state_badge_text, self.font, 0.45, 2
        )
        
        # Calculate right-aligned offsets
        badge_x = width - sb_w - 20
        badge_y = 20
        cv2.rectangle(
            frame,
            (badge_x, badge_y),
            (badge_x + sb_w, badge_y + sb_h + 8),
            state_color,
            -1
        )
        cv2.putText(
            frame,
            state_badge_text,
            (badge_x, badge_y + sb_h + 4),
            self.font,
            0.45,
            (20, 20, 24), # Dark text for visibility inside colored pill
            2,
            cv2.LINE_AA
        )

        cv2.putText(
            frame,
            time_fps_text,
            (badge_x - tf_w - 25, 36),
            self.font,
            0.45,
            self.color_muted,
            1,
            cv2.LINE_AA
        )

        # 3. Dynamic sizing of sidebar panels to prevent overlap
        panel_w = min(270, int(width * 0.42))
        panel_h = height - header_h - 65 # Leave room for footer
        panel_y = header_h + 10

        # Left Panel (Eyes & Mouth)
        self.draw_panel(
            frame,
            x=10,
            y=panel_y,
            w=panel_w,
            h=panel_h,
            title="Eyes & Mouth Telemetry",
            border_color=self.color_border
        )

        # Right Panel (Head Pose & Decision Engine)
        self.draw_panel(
            frame,
            x=width - panel_w - 10,
            y=panel_y,
            w=panel_w,
            h=panel_h,
            title="Pose & Decision Engine",
            border_color=self.color_border
        )

        # 4. Draw Left Panel Contents (Eyes & Mouth)
        left_x = 20
        left_y = panel_y + 40
        label_val_gap = panel_w - 20 - 90  # Space between label and value string

        # Eye Metrics
        ear_metrics = metrics.get("ear_metrics", {})
        l_ear = ear_metrics.get("left_ear")
        r_ear = ear_metrics.get("right_ear")
        avg_ear = ear_metrics.get("avg_ear")
        ear_thresh = ear_metrics.get("threshold", 0.25)
        eye_state_str = ear_metrics.get("state", "UNKNOWN")

        l_ear_str = f"{l_ear:.3f}" if l_ear is not None else "N/A"
        r_ear_str = f"{r_ear:.3f}" if r_ear is not None else "N/A"
        avg_ear_str = f"{avg_ear:.3f}" if avg_ear is not None else "N/A"

        # Helper to draw label-value pairs
        def draw_kv(y_pos: int, label: str, val: str, val_color: Tuple[int, int, int] = self.color_text) -> None:
            cv2.putText(frame, label, (left_x, y_pos), self.font, self.font_scale_labels, self.color_muted, self.thickness, cv2.LINE_AA)
            cv2.putText(frame, val, (left_x + panel_w - 100, y_pos), self.font, self.font_scale_values, val_color, self.thickness, cv2.LINE_AA)

        draw_kv(left_y, "Left EAR", l_ear_str)
        left_y += self.line_height
        draw_kv(left_y, "Right EAR", r_ear_str)
        left_y += self.line_height
        draw_kv(left_y, "Average EAR", avg_ear_str)
        left_y += self.line_height

        # EAR Progress Bar
        bar_y_val = avg_ear if avg_ear is not None else 0.0
        # Color bar: Red if below threshold, Green if above
        ear_bar_color = (0, 255, 0) if bar_y_val >= ear_thresh else (0, 0, 255)
        self.draw_progress_bar(
            frame,
            x=left_x,
            y=left_y,
            w=panel_w - 20,
            h=8,
            value=bar_y_val,
            max_value=0.5,
            threshold=ear_thresh,
            color=ear_bar_color
        )
        left_y += self.line_height

        draw_kv(left_y, "EAR Thresh", f"{ear_thresh:.3f}")
        left_y += self.line_height

        eye_state_color = (0, 255, 0) if "OPEN" in eye_state_str.upper() else (0, 0, 255)
        draw_kv(left_y, "Eye State", eye_state_str, eye_state_color)
        left_y += self.line_height

        # Temporal Eye metrics
        blink_count = metrics.get("blink_count", 0)
        closed_frames = metrics.get("closed_frames", 0)
        closed_time = metrics.get("closed_time", 0.0)

        draw_kv(left_y, "Blink Count", str(blink_count))
        left_y += self.line_height
        draw_kv(left_y, "Closed Time", f"{closed_time:.2f} s")
        left_y += self.line_height

        # Divider
        cv2.line(frame, (left_x, left_y - 5), (left_x + panel_w - 20, left_y - 5), self.color_border, 1)
        left_y += 10

        # Mouth Metrics
        mar_metrics = metrics.get("mar_metrics", {})
        mar_val = mar_metrics.get("mar")
        mar_thresh = mar_metrics.get("threshold", 0.60)
        mouth_state_str = mar_metrics.get("state", "UNKNOWN")

        mar_str = f"{mar_val:.2f}" if mar_val is not None else "N/A"
        draw_kv(left_y, "MAR Value", mar_str)
        left_y += self.line_height

        # MAR Progress Bar
        bar_mar_val = mar_val if mar_val is not None else 0.0
        mar_bar_color = (255, 0, 255) if bar_mar_val >= mar_thresh else (0, 255, 0)
        self.draw_progress_bar(
            frame,
            x=left_x,
            y=left_y,
            w=panel_w - 20,
            h=8,
            value=bar_mar_val,
            max_value=1.0,
            threshold=mar_thresh,
            color=mar_bar_color
        )
        left_y += self.line_height

        draw_kv(left_y, "MAR Thresh", f"{mar_thresh:.2f}")
        left_y += self.line_height

        mouth_state_color = (255, 0, 255) if "OPEN" in mouth_state_str.upper() or "YAWN" in mouth_state_str.upper() else (0, 255, 0)
        draw_kv(left_y, "Mouth State", mouth_state_str, mouth_state_color)
        left_y += self.line_height

        # Yawn metrics
        yawn_count = metrics.get("yawn_count", 0)
        open_time = metrics.get("open_time", 0.0)

        draw_kv(left_y, "Yawn Count", str(yawn_count))
        left_y += self.line_height
        draw_kv(left_y, "Open Time", f"{open_time:.2f} s")

        # 5. Draw Right Panel Contents (Pose & Decision Engine)
        right_x = width - panel_w
        right_y = panel_y + 40

        # Pose Metrics
        head_pose = metrics.get("head_pose", {})
        yaw = head_pose.get("yaw", 0.0)
        pitch = head_pose.get("pitch", 0.0)
        roll = head_pose.get("roll", 0.0)
        pose_valid = head_pose.get("valid", False)

        pose_status_str = "TRACKING" if pose_valid else "SEARCHING"
        pose_status_color = (0, 255, 0) if pose_valid else (0, 0, 255)

        # Draw Pose values next to Reticle
        reticle_size = 75
        self.draw_pose_reticle(
            frame,
            x=right_x,
            y=right_y,
            size=reticle_size,
            yaw=yaw,
            pitch=pitch,
            roll=roll,
            valid=pose_valid,
            active_color=state_color
        )

        val_x_offset = right_x + reticle_size + 10
        cv2.putText(frame, "Head Pose Status", (val_x_offset, right_y + 10), self.font, self.font_scale_labels, self.color_muted, self.thickness, cv2.LINE_AA)
        cv2.putText(frame, pose_status_str, (val_x_offset, right_y + 25), self.font, 0.45, pose_status_color, self.thickness, cv2.LINE_AA)

        p_str = f"P: {pitch:+.1f}" if pose_valid else "P: N/A"
        y_str = f"Y: {yaw:+.1f}" if pose_valid else "Y: N/A"
        r_str = f"R: {roll:+.1f}" if pose_valid else "R: N/A"
        cv2.putText(frame, p_str, (val_x_offset, right_y + 40), self.font, self.font_scale_values, self.color_text, self.thickness, cv2.LINE_AA)
        cv2.putText(frame, y_str, (val_x_offset, right_y + 55), self.font, self.font_scale_values, self.color_text, self.thickness, cv2.LINE_AA)
        cv2.putText(frame, r_str, (val_x_offset, right_y + 70), self.font, self.font_scale_values, self.color_text, self.thickness, cv2.LINE_AA)

        right_y += reticle_size + 15

        # Divider
        cv2.line(frame, (right_x, right_y - 5), (right_x + panel_w - 20, right_y - 5), self.color_border, 1)
        right_y += 10

        # Decision Engine Metrics
        score = metrics.get("drowsiness_score", 0.0)
        confidence = metrics.get("confidence", 0.0)
        cooccurrence = metrics.get("cooccurrence", 0)
        explanation = metrics.get("explanation", "")

        def draw_kv_right(y_pos: int, label: str, val: str, val_color: Tuple[int, int, int] = self.color_text) -> None:
            cv2.putText(frame, label, (right_x, y_pos), self.font, self.font_scale_labels, self.color_muted, self.thickness, cv2.LINE_AA)
            cv2.putText(frame, val, (right_x + panel_w - 100, y_pos), self.font, self.font_scale_values, val_color, self.thickness, cv2.LINE_AA)

        draw_kv_right(right_y, "Drowsiness Score", f"{score:.0f} / 100", state_color)
        right_y += self.line_height

        # Score progress bar
        self.draw_progress_bar(
            frame,
            x=right_x,
            y=right_y,
            w=panel_w - 20,
            h=8,
            value=score,
            max_value=100.0,
            threshold=30.0,  # Warning alert limit
            color=state_color
        )
        right_y += self.line_height

        draw_kv_right(right_y, "Confidence", f"{confidence:.0f}%")
        right_y += self.line_height

        self.draw_progress_bar(
            frame,
            x=right_x,
            y=right_y,
            w=panel_w - 20,
            h=6,
            value=confidence,
            max_value=100.0,
            color=self.color_alert
        )
        right_y += self.line_height

        draw_kv_right(right_y, "Co-occurrence", f"{cooccurrence} / 3")
        right_y += self.line_height

        # Draw Co-occurrence Badges
        badge_w, badge_h = 16, 12
        for i in range(3):
            badge_x = right_x + (i * 22)
            badge_bg = state_color if i < cooccurrence else (40, 40, 48)
            cv2.rectangle(frame, (badge_x, right_y), (badge_x + badge_w, right_y + badge_h), badge_bg, -1)
            cv2.rectangle(frame, (badge_x, right_y), (badge_x + badge_w, right_y + badge_h), (80, 80, 88), 1)
        right_y += badge_h + 15

        # Reason / Explanation
        cv2.putText(frame, "PRIMARY DECISION REASON:", (right_x, right_y), self.font, 0.4, self.color_muted, 1, cv2.LINE_AA)
        right_y += 15

        wrapped_lines = self._wrap_text(explanation, panel_w - 20)
        for line in wrapped_lines[:3]:  # Max 3 lines to fit inside box
            cv2.putText(frame, line, (right_x, right_y), self.font, 0.38, self.color_text, 1, cv2.LINE_AA)
            right_y += 14

        # 6. Render Footer Panel
        footer_h = 45
        footer_y = height - footer_h
        recent_event = metrics.get("recent_event", "No events.")
        alert_status = metrics.get("alert_status", "System ready.")

        # If highly drowsy, flash footer red to grab attention
        is_critical = "HIGHLY" in drowsiness_state.upper()
        footer_bg = (20, 20, 90) if is_critical else self.color_bg
        footer_border = (80, 80, 240) if is_critical else self.color_border

        footer_overlay = frame.copy()
        cv2.rectangle(footer_overlay, (0, footer_y), (width, height), footer_bg, -1)
        cv2.addWeighted(footer_overlay, 0.85, frame, 0.15, 0, frame)

        cv2.line(frame, (0, footer_y), (width, footer_y), footer_border, 1)

        # Event and Alert Status text in Footer
        event_str = f"EVENT: {recent_event}"
        status_str = f"ALERTS: {alert_status}"

        # Clean event string length to fit
        max_event_chars = int(width * 0.09)
        if len(event_str) > max_event_chars:
            event_str = event_str[:max_event_chars-3] + "..."

        cv2.putText(
            frame,
            event_str,
            (15, footer_y + 26),
            self.font,
            0.42,
            self.color_text,
            1,
            cv2.LINE_AA
        )

        (s_w, s_h), _ = cv2.getTextSize(status_str, self.font, 0.42, 1)
        cv2.putText(
            frame,
            status_str,
            (width - s_w - 15, footer_y + 26),
            self.font,
            0.42,
            self.color_muted,
            1,
            cv2.LINE_AA
        )

        return frame
