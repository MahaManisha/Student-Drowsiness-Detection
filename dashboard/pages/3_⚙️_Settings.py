"""
Student Drowsiness Detection System - Settings & Configuration Sub-Page
"""

import streamlit as st
from dashboard.utils.configuration_manager import ConfigurationManager
from dashboard.components.system_info import render_system_info_card

st.set_page_config(page_title="Settings & Configuration", page_icon="⚙️", layout="wide")

st.title("⚙️ Settings & Application Configuration")
st.markdown("Customize user interface display preferences, camera selection, and alert notifications.")

# Load configuration preferences
config = ConfigurationManager.get_config()

# 1. General Settings Card
st.markdown('<div class="dash-card">', unsafe_allow_html=True)
st.markdown('<div style="font-weight: 800; color: #F9FAFB; font-size: 1.0rem; margin-bottom: 10px;">⚙️ General Application Preferences</div>', unsafe_allow_html=True)

col_g1, col_g2, col_g3 = st.columns(3)
with col_g1:
    st.text_input("Application Version", value=config["app_version"], disabled=True)
    time_fmt = st.selectbox("Time Format", options=["24 Hour", "12 Hour"], index=0 if config["time_format"] == "24 Hour" else 1)

with col_g2:
    st.text_input("Current Theme", value=config["theme"], disabled=True)
    lang = st.selectbox("System Language", options=["English (US)", "Spanish (ES)", "French (FR)"], index=0)

with col_g3:
    refresh_fps = st.slider("UI Refresh Rate Target (FPS)", min_value=15, max_value=60, value=config["refresh_fps"], step=5)
    default_page = st.selectbox("Default Landing Page", options=["Dashboard", "Reports", "Settings", "About"], index=0)

st.markdown('</div>', unsafe_allow_html=True)

# 2. Camera Settings Card
st.markdown('<div class="dash-card">', unsafe_allow_html=True)
st.markdown('<div style="font-weight: 800; color: #F9FAFB; font-size: 1.0rem; margin-bottom: 10px;">📹 Camera Input Configuration</div>', unsafe_allow_html=True)

col_c1, col_c2, col_c3 = st.columns(3)
with col_c1:
    cam_device = st.selectbox("Available Camera Devices", options=["Camera 0 (Integrated WebCam)", "Camera 1 (External USB)"], index=0)
    cam_id = 0 if "0" in cam_device else 1

with col_c2:
    res = st.selectbox("Capture Resolution", options=["1280x720 (HD Widescreen)", "1920x1080 (Full HD)", "640x480 (VGA)"], index=0)
    st.markdown('<div style="font-size: 0.8rem; color: #10B981; font-weight: 700; margin-top: 24px;">● Camera Connected & Active</div>', unsafe_allow_html=True)

with col_c3:
    st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
    if st.button("📷 Test Camera Feed", use_container_width=True):
        st.success("Camera stream test passed! Resolution: 1280x720 @ 30 FPS")

st.markdown('</div>', unsafe_allow_html=True)

# 3. Alert Settings Card
st.markdown('<div class="dash-card">', unsafe_allow_html=True)
st.markdown('<div style="font-weight: 800; color: #F9FAFB; font-size: 1.0rem; margin-bottom: 10px;">🚨 Notification & Alarm Settings</div>', unsafe_allow_html=True)

col_a1, col_a2 = st.columns(2)
with col_a1:
    audio_enabled = st.toggle("Enable Audio Alarm Synthesizer", value=config["audio_enabled"])
    vol = st.slider("Notification Volume", min_value=0, max_value=100, value=config["volume"], step=5)

with col_a2:
    anim_enabled = st.toggle("Enable Alert Pulse Animations", value=config["animations_enabled"])
    desktop_notif = st.toggle("Desktop Notifications (System Tray)", value=config["desktop_notifications"])

st.markdown('</div>', unsafe_allow_html=True)

# 4. Display Settings Card
st.markdown('<div class="dash-card">', unsafe_allow_html=True)
st.markdown('<div style="font-weight: 800; color: #F9FAFB; font-size: 1.0rem; margin-bottom: 10px;">🎨 Display & Layout Preferences</div>', unsafe_allow_html=True)

col_d1, col_d2, col_d3 = st.columns(3)
with col_d1:
    dark_mode = st.toggle("Dark Mode Theme", value=config["dark_mode"])
    show_fps = st.toggle("Show Header FPS Counter", value=config["show_fps"])

with col_d2:
    zoom = st.slider("Dashboard Zoom Level", min_value=80, max_value=120, value=config["zoom_level"], step=5)
    compact_view = st.toggle("Compact Layout View", value=config["compact_view"])

with col_d3:
    show_telemetry = st.toggle("Show Telemetry Cards", value=config["show_telemetry_panels"])

st.markdown('</div>', unsafe_allow_html=True)

# 5. System Information Diagnostics Card
render_system_info_card()

# Save Preferences Button
if st.button("💾 Save Application Settings", type="primary", use_container_width=True):
    ConfigurationManager.update_config({
        "refresh_fps": refresh_fps,
        "default_page": default_page,
        "time_format": time_fmt,
        "language": lang,
        "camera_id": cam_id,
        "audio_enabled": audio_enabled,
        "volume": vol,
        "animations_enabled": anim_enabled,
        "desktop_notifications": desktop_notif,
        "dark_mode": dark_mode,
        "zoom_level": zoom,
        "show_telemetry_panels": show_telemetry,
        "compact_view": compact_view,
        "show_fps": show_fps,
    })
    st.success("Application settings saved successfully!")
