from datetime import datetime
from time import time
from typing import Any

import numpy as np
import plotly.graph_objects as go
from fastapi import APIRouter, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

from app.config import FAVICON_PATH, VERSION, logger
from app.dependencies import edge_provider, geoid
from app.oaem import Oaem, compute_oaem
from app.suntrack import SunTrack

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(FAVICON_PATH)


@router.get("/", include_in_schema=False)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "version": VERSION}
    )


@router.get("/privacy_policy", include_in_schema=False)
async def privacy_policy(request: Request):
    return templates.TemplateResponse("privacy_policy.html", {"request": request})


@router.get("/api")
async def oaem_request(pos_x: float, pos_y: float, pos_z: float, epsg: int) -> dict:
    """
    Computes the Obstruction Adaptive Elevation Mask (OAEM) for a given position and EPSG code.

    This API endpoint calculates the OAEM, which represents the obstruction of the sky view due to
    buildings using elevation angles. The OAEM is given with an azimuth resolution of 1 degree.

    Note: The OAEM data provided by this API is currently available only for the state of North Rhine-Westphalia (NRW), Germany.
    If the provided position is outside the area of operation, an empty OAEM is returned.

    Args:

        pos_x (float): The x-coordinate of the position.
        pos_y (float): The y-coordinate of the position.
        pos_z (float): The z-coordinate of the position.
        epsg (int): The EPSG code specifying the coordinate reference system (CRS) of the provided position.

    Returns:

        A JSON object with:

            - data (str): The OAEM data represented as a string in azimuth:elevation format.
                          If the position is outside the area of operation, the OAEM will be empty.
                          Azimuth and elevation are given in radians.
            - within_area (bool): A boolean indicating whether the provided position is within the area of operation.
    """
    logger.info(
        "Received API request for position [%.3f, %.3f, %.3f], EPSG: %i",
        pos_x,
        pos_y,
        pos_z,
        epsg,
    )

    oaem = compute_oaem(geoid, edge_provider, pos_x, pos_y, pos_z, epsg)

    return {"data": oaem.az_el_str}


@router.get("/sunvis")
async def sunvis(pos_x: float, pos_y: float, pos_z: float, epsg: int) -> dict:
    query_time = time()
    oaem = compute_oaem(geoid, edge_provider, pos_x, pos_y, pos_z, epsg)
    sun_track = SunTrack(pos=oaem.pos)
    sun_track.intersect_with_oaem(oaem)
    sun_az, sun_el = sun_track.current_sunpos
    sun_visible = sun_el > oaem.query(sun_az)
    response_time = time()

    logger.info(
        "Computed sun visibility for position [%.3f, %.3f, %.3f], EPSG: %i in %.3f} ms",
        pos_x,
        pos_y,
        pos_z,
        epsg,
        (response_time - query_time) * 1000,
    )

    return {
        "visible": str(sun_visible),
        "since": str(sun_track.since),
        "until": str(sun_track.until),
    }


@router.get("/plot")
async def plot(
    pos_x: float,
    pos_y: float,
    pos_z: float,
    epsg: int,
    width: int = 600,
    height: int = 600,
    heading: float = 0.0,
):
    """
    Computes the Obstruction Adaptive Elevation Mask (OAEM) for a given position and EPSG code, and returns a plot of the OAEM.

    Due to the unavailability of data for other federal states, the OAEM is currently only available for
    the state of North Rhine-Westphalia (NRW), Germany.

    Args:

        pos_x (float): The x-coordinate of the position.
        pos_y (float): The y-coordinate of the position.
        pos_z (float): The z-coordinate of the position.
        epsg (int): The EPSG code of the position.
        width (int, optional): The width of the plot in pixels. Defaults to 600.
        height (int, optional): The height of the plot in pixels. Defaults to 600.
        heading (float, optional): The heading of the plot in degrees. Defaults to 0.0.

    Returns:

        A JSON string representation of the Plotly figure.
    """
    oaem = compute_oaem(geoid, edge_provider, pos_x, pos_y, pos_z, epsg)
    sun_track = SunTrack(pos=oaem.pos)
    sun_track.intersect_with_oaem(oaem)
    sun_az, sun_el = sun_track.current_sunpos
    sun_visible = sun_el > oaem.query(sun_az)

    fig_json = create_json_fig(width, height, heading, oaem, sun_track)

    return {
        "data": fig_json,
        "within_area": True,
        "visible": str(sun_visible),
        "since": str(sun_track.since),
        "until": str(sun_track.until),
    }


def create_json_fig(
    width: int, height: int, heading: float, oaem: Oaem, sun_track: SunTrack
) -> str | None | Any:
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
    today_sun_track = sun_track.get_sun_track(
        date=datetime.now().astimezone(), daylight_only=True
    )
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
