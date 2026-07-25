"""
Student Drowsiness Detection System - Reports & Export Center Sub-Page
"""

import streamlit as st
import pandas as pd
from dashboard.components.report_summary import render_report_summary
from dashboard.components.export_panel import render_export_panel
from dashboard.components.report_history import render_report_history
from dashboard.components.analytics_dashboard import render_analytics_dashboard
from dashboard.utils.mock_data import MockTelemetryProvider

st.set_page_config(page_title="Reports & Export Center", page_icon="📊", layout="wide")

st.title("📊 Reports & Export Center")
st.markdown("Review completed monitoring sessions, inspect detailed AI telemetry results, and download session reports.")

# Fetch telemetry payload & history buffer from session_state
if "telemetry_provider" not in st.session_state:
    st.session_state.telemetry_provider = MockTelemetryProvider()

raw_telemetry = st.session_state.telemetry_provider.get_telemetry()

# History DataFrame
history_list = st.session_state.get("telemetry_history", [])
history_df = pd.DataFrame(history_list) if history_list else None

# 1. Render Session Overview & 11 Detailed Result Metrics
render_report_summary(raw_telemetry)

# 2. Render Export Controls Panel (CSV, JSON, PDF)
render_export_panel(raw_telemetry, history_df)

# 3. Render Historical Session Reports Catalog
render_report_history()

# 4. Render Interactive Session Analytics Suite (Plotly Charts & KPI Grid)
render_analytics_dashboard(raw_telemetry, history_df)
