"""
Student Drowsiness Detection System - Part 4 Runtime Validation
This script simulates the runtime scenarios specified in Part 4 of the QA Audit request:
- Test 1: Normal blink
- Test 2: Five normal blinks
- Test 3: Eyes remain closed for 3 seconds (both with and without max duration limit)
- Test 4: Rapid blinking
- Test 5: EAR fluctuations near threshold (illustrating the threshold jitter issue and its fix)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from detection.eye_state_classifier import EyeState
from detection.temporal_eye_analyzer import TemporalEyeAnalyzer

def run_part4_tests():
    print("======================================================================")
    # Test 1: Normal Blink
    print("RUNNING TEST 1: Normal Blink")
    # Using min=1, max=15, fps=30
    analyzer = TemporalEyeAnalyzer(min_blink_duration=1, max_blink_duration=15, fps=30.0)
    
    # 10 frames OPEN
    for _ in range(10):
        analyzer.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, 0.35)
    
    # 3 frames CLOSED (blink duration = 3)
    for _ in range(3):
        analyzer.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.12)
        
    print(f"  During closure: Consecutive Closed = {analyzer.get_closed_frame_count()}, Duration = {analyzer.get_closed_duration_seconds():.3f}s")
    
    # Reopen (Frame 14)
    analyzer.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, 0.35)
    print(f"  After reopening: Blink Count = {analyzer.get_blink_count()}, Consecutive Closed = {analyzer.get_closed_frame_count()}")
    
    # Test 1 Verdict
    t1_pass = (analyzer.get_blink_count() == 1 and analyzer.get_closed_frame_count() == 0)
    print(f"  Test 1 Verdict: {'PASS' if t1_pass else 'FAIL'}")

    print("======================================================================")
    # Test 2: Five normal blinks
    print("RUNNING TEST 2: Five Normal Blinks")
    analyzer.clear_history()
    
    for i in range(5):
        # 5 frames OPEN
        for _ in range(5):
            analyzer.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, 0.35)
        # 3 frames CLOSED
        for _ in range(3):
            analyzer.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.12)
        # Reopen
        analyzer.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, 0.35)
        
    print(f"  After 5 blinks: Blink Count = {analyzer.get_blink_count()}")
    t2_pass = (analyzer.get_blink_count() == 5)
    print(f"  Test 2 Verdict: {'PASS' if t2_pass else 'FAIL'}")

    print("======================================================================")
    # Test 3: Eyes remain closed for 3 seconds (90 frames at 30 FPS)
    print("RUNNING TEST 3: Eyes remain closed for 3 seconds")
    
    # Scenario A: Standard analyzer with max_blink_duration=15 (drowsiness filter active)
    print("  Scenario 3A: Drowsiness filter active (max_blink_duration = 15)")
    analyzer_3a = TemporalEyeAnalyzer(min_blink_duration=2, max_blink_duration=15, fps=30.0)
    for _ in range(10):
        analyzer_3a.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, 0.35)
        
    mid_closed_counts = []
    mid_durations = []
    # Closed for 3 seconds (90 frames)
    for _ in range(90):
        analyzer_3a.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.10)
        mid_closed_counts.append(analyzer_3a.get_closed_frame_count())
        mid_durations.append(analyzer_3a.get_closed_duration_seconds())
        
    print(f"    During closure (max frames reached): Consecutive Closed = {max(mid_closed_counts)}, Closed Duration = {max(mid_durations):.3f}s")
    
    # Reopen
    analyzer_3a.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, 0.35)
    print(f"    After reopening: Blink Count = {analyzer_3a.get_blink_count()} (Expected 0, classified as drowsiness/microsleep)")
    print(f"    After reopening: Consecutive Closed = {analyzer_3a.get_closed_frame_count()} (Expected 0, resets on open)")
    
    # Scenario B: Analyzer configured with high max_blink_duration to allow counting long closure as 1 blink
    print("  Scenario 3B: High max_blink_duration (max_blink_duration = 150) to verify transition count")
    analyzer_3b = TemporalEyeAnalyzer(min_blink_duration=2, max_blink_duration=150, fps=30.0)
    for _ in range(10):
        analyzer_3b.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, 0.35)
    for _ in range(90):
        analyzer_3b.update(EyeState.CLOSED, EyeState.CLOSED, EyeState.CLOSED, 0.10)
    analyzer_3b.update(EyeState.OPEN, EyeState.OPEN, EyeState.OPEN, 0.35)
    print(f"    After reopening: Blink Count = {analyzer_3b.get_blink_count()} (Expected 1)")
    print(f"    After reopening: Consecutive Closed = {analyzer_3b.get_closed_frame_count()} (Expected 0)")
    
    t3_pass = (analyzer_3a.get_blink_count() == 0 and analyzer_3b.get_blink_count() == 1 and analyzer_3a.get_closed_frame_count() == 0)
    print(f"  Test 3 Verdict: {'PASS' if t3_pass else 'FAIL'}")

    print("======================================================================")
    # Test 4: Rapid blinking
    print("RUNNING TEST 4: Rapid Blinking")
    # Verify that every complete OPEN -> CLOSED -> OPEN cycle is counted exactly once.
    analyzer.clear_history()
    
    # Sequence of 3 rapid blinks (2 frames closed, 2 frames open)
    # 1. Open -> Closed -> Closed -> Open
    # 2. Open -> Closed -> Closed -> Open
    # 3. Open -> Closed -> Closed -> Open
    sequence = [
        EyeState.OPEN, EyeState.OPEN,
        EyeState.CLOSED, EyeState.CLOSED, EyeState.OPEN, EyeState.OPEN,
        EyeState.CLOSED, EyeState.CLOSED, EyeState.OPEN, EyeState.OPEN,
        EyeState.CLOSED, EyeState.CLOSED, EyeState.OPEN, EyeState.OPEN
    ]
    for state in sequence:
        analyzer.update(state, state, state, 0.12 if state == EyeState.CLOSED else 0.35)
        
    print(f"  Rapid Blinks count = {analyzer.get_blink_count()} (Expected 3)")
    t4_pass = (analyzer.get_blink_count() == 3)
    print(f"  Test 4 Verdict: {'PASS' if t4_pass else 'FAIL'}")

    print("======================================================================")
    # Test 5: EAR Fluctuations Near Threshold (0.248 - 0.252)
    print("RUNNING TEST 5: EAR Fluctuations Near Threshold (Threshold Jitter)")
    
    # Sequence of micro-fluctuations around 0.25 threshold
    jitter_ears = [0.252, 0.248, 0.252, 0.248, 0.252, 0.248, 0.252]
    # Corresponding states under classifier: OPEN -> CLOSED -> OPEN -> CLOSED -> OPEN -> CLOSED -> OPEN
    
    # Scenario A: min_blink_duration = 1 (No debounce)
    analyzer_no_debounce = TemporalEyeAnalyzer(min_blink_duration=1, max_blink_duration=15, fps=30.0)
    for ear in jitter_ears:
        state = EyeState.OPEN if ear >= 0.25 else EyeState.CLOSED
        analyzer_no_debounce.update(state, state, state, ear)
    print(f"  Without Debounce (min_blink_duration = 1): Blink Count = {analyzer_no_debounce.get_blink_count()} (Expected 3, indicating false positives!)")
    
    # Scenario B: min_blink_duration = 2 (Debounce active)
    analyzer_debounced = TemporalEyeAnalyzer(min_blink_duration=2, max_blink_duration=15, fps=30.0)
    for ear in jitter_ears:
        state = EyeState.OPEN if ear >= 0.25 else EyeState.CLOSED
        analyzer_debounced.update(state, state, state, ear)
    print(f"  With Debounce (min_blink_duration = 2): Blink Count = {analyzer_debounced.get_blink_count()} (Expected 0, false positives filtered!)")
    
    t5_pass = (analyzer_no_debounce.get_blink_count() == 3 and analyzer_debounced.get_blink_count() == 0)
    print(f"  Test 5 Verdict: {'PASS' if t5_pass else 'FAIL'}")
    print("======================================================================")
    
    all_passed = t1_pass and t2_pass and t3_pass and t4_pass and t5_pass
    print(f"OVERALL PART 4 RUNTIME VALIDATION: {'PASS' if all_passed else 'FAIL'}")

if __name__ == "__main__":
    run_part4_tests()
