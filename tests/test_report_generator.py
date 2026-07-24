"""
Unit tests for the ReportGenerator module (Phase 12.5).
Verifies that the generator parses events, evaluates session attentiveness ratings,
and correctly compiles structured reports in Markdown.
"""

import json
from pathlib import Path
import pytest
from reports.report_generator import ReportGenerator


def test_report_generator_assessment() -> None:
    """Verify state time ratios evaluate to expected attentiveness ratings."""
    dummy_stats = {
        "total_session_time": 100.0,
        "number_of_alerts": 0,
        "time_spent_in_states": {
            "ALERT": 90.0,
            "SLIGHTLY_DROWSY": 10.0,
            "DROWSY": 0.0,
            "HIGHLY_DROWSY": 0.0
        }
    }
    
    # 1. 90% ALERT -> EXCELLENT
    gen = ReportGenerator(dummy_stats, "dummy_path.json")
    a1 = gen.get_overall_assessment()
    assert a1["rating"] == "EXCELLENT"
    assert "🟢" in a1["badge"]

    # 2. 30% SLIGHTLY_DROWSY -> MILD FATIGUE
    dummy_stats["time_spent_in_states"] = {
        "ALERT": 70.0,
        "SLIGHTLY_DROWSY": 30.0,
        "DROWSY": 0.0,
        "HIGHLY_DROWSY": 0.0
    }
    a2 = gen.get_overall_assessment()
    assert a2["rating"] == "ATTENTION REQUIRED"
    assert "🟡" in a2["badge"]

    # 3. 20% DROWSY -> MODERATE DROWSINESS
    dummy_stats["time_spent_in_states"] = {
        "ALERT": 80.0,
        "SLIGHTLY_DROWSY": 0.0,
        "DROWSY": 20.0,
        "HIGHLY_DROWSY": 0.0
    }
    a3 = gen.get_overall_assessment()
    assert a3["rating"] == "WARNING"
    assert "🟠" in a3["badge"]

    # 4. 15% HIGHLY_DROWSY -> CRITICAL RISK
    dummy_stats["time_spent_in_states"] = {
        "ALERT": 85.0,
        "SLIGHTLY_DROWSY": 0.0,
        "DROWSY": 0.0,
        "HIGHLY_DROWSY": 15.0
    }
    a4 = gen.get_overall_assessment()
    assert a4["rating"] == "CRITICAL ATTENTION REQUIRED"
    assert "🔴" in a4["badge"]


def test_report_generator_event_parsing(tmp_path: Path) -> None:
    """Verify that JSON Lines event logs are parsed correctly into dictionaries."""
    log_file = tmp_path / "drowsiness_log.json"
    
    e1 = {"timestamp": "2026-07-24T10:45:00Z", "event_type": "student_became_slightly_drowsy", "state": "SLIGHTLY_DROWSY", "score": 35.0, "confidence": 75.0, "duration": 5.0}
    e2 = {"timestamp": "2026-07-24T10:45:10Z", "event_type": "alert_triggered", "state": "SLIGHTLY_DROWSY", "score": 35.0, "confidence": 75.0, "duration": 0.0}
    
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(e1) + "\n")
        f.write(json.dumps(e2) + "\n")

    gen = ReportGenerator({}, str(log_file))
    parsed = gen.parse_events()
    
    assert len(parsed) == 2
    assert parsed[0]["event_type"] == "student_became_slightly_drowsy"
    assert parsed[1]["event_type"] == "alert_triggered"


def test_report_generator_file_generation(tmp_path: Path) -> None:
    """Verify that ReportGenerator outputs a valid Markdown report file."""
    log_file = tmp_path / "drowsiness_log.json"
    report_file = tmp_path / "summary_report.md"

    e1 = {"timestamp": "2026-07-24T10:45:00.123456Z", "event_type": "student_became_slightly_drowsy", "state": "SLIGHTLY_DROWSY", "score": 35.0, "confidence": 75.0, "duration": 5.0}
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(e1) + "\n")

    dummy_stats = {
        "total_session_time": 100.0,
        "average_ear": 0.2854,
        "average_mar": 0.3242,
        "blink_count": 24,
        "yawn_count": 1,
        "highest_score": 67.5,
        "longest_eye_closure": 1.45,
        "number_of_alerts": 2,
        "time_spent_in_states": {
            "ALERT": 90.0,
            "SLIGHTLY_DROWSY": 10.0,
            "DROWSY": 0.0,
            "HIGHLY_DROWSY": 0.0
        }
    }

    gen = ReportGenerator(dummy_stats, str(log_file))
    gen.generate_report(str(report_file))

    assert report_file.exists()
    report_content = report_file.read_text(encoding="utf-8")

    assert "# 📋 Student Drowsiness Monitoring: Session Summary Report" in report_content
    assert "## ⏱️ Session Overview" in report_content
    assert "## 📊 Key Performance Indicators (KPIs)" in report_content
    assert "## ⌛ State Duration Breakdown" in report_content
    assert "## 🕒 Timeline of Drowsiness Events" in report_content
    assert "Slightly Drowsy" in report_content
    assert "24" in report_content
