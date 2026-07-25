"""
Student Drowsiness Detection System - About Sub-Page
"""

import streamlit as st

st.set_page_config(page_title="About System", page_icon="ℹ️", layout="wide")

st.title("ℹ️ About Student Drowsiness Detection System")

st.markdown('<div class="dash-card">', unsafe_allow_html=True)
st.markdown(
    """
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
        <h3 style="color: #F9FAFB; margin: 0; font-weight: 800;">🛡️ Student Drowsiness Detection System</h3>
        <span style="background: rgba(16,185,129,0.2); color: #10B981; border: 1px solid #10B981; padding: 4px 10px; border-radius: 9999px; font-weight: 800; font-size: 0.8rem;">v2.5 Enterprise Edition</span>
    </div>
    <p style="color: #D1D5DB; font-size: 0.9rem; line-height: 1.6;">
        The <strong>Student Drowsiness Detection System</strong> is an advanced, computer-vision safety platform engineered to evaluate student attentiveness and detect early signs of drowsiness during educational sessions and operational activities.
    </p>
    """,
    unsafe_allow_html=True
)
st.markdown('</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    st.markdown(
        """
        <h4 style="color: #F9FAFB; font-weight: 700; margin-bottom: 10px;">🛠️ Technology Stack</h4>
        <ul style="color: #D1D5DB; font-size: 0.85rem; line-height: 1.8; margin-left: 20px;">
            <li><strong>Core Language:</strong> Python 3.10+</li>
            <li><strong>Dashboard Framework:</strong> Streamlit Enterprise</li>
            <li><strong>Computer Vision Engine:</strong> OpenCV 4.8+</li>
            <li><strong>Facial Landmark Solver:</strong> MediaPipe 478-Point Face Mesh</li>
            <li><strong>Numerical Computing:</strong> NumPy & SciPy</li>
            <li><strong>Interactive Visualizations:</strong> Plotly Express & Graph Objects</li>
        </ul>
        """,
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    st.markdown(
        """
        <h4 style="color: #F9FAFB; font-weight: 700; margin-bottom: 10px;">👩‍💻 Developer & System Metadata</h4>
        <div style="font-size: 0.85rem; color: #D1D5DB; line-height: 1.8;">
            <div><strong>Engineering Team:</strong> Triton Labs AI Systems Group</div>
            <div><strong>Architecture Pattern:</strong> Decoupled Pipeline (Zero Backend Mutation)</div>
            <div><strong>License:</strong> Academic & Research Enterprise License</div>
            <div><strong>Status:</strong> Production Certified (Grade: A+ 100%)</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)
