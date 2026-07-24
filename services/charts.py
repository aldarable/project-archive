"""
services/charts.py for Plotly figure builders.

"""

from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go
from config import COLORS

GRID = COLORS["grid"]
TEXT = COLORS["text"]

_BASE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=TEXT, size=13),
    margin=dict(l=10, r=10, t=10, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=12)),
    hovermode="x unified",
)

_AXIS = dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, tickfont=dict(color=TEXT))


def _rgba(hex_color: str, alpha: float) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"



# Chapter 1 — S-Curve
def scurve_plan_actual_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["Date"], y=df["PlanCumPct_%"], name="Plan Progress",
        mode="lines", line=dict(color=COLORS["plan"], width=2.5),
        hovertemplate="Plan: %{y:.2f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df["Date"], y=df["ActualCumPct_%"], name="Actual Progress",
        mode="lines", line=dict(color=COLORS["actual"], width=3),
        fill="tozeroy", fillcolor=_rgba(COLORS["actual"], 0.15),
        hovertemplate="Actual: %{y:.2f}%<extra></extra>",
    ))

    milestones = df[(df["Remarks"].fillna("") != "") & df["ActualCumPct_%"].notna()]
    if not milestones.empty:
        fig.add_trace(go.Scatter(
            x=milestones["Date"], y=milestones["ActualCumPct_%"],
            mode="markers", name="Milestone",
            marker=dict(color=COLORS["actual"], size=8, line=dict(color=COLORS["deviation"], width=1.5)),
            text=milestones["Remarks"], hovertemplate="%{text}<extra></extra>",
        ))

    fig.update_layout(
        **_BASE_LAYOUT,
        height=340,
        yaxis=dict(title="Cumulative %", range=[0, 100], ticksuffix="%", **_AXIS),
        xaxis=dict(**_AXIS),
    )
    return fig


