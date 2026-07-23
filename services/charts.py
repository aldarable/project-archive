"""
services/charts.py — Reusable Plotly figure builders.

Keeping chart construction here (instead of inline in each page) avoids
duplicating layout/styling logic across chapters.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from config import THEME
from utils import hex_to_rgba

PLOTLY_TEMPLATE = "plotly_white"


def scurve_combined_chart(df: pd.DataFrame) -> go.Figure:
    """Chapter 1 — single combined chart: Plan % line, Actual % line, and
    Deviation (read directly from the sheet's DevPct_% column, never
    recomputed) as bars on a secondary y-axis.
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["Date"], y=df["PlanPct_%"], name="Plan Progress",
        line=dict(color=THEME["blue"], width=2),
        hovertemplate="Plan: %{y:.2f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df["Date"], y=df["ActualPct_%"], name="Actual Progress",
        line=dict(color=THEME["amber"], width=3),
        fill="tozeroy", fillcolor=hex_to_rgba(THEME["amber"], 0.12),
        hovertemplate="Actual: %{y:.2f}%<extra></extra>",
    ))

    dev = df["DevPct_%"]
    bar_colors = [THEME["green"] if (pd.notna(v) and v >= 0) else THEME["red"] for v in dev]
    fig.add_trace(go.Bar(
        x=df["Date"], y=dev, name="Deviation",
        marker=dict(color=bar_colors, opacity=0.55),
        yaxis="y2",
        hovertemplate="Deviation: %{y:+.2f}%<extra></extra>",
    ))

    milestones = df[df["Remarks"].fillna("") != ""]
    if not milestones.empty:
        fig.add_trace(go.Scatter(
            x=milestones["Date"], y=milestones["ActualPct_%"],
            mode="markers", name="Milestone",
            marker=dict(color=THEME["red"], size=9, line=dict(color=THEME["ink"], width=1)),
            text=milestones["Remarks"], hovertemplate="%{text}<extra></extra>",
        ))

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=460,
        yaxis=dict(title="Cumulative %", range=[0, 100], ticksuffix="%"),
        yaxis2=dict(title="Deviation (%)", overlaying="y", side="right", showgrid=False, zeroline=True),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=10, r=10, t=10, b=10),
        hovermode="x unified",
        barmode="relative",
    )
    return fig


def manpower_category_trend_chart(df: pd.DataFrame, categories: list[str], colors: dict, x_col: str = "date") -> go.Figure:
    fig = go.Figure()
    for c in categories:
        fig.add_trace(go.Scatter(
            x=df[x_col], y=df[c], mode="lines+markers", name=c,
            line=dict(color=colors.get(c, THEME["purple"]), width=2.5), marker=dict(size=6),
        ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=420,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        yaxis_title="Headcount",
        hovermode="x unified",
    )
    return fig


def single_line_trend_chart(df: pd.DataFrame, y_col: str, name: str, color: str, x_col: str = "date", fill: bool = True) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[x_col], y=df[y_col], mode="lines+markers", name=name,
        line=dict(color=color, width=3), marker=dict(size=7),
        fill="tozeroy" if fill else None,
        fillcolor=hex_to_rgba(color, 0.08) if fill else None,
    ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=320,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
        yaxis_title=name,
        hovermode="x unified",
    )
    return fig


def bar_by_category_chart(labels: list[str], values: list[float], color: str, horizontal: bool = False, title_y: str = "") -> go.Figure:
    fig = go.Figure()
    if horizontal:
        fig.add_trace(go.Bar(y=labels, x=values, orientation="h", marker=dict(color=color)))
        fig.update_layout(xaxis_title=title_y)
    else:
        fig.add_trace(go.Bar(x=labels, y=values, marker=dict(color=color)))
        fig.update_layout(yaxis_title=title_y)
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=380,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
    )
    return fig


def docon_summary_bar_chart(summary: dict) -> go.Figure:
    """Section 1 — one bar chart summarizing the overall document-control KPIs."""
    labels = list(summary.keys())
    values = list(summary.values())
    palette = [THEME["blue"], THEME["purple"], THEME["pink"], THEME["amber"],
               THEME["green"], THEME["red"]] * 3
    fig = go.Figure(go.Bar(x=labels, y=values, marker=dict(color=palette[: len(labels)])))
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=420,
        margin=dict(l=10, r=10, t=10, b=10),
        yaxis_title="Count",
        xaxis_tickangle=-20,
    )
    return fig
