import plotly.graph_objects as go


def apply(fig):
    fig.update_layout(
        template="plotly_white",
        margin=dict(
            l=15,
            r=15,
            t=20,
            b=15
        ),

        legend=dict(
            orientation="h",
            y=1.08
        ),

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified"
    )

    return fig
