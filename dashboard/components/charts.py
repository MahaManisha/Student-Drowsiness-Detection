"""
Student Drowsiness Detection System - Plotly Charts Component

Renders 5 interactive Plotly charts for session analytics:
  1. EAR Trend Chart (Time vs EAR)
  2. MAR Trend Chart (Time vs MAR)
  3. Drowsiness Score Trend Chart (Time vs Score)
  4. Blink Frequency Bar Chart
  5. Alert Distribution Pie Chart
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional, List, Dict, Any


def get_dark_layout(title: str, height: int = 220) -> Dict[str, Any]:
    """Returns standardized dark mode layout parameters for Plotly figures."""
    return dict(
        title=dict(text=title, font=dict(color="#F9FAFB", size=13, family="Inter")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        margin=dict(l=30, r=20, t=35, b=30),
        xaxis=dict(showgrid=True, gridcolor="#2D3748", zeroline=False, tickfont=dict(color="#9CA3AF", size=10)),
        yaxis=dict(showgrid=True, gridcolor="#2D3748", zeroline=False, tickfont=dict(color="#9CA3AF", size=10)),
        legend=dict(font=dict(color="#F9FAFB", size=10))
    )


def render_ear_trend_chart(history_df: Optional[pd.DataFrame]) -> go.Figure:
    """Renders EAR Trend Smooth Line Chart with Threshold Line."""
    fig = go.Figure()

    if history_df is not None and not history_df.empty and "ear" in history_df.columns:
        fig.add_trace(go.Scatter(
            x=history_df["timestamp"],
            y=history_df["ear"],
            mode="lines",
            name="EAR",
            line=dict(color="#10B981", width=2, shape="spline"),
            hovertemplate="Time: %{x}<br>EAR: %{y:.3f}<extra></extra>"
        ))
        # Threshold Reference Line at 0.21
        fig.add_hline(y=0.21, line_dash="dash", line_color="#EF4444", annotation_text="Threshold (0.21)", annotation_font_color="#EF4444")
    else:
        fig.add_annotation(text="Not enough session data yet.", showarrow=False, font=dict(color="#9CA3AF", size=12))

    fig.update_layout(**get_dark_layout("👁️ Eye Aspect Ratio (EAR) Trend Over Time"))
    return fig


def render_mar_trend_chart(history_df: Optional[pd.DataFrame]) -> go.Figure:
    """Renders MAR Trend Smooth Line Chart with Threshold Line."""
    fig = go.Figure()

    if history_df is not None and not history_df.empty and "mar" in history_df.columns:
        fig.add_trace(go.Scatter(
            x=history_df["timestamp"],
            y=history_df["mar"],
            mode="lines",
            name="MAR",
            line=dict(color="#EC4899", width=2, shape="spline"),
            hovertemplate="Time: %{x}<br>MAR: %{y:.3f}<extra></extra>"
        ))
        # Threshold Reference Line at 0.55
        fig.add_hline(y=0.55, line_dash="dash", line_color="#F59E0B", annotation_text="Threshold (0.55)", annotation_font_color="#F59E0B")
    else:
        fig.add_annotation(text="Not enough session data yet.", showarrow=False, font=dict(color="#9CA3AF", size=12))

    fig.update_layout(**get_dark_layout("👄 Mouth Aspect Ratio (MAR) Trend Over Time"))
    return fig


def render_score_trend_chart(history_df: Optional[pd.DataFrame]) -> go.Figure:
    """Renders Drowsiness Risk Score Trend Chart."""
    fig = go.Figure()

    if history_df is not None and not history_df.empty and "score" in history_df.columns:
        fig.add_trace(go.Scatter(
            x=history_df["timestamp"],
            y=history_df["score"],
            mode="lines",
            name="Risk Score",
            line=dict(color="#38BDF8", width=2, shape="spline"),
            fill="tozeroy",
            fillcolor="rgba(56, 189, 248, 0.15)",
            hovertemplate="Time: %{x}<br>Score: %{y:.0f}/100<extra></extra>"
        ))
    else:
        fig.add_annotation(text="Not enough session data yet.", showarrow=False, font=dict(color="#9CA3AF", size=12))

    fig.update_layout(**get_dark_layout("🧠 Drowsiness Risk Score Progression"))
    return fig


def render_blink_frequency_chart(history_df: Optional[pd.DataFrame]) -> go.Figure:
    """Renders Blink Frequency Bar Chart."""
    fig = go.Figure()

    if history_df is not None and not history_df.empty and "blinks" in history_df.columns:
        # Resample or group by interval
        df_bars = history_df.tail(20)
        fig.add_trace(go.Bar(
            x=df_bars["timestamp"],
            y=df_bars["blinks"],
            name="Blink Count",
            marker_color="#10B981"
        ))
    else:
        fig.add_annotation(text="Not enough session data yet.", showarrow=False, font=dict(color="#9CA3AF", size=12))

    fig.update_layout(**get_dark_layout("⚡ Blink Frequency Stream", height=200))
    return fig


def render_alert_distribution_chart(history_df: Optional[pd.DataFrame]) -> go.Figure:
    """Renders Alert State Distribution Pie Chart."""
    fig = go.Figure()

    if history_df is not None and not history_df.empty and "state" in history_df.columns:
        counts = history_df["state"].value_counts().to_dict()
        labels = list(counts.keys())
        values = list(counts.values())
        colors = ["#10B981", "#F59E0B", "#F97316", "#EF4444"]

        fig.add_trace(go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker=dict(colors=colors, line=dict(color="#1F2937", width=2)),
            textinfo="percent+label",
            textfont=dict(color="#F9FAFB", size=10)
        ))
    else:
        # Default distribution simulation
        labels = ["Normal (ALERT)", "Slightly Drowsy", "Drowsy", "Highly Drowsy"]
        values = [85, 10, 4, 1]
        colors = ["#10B981", "#F59E0B", "#F97316", "#EF4444"]
        fig.add_trace(go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker=dict(colors=colors, line=dict(color="#1F2937", width=2)),
            textinfo="percent+label",
            textfont=dict(color="#F9FAFB", size=10)
        ))

    fig.update_layout(
        title=dict(text="📊 Alert State Distribution", font=dict(color="#F9FAFB", size=13, family="Inter")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=200,
        margin=dict(l=10, r=10, t=35, b=10),
        showlegend=False
    )
    return fig
