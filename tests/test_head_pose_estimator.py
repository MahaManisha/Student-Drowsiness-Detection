"""
Unit tests for the HeadPoseEstimator module (Phase 10.1).
Verifies that HeadPoseEstimator initializes properly, holds the correct states,
tracks frame counts during updates, resets properly, and returns structured metrics.
"""

import pytest
import numpy as np
import config
from detection.head_pose_estimator import HeadPoseEstimator, HeadPoseResult


def test_head_pose_estimator_landmark_constants():
    """Verify that the landmark indices match configuration constants."""
    assert HeadPoseEstimator.LANDMARK_INDICES == [4, 152, 263, 33, 291, 61]
    assert HeadPoseEstimator.LANDMARK_INDICES == config.HEAD_POSE_LANDMARK_INDICES


def test_head_pose_estimator_initialization():
    """Verify that HeadPoseEstimator initializes with correct properties and default states."""
    estimator = HeadPoseEstimator()
    
    assert estimator.camera_matrix is None
    assert estimator.dist_coeffs is None
    assert estimator.yaw is None
    assert estimator.pitch is None
    assert estimator.roll is None
    assert estimator.frame_counter == 0


def test_head_pose_estimator_custom_matrices():
    """Verify constructor accepts custom camera parameter matrices."""
    cam_mat = np.eye(3, dtype=np.float32)
    dist_coef = np.zeros((4, 1), dtype=np.float32)
    
    estimator = HeadPoseEstimator(camera_matrix=cam_mat, dist_coeffs=dist_coef)
    
    assert np.array_equal(estimator.camera_matrix, cam_mat)
    assert np.array_equal(estimator.dist_coeffs, dist_coef)


def test_head_pose_estimator_estimate_valid():
    """Verify that estimate_head_pose computes valid angles and returns HeadPoseResult."""
    estimator = HeadPoseEstimator()
    mesh = np.zeros((478, 2), dtype=np.float32)
    # Set standard values for the 6 points
    mesh[4] = (0.5, 0.5)      # Nose tip
    mesh[152] = (0.5, 0.8)    # Chin
    mesh[263] = (0.6, 0.4)    # Left eye outer
    mesh[33] = (0.4, 0.4)     # Right eye outer
    mesh[291] = (0.58, 0.65)  # Left mouth corner
    mesh[61] = (0.42, 0.65)   # Right mouth corner

    result = estimator.estimate_head_pose(mesh, (480, 640))
    
    assert isinstance(result, HeadPoseResult)
    assert result.valid is True
    assert result.yaw is not None
    assert result.pitch is not None
    assert result.roll is not None
    assert estimator.frame_counter == 1


def test_head_pose_estimator_reset():
    """Verify orientation states and frame counters are reset successfully."""
    estimator = HeadPoseEstimator()
    estimator.yaw = 15.0
    estimator.pitch = -10.0
    estimator.roll = 5.0
    estimator.frame_counter = 150
    
    estimator.reset()
    assert estimator.yaw is None
    assert estimator.pitch is None
    assert estimator.roll is None
    assert estimator.frame_counter == 0


def test_head_pose_estimator_metrics():
    """Verify the metrics dictionary contains the required keys and types."""
    estimator = HeadPoseEstimator()
    
    # Before estimation (invalid)
    metrics = estimator.get_pose_metrics()
    assert isinstance(metrics, dict)
    assert "yaw" in metrics
    assert "pitch" in metrics
    assert "roll" in metrics
    assert metrics["valid"] is False
    
    # Mock active estimations
    estimator.yaw = 5.0
    estimator.pitch = -5.0
    estimator.roll = 2.0
    
    metrics = estimator.get_pose_metrics()
    assert metrics["yaw"] == 5.0
    assert metrics["pitch"] == -5.0
    assert metrics["roll"] == 2.0
    assert metrics["valid"] is True


def test_head_pose_estimator_solve_pnp_valid():
    """Verify that estimate_head_pose runs solvePnP and computes rvec/tvec on valid landmarks."""
    estimator = HeadPoseEstimator()
    mesh = np.zeros((478, 2), dtype=np.float32)
    # Set standard values for the 6 points
    mesh[4] = (0.5, 0.5)      # Nose tip
    mesh[152] = (0.5, 0.8)    # Chin
    mesh[263] = (0.6, 0.4)    # Left eye outer
    mesh[33] = (0.4, 0.4)     # Right eye outer
    mesh[291] = (0.58, 0.65)  # Left mouth corner
    mesh[61] = (0.42, 0.65)   # Right mouth corner

    result = estimator.estimate_head_pose(mesh, (480, 640))
    
    assert isinstance(result, HeadPoseResult)
    assert result.valid is True
    assert result.yaw is not None
    assert result.pitch is not None
    assert result.roll is not None
    
    # rvec and tvec must be computed successfully
    assert estimator.rvec is not None
    assert estimator.tvec is not None
    assert isinstance(estimator.rvec, np.ndarray)
    assert isinstance(estimator.tvec, np.ndarray)
    assert estimator.rvec.shape == (3, 1)
    assert estimator.tvec.shape == (3, 1)


def test_head_pose_estimator_solve_pnp_invalid():
    """Verify that estimate_head_pose handles invalid inputs safely without crashing."""
    estimator = HeadPoseEstimator()
    
    # 1. Null landmarks
    result = estimator.estimate_head_pose(None, (480, 640))
    assert result.yaw is None
    assert result.valid is False
    assert estimator.rvec is None
    assert estimator.tvec is None
    
    # 2. Invalid frame dimensions
    mesh = np.zeros((478, 2), dtype=np.float32)
    result = estimator.estimate_head_pose(mesh, (0, 640))
    assert result.yaw is None
    assert result.valid is False
    assert estimator.rvec is None
    assert estimator.tvec is None
    
    result = estimator.estimate_head_pose(mesh, (-100, 640))
    assert result.yaw is None
    assert result.valid is False
    assert estimator.rvec is None
    assert estimator.tvec is None


def test_head_pose_estimator_reset_vectors():
    """Verify that reset clears computed rotation and translation vectors."""
    estimator = HeadPoseEstimator()
    estimator.rvec = np.array([0.1, 0.2, 0.3])
    estimator.tvec = np.array([10.0, 20.0, 30.0])
    
    estimator.reset()
    assert estimator.rvec is None
    assert estimator.tvec is None

