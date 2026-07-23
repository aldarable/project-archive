import plotly.graph_objects as go
from utils.colors import *
from components.chart_theme import apply

def scurve(df):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["Plan"],
            mode="lines",
            name="Plan",
            line=dict(
                color=PLAN,
                width=4
            )
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["Actual"],
            mode="lines+markers",
            name="Actual",
            line=dict(
                color=ACTUAL,
                width=4
            ),
            marker=dict(
                size=6
            )
        )
    )

    fig = apply(fig)

    fig.update_yaxes(
        ticksuffix="%"
    )

    return fig