def scurve_combined_chart(df: pd.DataFrame, plan_col: str = "PlanPct_%", actual_col: str = "ActualPct_%",
                           dev_col: str = "DeviationPctAbs") -> go.Figure:
    """Single chart, single shared axis: Plan, Actual, and Deviation
    (plotted as a positive magnitude — |Actual - Plan| — by design, not a
    signed value) + Milestone markers from Remarks. Matches the combined
    'S-Curve — Plan vs Actual vs Deviation' view."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["Date"], y=df[plan_col], name="Plan Progress",
        mode="lines", line=dict(color=COLORS["plan"], width=2.5),
        hovertemplate="Plan: %{y:.2f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df["Date"], y=df[actual_col], name="Actual Progress",
        mode="lines", line=dict(color=COLORS["actual"], width=3),
        fill="tozeroy", fillcolor=_rgba(COLORS["actual"], 0.15),
        hovertemplate="Actual: %{y:.2f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df["Date"], y=df[dev_col], name="Deviation",
        mode="lines", line=dict(color=COLORS["deviation"], width=2),
        hovertemplate="Deviation: %{y:.2f}%<extra></extra>",
    ))

    remarks_col = "Remarks" if "Remarks" in df.columns else None
    if remarks_col:
        milestones = df[(df[remarks_col].fillna("") != "") & df[actual_col].notna()]
        if not milestones.empty:
            fig.add_trace(go.Scatter(
                x=milestones["Date"], y=milestones[actual_col],
                mode="markers", name="Milestone",
                marker=dict(color=COLORS["actual"], size=9, line=dict(color=COLORS["deviation"], width=1.5)),
                text=milestones[remarks_col], hovertemplate="%{text}<extra></extra>",
            ))

    fig.update_layout(
        **_BASE_LAYOUT,
        height=380,
        yaxis=dict(title="Percentage (%)", range=[0, 100], ticksuffix="%", **_AXIS),
        xaxis=dict(**_AXIS),
    )
    return fig


def sumaraja_scurve_chart(df: pd.DataFrame) -> go.Figure:
    """Matches the vendor's original Excel S-Curve: weekly Plan/Actual as
    grouped columns plus Cumulative Plan/Actual as lines on top, all on the
    same 0-100% axis."""
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df["WeekStart"], y=df["PlanWeeklyPct"], name="Plan",
        marker=dict(color=COLORS["actual"]),
        hovertemplate="Plan (week): %{y:.3f}%<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=df["WeekStart"], y=df["ActualWeeklyPct"], name="Actual",
        marker=dict(color=COLORS["on_track"]),
        hovertemplate="Actual (week): %{y:.3f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df["WeekStart"], y=df["PlanCumPct"], name="Cummulative Plan",
        mode="lines+markers", line=dict(color=COLORS["actual"], width=2.5),
        marker=dict(size=6, color=COLORS["actual"]),
        hovertemplate="Cumulative Plan: %{y:.2f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df["WeekStart"], y=df["ActualCumPct"], name="Cummulative Actual",
        mode="lines+markers", line=dict(color=COLORS["on_track"], width=3),
        marker=dict(size=6, color=COLORS["on_track"]),
        hovertemplate="Cumulative Actual: %{y:.2f}%<extra></extra>",
    ))

    fig.update_layout(
        **_BASE_LAYOUT,
        height=380,
        barmode="group",
        yaxis=dict(title="Cumulative %", range=[0, 100], ticksuffix="%", **_AXIS),
        xaxis=dict(title="Week", **_AXIS),
    )
    return fig


def scurve_deviation_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Date"], y=df["DeviationPct"], name="Deviation",
        mode="lines", line=dict(color=COLORS["deviation"], width=2),
        fill="tozeroy", fillcolor=_rgba(COLORS["deviation"], 0.18),
        hovertemplate="Deviation: %{y:+.2f}%<extra></extra>",
    ))
    fig.update_layout(
        **_BASE_LAYOUT,
        height=180,
        showlegend=False,
        yaxis=dict(title="Deviation (%)", ticksuffix="%", **_AXIS),
        xaxis=dict(**_AXIS),
    )
    return fig


def workbreakdown_bar(df: pd.DataFrame) -> go.Figure:
    d = df.iloc[::-1]  # first package on top
    colors = [COLORS["actual"] if v > 0 else COLORS["grid"] for v in d["ActualPct"]]
    fig = go.Figure(go.Bar(
        x=d["ActualPct"], y=d["Package"], orientation="h",
        marker=dict(color=colors),
        customdata=d["LoadPct"],
        hovertemplate="%{y}<br>Complete: %{x:.1f}% of package scope<br>Package weight: %{customdata:.1f}% of total project<extra></extra>",
    ))
    fig.update_layout(
        **_BASE_LAYOUT,
        height=max(320, 32 * len(d)),
        showlegend=False,
        xaxis=dict(title="% of package scope complete", range=[0, 100], ticksuffix="%", **_AXIS),
        yaxis=dict(**_AXIS),
    )
    return fig



# Chapter 2 — HSE Manpower
def category_trend_chart(df: pd.DataFrame, categories: list[str], colors: dict, height: int = 320) -> go.Figure:
    fig = go.Figure()
    for c in categories:
        fig.add_trace(go.Scatter(
            x=df["date"], y=df[c], name=c, mode="lines+markers",
            line=dict(color=colors.get(c, COLORS["purple"]), width=2.5), marker=dict(size=5),
        ))
    fig.update_layout(
        **_BASE_LAYOUT,
        height=height,
        yaxis=dict(title="Headcount", **_AXIS),
        xaxis=dict(**_AXIS),
    )
    return fig


def single_line_chart(df: pd.DataFrame, y_col: str, color: str, height: int = 280) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df[y_col], mode="lines+markers", name=y_col,
        line=dict(color=color, width=2.5), marker=dict(size=5),
        fill="tozeroy", fillcolor=_rgba(color, 0.10),
    ))
    fig.update_layout(
        **_BASE_LAYOUT,
        height=height,
        showlegend=False,
        yaxis=dict(**_AXIS),
        xaxis=dict(**_AXIS),
    )
    return fig



# Chapter 3 — Document Control
def docon_grouped_bar(vendors: list[str], series: dict[str, list[float]], colors: list[str], height: int = 420) -> go.Figure:
    fig = go.Figure()
    for i, (label, values) in enumerate(series.items()):
        fig.add_trace(go.Bar(x=vendors, y=values, name=label, marker=dict(color=colors[i % len(colors)])))
    layout = dict(_BASE_LAYOUT)
    layout["legend"] = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=11))
    fig.update_layout(
        **layout,
        height=height,
        barmode="group",
        yaxis=dict(title="Count", **_AXIS),
        xaxis=dict(**_AXIS),
    )
    return fig
