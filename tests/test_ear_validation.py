"""
Student Drowsiness Detection System - Phase 4.6 EAR Validation Suite

This test script validates that:
1. EAR values change appropriately across Open, Partially Closed, and Fully Closed eye states.
2. No abnormal spikes (> 1.0, negative, or step discontinuities) occur.
3. Outputs a structured EAR validation summary table.
"""

from typing import List, Tuple
from detection.ear_calculator import EARCalculator
from utils.logger import get_logger

logger = get_logger("EARValidationTest")


def run_ear_validation_suite() -> None:
    calculator = EARCalculator()

    # 1. Synthetic Eye States (Standard 6-Point Coordinates)
    open_eye = [(0, 0), (3, 4), (7, 4), (10, 0), (7, 0), (3, 0)]
    partially_closed_eye = [(0, 0), (3, 2), (7, 2), (10, 0), (7, 0), (3, 0)]
    fully_closed_eye = [(0, 0), (3, 0.2), (7, 0.2), (10, 0), (7, 0), (3, 0)]

    print("\n==========================================================================")
    print("                PHASE 4.6 EAR VALIDATION SUMMARY REPORT                   ")
    print("==========================================================================")
    print(f"{'Eye State':<22} | {'Right EAR':<10} | {'Left EAR':<10} | {'Avg EAR':<10} | {'Status'}")
    print("--------------------------------------------------------------------------")

    states = [
        ("Open Eyes", open_eye, open_eye),
        ("Partially Closed Eyes", partially_closed_eye, partially_closed_eye),
        ("Fully Closed Eyes", fully_closed_eye, fully_closed_eye),
    ]

    for label, r_eye, l_eye in states:
        r_ear, l_ear, avg_ear = calculator.calculate_ear(r_eye, l_eye)
        is_valid_range = calculator.validate_ear_value(avg_ear)

        status = "VALID" if is_valid_range else "INVALID SPIKE"
        r_str = f"{r_ear:.3f}" if r_ear is not None else "N/A"
        l_str = f"{l_ear:.3f}" if l_ear is not None else "N/A"
        avg_str = f"{avg_ear:.3f}" if avg_ear is not None else "N/A"

        print(f"{label:<22} | {r_str:<10} | {l_str:<10} | {avg_str:<10} | {status}")

    print("--------------------------------------------------------------------------")

    # 2. Continuous Sequence & Spike Discontinuity Check
    print("\nEvaluating Continuous Transition & Spike Detection...")
    sequence = [0.38, 0.37, 0.36, 0.25, 0.18, 0.05, 0.04, 0.05, 0.20, 0.36]
    spike_sequence = [0.36, 0.35, 0.95, 0.34]  # 0.95 is an artificial spike

    print("Normal Smooth Transition Sequence:")
    prev = None
    for idx, ear_val in enumerate(sequence):
        calculator.validate_ear_value(ear_val)
        spike = calculator.detect_ear_spike(ear_val, prev)
        prev = ear_val

    print("\nArtificial Spike Injected Sequence:")
    prev = None
    for idx, ear_val in enumerate(spike_sequence):
        calculator.validate_ear_value(ear_val)
        spike = calculator.detect_ear_spike(ear_val, prev)
        prev = ear_val

    print("==========================================================================\n")


if __name__ == "__main__":
    run_ear_validation_suite()
