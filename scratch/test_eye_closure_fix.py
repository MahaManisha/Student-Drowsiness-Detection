import sys
import pathlib
ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from detection.ear_calculator import EARCalculator
from detection.eye_state_classifier import EyeStateClassifier, EyeState

print("=== Testing Asymmetric Eye Closure Fix (User Screenshot Telemetry) ===")

ear_calc = EARCalculator(ear_threshold=0.240)
classifier = EyeStateClassifier(ear_threshold=0.240)

# User's exact values from screenshot:
# Right eye (facing camera): 0.272 (OPEN)
# Left eye (perspective foreshortened at 27.5 deg yaw): 0.182
r_ear = 0.272
l_ear = 0.182

avg_ear = ear_calc.calculate_avg_ear(r_ear, l_ear)
r_state, l_state, overall_state = classifier.classify_both_eyes(r_ear, l_ear)

print(f"Right EAR: {r_ear} ({r_state})")
print(f"Left EAR: {l_ear} ({l_state})")
print(f"Avg EAR: {avg_ear:.3f}")
print(f"Overall State: {overall_state}")

assert overall_state == EyeState.OPEN, f"Expected EyeState.OPEN, got {overall_state}"
assert avg_ear >= 0.240, f"Expected avg_ear >= 0.240, got {avg_ear}"

print("SUCCESS: Asymmetric eye false closure fix verified!")
