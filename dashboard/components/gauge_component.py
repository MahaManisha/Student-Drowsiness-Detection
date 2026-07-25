"""
Student Drowsiness Detection System - Circular Gauge Component

Renders a circular Plotly gauge chart for the Drowsiness Risk Score (0 - 100)
with dynamic arc color thresholds and smooth progress rendering.
"""

import plotly.graph_objects as go
from typing import Optional


def render_drowsiness_gauge(score: Optional[float]) -> go.Figure:
    """
    Renders a 2D Plotly circular gauge chart for drowsiness score (0-100).
    """
    if score is None:
        val = 0.0
        display_str = "N/A"
    else:
        val = min(100.0, max(0.0, float(score)))
        display_str = f"{val:.0f}"

    # Determine needle / bar color based on score value
    if val < 25:
        bar_color = "#10B981"  # Mint Green (Alert)
    elif val < 50:
        bar_color = "#F59E0B"  # Amber (Slightly Drowsy)
    elif val < 75:
        bar_color = "#F97316"  # Orange (Drowsy)
    else:
        bar_color = "#EF4444"  # Crimson Red (Critical)

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=val,
        number={'suffix': " / 100", 'font': {'size': 24, 'color': '#F9FAFB', 'family': 'JetBrains Mono'}},
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {
                'range': [0, 100],
                'tickwidth': 1,
                'tickcolor': "#4B5563",
                'tickvals': [0, 25, 50, 75, 100],
                'ticktext': ['0', '25', '50', '75', '100'],
                'tickfont': {'color': '#9CA3AF', 'size': 10}
            },
            'bar': {'color': bar_color, 'thickness': 0.25},
            'bgcolor': "#1F2937",
            'borderwidth': 1,
            'bordercolor': "rgba(255,255,255,0.08)",
            'steps': [
                {'range': [0, 25], 'color': 'rgba(16, 185, 129, 0.15)'},
                {'range': [25, 50], 'color': 'rgba(245, 158, 11, 0.15)'},
                {'range': [50, 75], 'color': 'rgba(249, 115, 22, 0.15)'},
                {'range': [75, 100], 'color': 'rgba(239, 68, 68, 0.20)'}
            ],
            'threshold': {
                'line': {'color': "#EF4444", 'width': 3},
                'thickness': 0.75,
                'value': 75
            }
        }
    ))

    fig.update_layout(
        margin=dict(l=15, r=15, t=15, b=15),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=140,
        font={'color': "#F9FAFB", 'family': "Inter"}
    )

    return fig
