"""
Student Drowsiness Detection System - Session History Sub-Page
"""

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Session History", page_icon="📜", layout="wide")

st.title("📜 Session Logs & History")
st.markdown("Browse previous session records and structured JSON Lines event logs.")

history_data = [
    {"Session ID": "SES_20260725_01", "Date": "2026-07-25 08:00", "Duration": "01:24:15", "Avg EAR": 0.285, "Avg MAR": 0.180, "Max Score": 12.0, "Status": "COMPLETED"},
    {"Session ID": "SES_20260724_02", "Date": "2026-07-24 14:30", "Duration": "00:45:10", "Avg EAR": 0.271, "Avg MAR": 0.210, "Max Score": 48.5, "Status": "COMPLETED"},
    {"Session ID": "SES_20260724_01", "Date": "2026-07-24 09:15", "Duration": "02:10:00", "Avg EAR": 0.264, "Avg MAR": 0.245, "Max Score": 85.0, "Status": "CRITICAL ALERT"},
]

df = pd.DataFrame(history_data)
st.dataframe(df, use_container_width=True)
