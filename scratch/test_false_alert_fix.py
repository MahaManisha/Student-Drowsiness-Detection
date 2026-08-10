import sys
import pathlib
ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from detection.drowsiness_decision_engine import StudentDrowsinessDecisionEngine

print("=== Testing False Alert Fix with User's Exact Screenshot Telemetry ===")

engine = StudentDrowsinessDecisionEngine()

# Telemetry matching screenshot:
# EYES: OPEN (EAR = 0.267, closed_duration = 0.0s)
# MOUTH: CLOSED (MAR = 0.032, is_active_yawn = False, yawn_count = 1 from earlier)
# HEAD POSE: Pitch = +11.1 deg (normal screen viewing), Yaw = 0.0, Roll = 0.0

eye_payload = {
    "blink_count": 5,
    "consecutive_closed_frames": 0,
    "closed_duration_seconds": 0.0
}
yawn_payload = {
    "yawn_count": 1,
    "consecutive_open_frames": 0,
    "yawn_duration_seconds": 0.0,
    "is_active_yawn": False,
    "mar_val": 0.032
}
pose_payload = {
    "yaw": 0.0,
    "pitch": 11.1,
    "roll": 0.0,
    "valid": True
}

metrics = engine.update(eye_payload, yawn_payload, pose_payload)

score = metrics["drowsiness_score"]
state = metrics["drowsiness_state"]
explanation = (metrics.get("drowsiness_result") or {}).get("explanation", "")

print(f"Result -> Score: {score:.1f}/100 | State: {state}")
print(f"Explanation: '{explanation}'")

assert score == 0.0, f"Expected 0.0 score for open eyes & closed mouth, got {score}"
assert state == "ALERT", f"Expected ALERT state, got {state}"

print("SUCCESS: False alert eliminated! Score is 0/100 (ALERT state).")
