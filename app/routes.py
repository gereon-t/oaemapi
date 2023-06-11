from time import time
from typing import Any

import numpy as np
import plotly.graph_objects as go
from fastapi import Request, APIRouter

from fastapi.templating import Jinja2Templates
from app.config import VERSION, logger
from app.core.oaem import Oaem, compute_oaem

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


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
        f"Received API request for position [{pos_x:.3f}, {pos_y:.3f}, {pos_z:.3f}], EPSG: {epsg}"
    )

    query_time = time()
    oaem, within_area = compute_oaem(pos_x=pos_x, pos_y=pos_y, pos_z=pos_z, epsg=epsg)
    oaem_str = str(oaem.az_el_str)
    response_time = time()

    logger.info(f"Position cache info: {compute_oaem.cache_info()}")
    logger.info(
        f"Computed OAEM for position [{pos_x:.3f}, {pos_y:.3f}, {pos_z:.3f}], EPSG: {epsg} in {(response_time-query_time)*1000:.3f} ms"
    )
    logger.info(f"Position cache info: {compute_oaem.cache_info()}")

    return {"data": oaem_str, "within_area": within_area}


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
    oaem, within_area = compute_oaem(pos_x=pos_x, pos_y=pos_y, pos_z=pos_z, epsg=epsg)

    logger.info(f"Position cache info: {compute_oaem.cache_info()}")
    fig_json = create_json_fig(width, height, heading, oaem)

    return {"data": fig_json, "within_area": within_area}


def create_json_fig(
    width: int, height: int, heading: float, oaem: Oaem
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
    fig = go.Figure(
        data=go.Scatterpolar(
            theta=np.rad2deg(oaem.azimuth),
            r=np.rad2deg(np.pi / 2 - oaem.elevation),
            mode="lines",
            text="Obstruction Adaptive Elevation Mask",
        ),
        layout=go.Layout(
            polar=dict(
                angularaxis=dict(direction="clockwise", rotation=90 + heading),
                radialaxis=dict(
                    angle=90,
                    tickmode="array",
                    tickvals=[0, 15, 30, 45, 60, 75],
                    ticktext=["90°", "75°", "60°", "45°", "30°", "15°"],
                    tickangle=90,
                ),
            ),
            width=width,
            height=height,
            font=dict(size=30),
        ),
    )
    return fig.to_json()
