# 🚀 Streamlit Dashboard Setup & Execution Guide

This document provides step-by-step instructions for installing dependencies and launching the **Student Drowsiness Detection System Streamlit Dashboard**.

---

## 📦 1. Installation Instructions

### Step 1: Activate Virtual Environment
Open your terminal in the workspace root directory and activate your Python virtual environment:

```powershell
# Windows PowerShell
.\venv\Scripts\activate
```

### Step 2: Install Streamlit Ecosystem Packages
Run `pip` to install the required dashboard packages listed in `requirements.txt`:

```powershell
pip install -r requirements.txt
```

Alternatively, install the Streamlit packages directly:

```powershell
pip install streamlit plotly streamlit-option-menu streamlit-extras Pillow
```

---

## 🏃 2. Launching the Streamlit Dashboard

Execute the following command from the workspace root directory:

```powershell
streamlit run dashboard/app.py
```

### Expected Startup Output:
```text
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

---

## 🎨 3. Dashboard Structure & Layout

```
dashboard/
├── app.py                      # Main Streamlit application driver
├── components/                 # Modular UI components
│   ├── header.py               # Top Header (Timer, FPS, Status Pill)
│   ├── sidebar.py              # Left Sidebar (Navigation Option Menu)
│   ├── camera_panel.py         # Center Camera Viewport
│   ├── telemetry_panel.py      # Right Panel Eye & Mouth Analysis
│   ├── head_pose_panel.py      # Right Panel Head Pose Plotly Compass
│   ├── decision_panel.py       # Right Panel AI Decision Engine
│   └── bottom_analytics.py     # Bottom Section Statistics & Timeline
├── pages/                      # Multi-page views
│   ├── 1_📊_Reports.py         # Session Report Generator
│   ├── 2_📜_Session_History.py # Historical Logs Browser
│   ├── 3_⚙️_Settings.py        # System & Threshold Settings
│   └── 4_ℹ️_About.py           # System Architecture
├── styles/
│   └── custom.css              # Dark Modern UI Theme CSS
└── utils/
    └── mock_data.py            # Standalone Mock Telemetry Provider
```

---

## 🔒 4. Zero Backend Modification Guarantee

The Streamlit dashboard foundation communicates via clean telemetry data dictionaries, ensuring that all backend AI engines (`detection/`, `analytics/`, `alerts/`, `camera/`, `logging/`) remain **100% untouched and protected**.
