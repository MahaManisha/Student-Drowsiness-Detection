"""
Unit tests for the HUDVisualizer module (Phase 12.2).
Verifies that the HUD visualizer renders on input frames, maps states to correct colors,
wraps text correctly, and handles missing/partial metrics payloads gracefully.
"""

import numpy as np
import pytest
from dashboard.hud import HUDVisualizer


def test_hud_visualizer_initialization() -> None:
    """Verify default properties of HUDVisualizer are initialized."""
    vis = HUDVisualizer()
    assert vis.font_scale_labels == 0.45
    assert vis.line_height == 20
    assert len(vis.color_bg) == 3


def test_state_color_mapping() -> None:
    """Verify that drowsiness states map to the correct premium colors."""
    vis = HUDVisualizer()

    # Highly Drowsy maps to highly color
    assert vis.get_state_color("HIGHLY_DROWSY") == vis.color_highly
    assert vis.get_state_color("highly drowsy") == vis.color_highly

    # Drowsy maps to drowsy color
    assert vis.get_state_color("DROWSY") == vis.color_drowsy

    # Slightly Drowsy maps to slightly color
    assert vis.get_state_color("SLIGHTLY_DROWSY") == vis.color_slightly

    # Alert/Others map to alert color
    assert vis.get_state_color("ALERT") == vis.color_alert
    assert vis.get_state_color("unknown_state") == vis.color_alert


def test_text_wrapping() -> None:
    """Verify text wrapping limits line width based on OpenCV text size."""
    vis = HUDVisualizer()
    long_text = "This is an extremely long explanation message describing multiple simultaneous indicators of drowsiness"
    
    # Wrapping with a small width should yield multiple lines
    wrapped_lines = vis._wrap_text(long_text, max_width=150)
    assert len(wrapped_lines) > 1
    assert " ".join(wrapped_lines) == long_text


def test_hud_render_success() -> None:
    """Verify that drawing HUD elements updates the frame and returns a valid image."""
    vis = HUDVisualizer()
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    dummy_metrics = {
        "session_time": "01:23:45",
        "fps": 29.5,
        "drowsiness_state": "DROWSY",
        "drowsiness_score": 65.0,
        "confidence": 75.0,
        "cooccurrence": 2,
        "explanation": "Prolonged eye closure, excessive yawning.",
        "blink_count": 12,
        "closed_frames": 0,
        "closed_time": 0.0,
        "yawn_count": 2,
        "open_time": 0.0,
        "ear_metrics": {
            "left_ear": 0.28,
            "right_ear": 0.29,
            "avg_ear": 0.285,
            "threshold": 0.25,
            "state": "OPEN"
        },
        "mar_metrics": {
            "mar": 0.32,
            "threshold": 0.60,
            "state": "CLOSED"
        },
        "head_pose": {
            "yaw": 5.2,
            "pitch": -3.1,
            "roll": 1.2,
            "valid": True
        },
        "recent_event": "State changed to DROWSY",
        "alert_status": "HUD ACTIVE | AUDIO READY"
    }

    out_frame = vis.draw(frame, dummy_metrics)
    assert out_frame.shape == (480, 640, 3)
    # The output frame should no longer be completely black (all zeros)
    assert np.any(out_frame > 0)


def test_hud_render_graceful_handling_missing_keys() -> None:
    """Verify that HUDVisualizer does not crash when metrics dictionary is empty or missing key structures."""
    vis = HUDVisualizer()
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Empty metrics should use defaults and run without exceptions
    out_frame = vis.draw(frame, {})
    assert out_frame.shape == (480, 640, 3)
    assert np.any(out_frame > 0)
