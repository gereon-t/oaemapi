from datetime import datetime
from typing import Any

import numpy as np
import plotly.graph_objects as go

from app.oaem import Oaem
from app.suntrack import SunTrack


def create_json_fig(width: int, height: int, heading: float, oaem: Oaem, sun_track: SunTrack) -> str | None | Any:
    """
    Creates a Plotly scatterpolar figure of the Obstruction Adaptive Elevation Mask (OAEM) for a given position and EPSG code.

    Args:
        width (int): The width of the plot in pixels.
        height (int): The height of the plot in pixels.
        heading (float): The heading of the plot in degrees.
        oaem (Oaem): The OAEM object containing the azimuth and elevation data.

    Returns:
        str: A JSON string representation of the Plotly figure.
    """
    today_sun_track = sun_track.get_sun_track(date=datetime.now().astimezone(), daylight_only=True)

    fig = go.Figure()

    fig.add_trace(
        trace=go.Scatterpolar(
            theta=np.rad2deg(oaem.azimuth),
            r=np.rad2deg(np.pi / 2 - oaem.elevation),
            fill="toself",
            fillcolor="#96d0ff",
            name="Obstruction Adaptive Elevation Mask",
        ),
    )

    fig.add_trace(
        trace=go.Scatterpolar(
            theta=np.rad2deg(today_sun_track[:, 1]),
            r=np.rad2deg(np.pi / 2 - today_sun_track[:, 2]),
            name="Sun Trajectory",
            line_color="black",
        ),
    )
    current_sun_az, current_sun_el = sun_track.current_sunpos
    if current_sun_el > 0:
        fig.add_trace(
            trace=go.Scatterpolar(
                theta=[np.rad2deg(current_sun_az)],
                r=[np.rad2deg(np.pi / 2 - current_sun_el)],
                name="Sun Position",
                mode="markers",
                marker=dict(size=40, color="gold"),
            ),
        )

    fig.update_layout(
        polar=dict(
            angularaxis=dict(direction="clockwise", rotation=90 + heading),
            radialaxis=dict(
                angle=90,
                tickmode="array",
                tickvals=[0, 15, 30, 45, 60, 75],
                ticktext=["90°", "75°", "60°", "45°", "30°", "15°"],
                tickangle=90,
            ),
            bgcolor="#c2c2c2",
        ),
        width=width,
        height=height,
        font=dict(size=30),
        showlegend=False,
        paper_bgcolor="#e5ecf6",
        plot_bgcolor="#fff",
    )
    return fig.to_json()
