"""
Student Drowsiness Detection System - Configuration Manager

Manages persistent UI display preferences, camera selection index, and notification toggles
inside Streamlit st.session_state.app_config.
Does NOT modify any backend AI detection algorithms or math calculators.
"""

import streamlit as st
from typing import Dict, Any


class ConfigurationManager:
    """
    Handles loading, updating, and saving user UI preferences.
    """

    DEFAULT_CONFIG: Dict[str, Any] = {
        "app_version": "v2.5 Enterprise Edition",
        "theme": "Dark Modern UI",
        "refresh_fps": 30,
        "default_page": "Dashboard",
        "time_format": "24 Hour",
        "language": "English (US)",
        "camera_id": 0,
        "resolution": "1280x720",
        "audio_enabled": True,
        "volume": 80,
        "animations_enabled": True,
        "desktop_notifications": False,
        "dark_mode": True,
        "zoom_level": 100,
        "show_telemetry_panels": True,
        "compact_view": False,
        "show_fps": True,
    }

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """
        Returns the current UI configuration dictionary from st.session_state.
        """
        if "app_config" not in st.session_state:
            st.session_state.app_config = cls.DEFAULT_CONFIG.copy()
        return st.session_state.app_config

    @classmethod
    def update_config(cls, updates: Dict[str, Any]) -> None:
        """
        Updates specific configuration keys.
        """
        config = cls.get_config()
        config.update(updates)
        st.session_state.app_config = config
