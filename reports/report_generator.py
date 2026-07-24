"""
Student Drowsiness Detection System - Report Generator Module

This module provides the ReportGenerator class to parse session statistics and event
logs and compile a comprehensive Markdown session summary report.
"""

import json
from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Any, Dict, List


class ReportGenerator:
    """
    Parses telemetry statistics and JSON Lines event logs to generate a comprehensive
    Markdown report summarizing student attentiveness during a tracking session.
    """

    def __init__(self, stats_payload: Dict[str, Any], event_log_path: str) -> None:
        """
        Initializes the ReportGenerator.

        Args:
            stats_payload (Dict[str, Any]): Session statistics payload from tracker.
            event_log_path (str): File path to the JSON Lines structured session log.
        """
        self.stats = stats_payload
        self.event_log_path = Path(event_log_path)

    def parse_events(self) -> List[Dict[str, Any]]:
        """
        Parses the JSON Lines event log file and returns structured event dictionaries.

        Returns:
            List[Dict[str, Any]]: List of parsed event objects.
        """
        events = []
        if not self.event_log_path.exists():
            return events

        try:
            with open(self.event_log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            events.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except Exception:
            pass
        return events

    def get_overall_assessment(self) -> Dict[str, str]:
        """
        Analyzes session times and alerts to determine student attentiveness.

        Returns:
            Dict[str, str]: Dictionary containing:
                - "rating": Assessment level name (EXCELLENT, MODIBLE, WARNING, CRITICAL).
                - "badge": Markdown colored text/badge.
                - "description": Detailed description text.
        """
        total_time = self.stats.get("total_session_time", 0.0)
        state_times = self.stats.get("time_spent_in_states", {})
        alerts_count = self.stats.get("number_of_alerts", 0)

        # Retrieve times in warning/drowsy states
        alert_time = state_times.get("ALERT", 0.0)
        slightly_drowsy_time = state_times.get("SLIGHTLY_DROWSY", 0.0)
        drowsy_time = state_times.get("DROWSY", 0.0)
        highly_drowsy_time = state_times.get("HIGHLY_DROWSY", 0.0)

        # Calculate ratios
        if total_time > 0:
            alert_ratio = alert_time / total_time
            highly_drowsy_ratio = highly_drowsy_time / total_time
            drowsy_ratio = (drowsy_time + highly_drowsy_time) / total_time
        else:
            alert_ratio = 1.0
            highly_drowsy_ratio = 0.0
            drowsy_ratio = 0.0

        # Evaluation rules
        if highly_drowsy_ratio >= 0.10 or alerts_count >= 5 or highly_drowsy_time > 30.0:
            return {
                "rating": "CRITICAL ATTENTION REQUIRED",
                "badge": "🔴 **CRITICAL RISK**",
                "description": (
                    "Severe drowsiness, abnormal eye closures, or active microsleep risks "
                    "were detected during the session. High frequency of critical warning "
                    "triggers indicates severe fatigue. Stop studying and rest immediately."
                )
            }
        elif drowsy_ratio >= 0.15 or alerts_count >= 3:
            return {
                "rating": "WARNING",
                "badge": "🟠 **MODERATE DROWSINESS**",
                "description": (
                    "Frequent signs of moderate drowsiness detected. The student was in "
                    "drowsy or highly drowsy states for a significant portion of the session. "
                    "Breaks and a change of environment are highly recommended to prevent lapses in attention."
                )
            }
        elif slightly_drowsy_time / max(0.001, total_time) >= 0.25:
            return {
                "rating": "ATTENTION REQUIRED",
                "badge": "🟡 **MILD FATIGUE**",
                "description": (
                    "Mild fatigue detected. The student exhibited recurring patterns of "
                    "drooping eyelids and yawning. Monitor alertness levels closely."
                )
            }
        else:
            return {
                "rating": "EXCELLENT",
                "badge": "🟢 **HIGHLY ATTENTIVE**",
                "description": (
                    "The student remained highly alert and focused throughout the session. "
                    "Minimal warning thresholds were reached. Attentiveness is optimal."
                )
            }

    def format_duration(self, seconds: float) -> str:
        """Helper to format seconds into readable string."""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hrs > 0:
            return f"{hrs}h {mins}m {secs}s"
        elif mins > 0:
            return f"{mins}m {secs}s"
        else:
            return f"{secs}s"

    def generate_report(self, output_path: str) -> None:
        """
        Assembles KPIs, state breakdown, assessment, and timeline into a Markdown file.

        Args:
            output_path (str): File path to write the Markdown report to.
        """
        current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # 1. Calculate overall assessment
        assessment = self.get_overall_assessment()
        
        # 2. Parse event timeline
        raw_events = self.parse_events()
        
        # Format session times
        total_time = self.stats.get("total_session_time", 0.0)
        duration_str = self.format_duration(total_time)

        # Start Markdown building
        md = []
        md.append("# 📋 Student Drowsiness Monitoring: Session Summary Report")
        md.append(f"\n*Generated on: {current_date}*")
        md.append("\n---")
        
        # Session Metadata Table
        md.append("\n## ⏱️ Session Overview")
        md.append("\n| Parameter | Value |")
        md.append("| :--- | :--- |")
        md.append(f"| **Session Duration** | {duration_str} ({total_time:.2f} seconds) |")
        md.append(f"| **Attentiveness Rating** | {assessment['badge']} |")
        md.append(f"| **Total Warnings Triggered** | {self.stats.get('number_of_alerts', 0)} |")
        
        # Assessment Detail
        md.append("\n### 📝 Attentiveness Assessment")
        md.append(f"> {assessment['description']}")

        # KPIs Table
        md.append("\n## 📊 Key Performance Indicators (KPIs)")
        md.append("\n| Metric | Session Value | Description |")
        md.append("| :--- | :---: | :--- |")
        md.append(f"| **Total Blinks** | `{self.stats.get('blink_count', 0)}` | Cumulative number of normal blink events. |")
        md.append(f"| **Total Yawns** | `{self.stats.get('yawn_count', 0)}` | Cumulative number of yawn cycles detected. |")
        md.append(f"| **Average EAR** | `{self.stats.get('average_ear', 0.0):.4f}` | Eye Aspect Ratio running average (normal ~0.25-0.35). |")
        md.append(f"| **Average MAR** | `{self.stats.get('average_mar', 0.0):.4f}` | Mouth Aspect Ratio running average (normal ~0.15-0.30). |")
        md.append(f"| **Highest Drowsiness Score** | `{self.stats.get('highest_score', 0.0):.1f} / 100` | Peak drowsiness score evaluated by decision engine. |")
        md.append(f"| **Longest Eye Closure** | `{self.stats.get('longest_eye_closure', 0.0):.2f} seconds` | Max consecutive duration eyes remained closed. |")

        # State Duration Breakdown Table
        md.append("\n## ⌛ State Duration Breakdown")
        md.append("\n| Drowsiness State | Time Spent | Percentage | Visual Trend |")
        md.append("| :--- | :---: | :---: | :--- |")
        
        state_times = self.stats.get("time_spent_in_states", {})
        for state in ["ALERT", "SLIGHTLY_DROWSY", "DROWSY", "HIGHLY_DROWSY"]:
            st_time = state_times.get(state, 0.0)
            pct = (st_time / total_time * 100.0) if total_time > 0 else 0.0
            # Draw ASCII bar graph for visual trend
            bar_len = int(pct / 5)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            
            clean_name = state.replace("_", " ").title()
            md.append(f"| {clean_name} | {st_time:.2f}s | {pct:.1f}% | `{bar}` |")

        # Event Timeline Section
        md.append("\n## 🕒 Timeline of Drowsiness Events")
        if not raw_events:
            md.append("\n*No state transitions or warning alerts were recorded during this session.*")
        else:
            md.append("\n| Timestamp | Event Type | Drowsiness State | Score | Confidence | Duration | Description / Details |")
            md.append("| :--- | :--- | :---: | :---: | :---: | :---: | :--- |")
            
            for ev in raw_events:
                # Format timestamp to show HH:MM:SS
                raw_time = ev.get("timestamp", "")
                try:
                    dt = datetime.strptime(raw_time, "%Y-%m-%dT%H:%M:%S.%fZ")
                except ValueError:
                    try:
                        dt = datetime.strptime(raw_time, "%Y-%m-%dT%H:%M:%SZ")
                    except ValueError:
                        dt = None
                
                time_str = dt.strftime("%H:%M:%S") if dt else raw_time
                
                # Humanize event types
                ev_type = ev.get("event_type", "")
                ev_name = ev_type.replace("_", " ").title()
                
                # Highlight alerts or transitions
                if "triggered" in ev_type:
                    ev_name = f"🚨 **{ev_name}**"
                elif "ended" in ev_type:
                    ev_name = f"✅ **{ev_name}**"
                elif "highly" in ev_type:
                    ev_name = f"🔴 {ev_name}"
                elif "slightly" in ev_type or "drowsy" in ev_type:
                    ev_name = f"🟡 {ev_name}"

                state = ev.get("state", "ALERT").replace("_", " ").title()
                score = ev.get("score", 0.0)
                conf = ev.get("confidence", 0.0)
                dur = ev.get("duration", 0.0)
                msg = ev.get("message", "-")

                # Format duration context
                if "became" in ev_type:
                    dur_str = f"Lasted {dur:.1f}s"
                elif "ended" in ev_type:
                    dur_str = f"Active {dur:.1f}s"
                else:
                    dur_str = "-"

                md.append(f"| {time_str} | {ev_name} | {state} | {score:.1f} | {conf:.0f}% | {dur_str} | {msg} |")

        # Save MD output file
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(md) + "\n")
            
            # Print console message
            print(f"Session Summary Report successfully generated: {path}")
        except Exception:
            pass
