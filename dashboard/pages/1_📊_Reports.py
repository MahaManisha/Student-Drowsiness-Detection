"""
Student Drowsiness Detection System - Reports & Export Center Sub-Page
"""

import streamlit as st
import pandas as pd
from dashboard.components.report_summary import render_report_summary
from dashboard.components.export_panel import render_export_panel
from dashboard.components.report_history import render_report_history
from dashboard.components.analytics_dashboard import render_analytics_dashboard
from dashboard.components.lifecycle import get_singleton_camera_manager

st.set_page_config(page_title="Reports & Export Center", page_icon="📊", layout="wide")

st.title("📊 Reports & Export Center")
st.markdown("Review completed monitoring sessions, inspect detailed AI telemetry results, and download session reports.")

# Retrieve active camera manager telemetry if available
camera_mgr = None
try:
    camera_mgr = get_singleton_camera_manager()
except Exception:
    pass

snapshot = camera_mgr.get_latest_snapshot() if camera_mgr else None
raw_telemetry = snapshot.telemetry if snapshot else {}

# History DataFrame
history_list = st.session_state.get("telemetry_history", [])
history_df = pd.DataFrame(history_list) if history_list else None

# 1. Render Export Controls Panel FIRST (CSV, JSON, PDF Downloads immediately visible at top!)
render_export_panel(raw_telemetry, history_df)

# 2. Render Session Overview & Detailed Result Metrics
render_report_summary(raw_telemetry)

# 3. Render Historical Session Reports Catalog
render_report_history()

# 4. Render Interactive Session Analytics Suite (Plotly Charts & KPI Grid)
render_analytics_dashboard(raw_telemetry, history_df)
