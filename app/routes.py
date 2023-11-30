from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

from app.config import FAVICON_PATH, VERSION
from app.oaem import Oaem, compute_oaem
from app.plotting import create_json_fig
from app.suntrack import SunTrack

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Favicon endpoint."""
    return FileResponse(FAVICON_PATH)


@router.get("/", include_in_schema=False)
async def index(request: Request):
    """Root endpoint."""
    return templates.TemplateResponse("index.html", {"request": request, "version": VERSION})


@router.get("/privacy_policy", include_in_schema=False)
async def privacy_policy(request: Request):
    """Privacy policy endpoint."""
    return templates.TemplateResponse("privacy_policy.html", {"request": request})


@router.get("/oaem")
async def request_oaem(oaem: Annotated[Oaem, Depends(compute_oaem)]) -> dict:
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
    """
    return {"data": oaem.az_el_str}


@router.get("/sunvis")
async def request_sun_visibility(
    oaem: Annotated[Oaem, Depends(compute_oaem)], sun_track: Annotated[SunTrack, Depends()]
) -> dict:
    """
    Derives the sun visibility for a given position using the Obstruction Adaptive Elevation Mask (OAEM).

    The trajectory of the sun is intersected with the OAEM to determine the sun visibility for the given position.
    The sun visibility is given as a boolean value, which is true if the sun is visible and false otherwise.
    Furthermore, the time interval for the current sun visibility is given.

    Args:

            pos_x (float): The x-coordinate of the position.
            pos_y (float): The y-coordinate of the position.
            pos_z (float): The z-coordinate of the position.
            epsg (int): The EPSG code of the position.

    Returns:

            A JSON object with:

                - visible (str): The sun visibility as a boolean value.
                - since (str): The start time of the current sun visibility interval.
                - until (str): The end time of the current sun visibility interval.
    """
    sun_track.intersect_with_oaem(oaem)
    sun_az, sun_el = sun_track.current_sunpos
    sun_visible = sun_el > oaem.query(sun_az)

    return {
        "visible": str(sun_visible),
        "since": str(sun_track.since),
        "until": str(sun_track.until),
    }


@router.get("/plot")
async def plot_oaem(
    oaem: Annotated[Oaem, Depends(compute_oaem)],
    sun_track: Annotated[SunTrack, Depends()],
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
    sun_track.intersect_with_oaem(oaem)
    sun_az, sun_el = sun_track.current_sunpos
    sun_visible = sun_el > oaem.query(sun_az)

    fig_json = create_json_fig(width, height, heading, oaem, sun_track)

    return {
        "data": fig_json,
        "visible": str(sun_visible),
        "since": str(sun_track.since),
        "until": str(sun_track.until),
    }
