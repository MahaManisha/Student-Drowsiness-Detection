"""
Unit tests for the simplified HUDVisualizer module.
Verifies clean AI visualization rendering, state color mapping, 3D pose axis drawing,
and graceful handling of empty metrics payloads.
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

    assert vis.get_state_color("HIGHLY_DROWSY") == vis.color_highly
    assert vis.get_state_color("highly drowsy") == vis.color_highly
    assert vis.get_state_color("DROWSY") == vis.color_drowsy
    assert vis.get_state_color("SLIGHTLY_DROWSY") == vis.color_slightly
    assert vis.get_state_color("ALERT") == vis.color_alert
    assert vis.get_state_color("unknown_state") == vis.color_alert


def test_pose_axis_render() -> None:
    """Verify 3D head pose axis rendering on frame."""
    vis = HUDVisualizer()
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    rvec = np.array([0.1, 0.2, 0.0], dtype=np.float64)
    tvec = np.array([0.0, 0.0, 500.0], dtype=np.float64)

    out_frame = vis.draw_pose_axis(frame, rvec, tvec)
    assert out_frame.shape == (480, 640, 3)
    # Pose axis lines should draw non-zero pixels
    assert np.any(out_frame > 0)


def test_hud_render_success() -> None:
    """Verify that HUDVisualizer returns valid frame with or without pose vectors."""
    vis = HUDVisualizer()
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    dummy_metrics = {
        "head_pose": {
            "yaw": 5.2,
            "pitch": -3.1,
            "roll": 1.2,
            "valid": True,
            "rvec": np.array([0.1, 0.2, 0.0], dtype=np.float64),
            "tvec": np.array([0.0, 0.0, 500.0], dtype=np.float64)
        }
    }

    out_frame = vis.draw(frame, dummy_metrics)
    assert out_frame.shape == (480, 640, 3)
    assert np.any(out_frame > 0)


def test_hud_render_graceful_handling_missing_keys() -> None:
    """Verify that HUDVisualizer handles empty or missing metrics dictionary gracefully."""
    vis = HUDVisualizer()
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    out_frame = vis.draw(frame, {})
    assert out_frame.shape == (480, 640, 3)
