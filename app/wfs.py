from functools import lru_cache

import numpy as np
import requests
from pointset import PointSet

from app.config import N_RANGE, WFS_BASE_REQUEST, WFS_EPSG, WFS_URL, logger
from app.edge import Edge
from app.gml import extract_lod1_coords


@lru_cache(maxsize=1024)
def edge_list_from_wfs(pos: PointSet, nrange: float = N_RANGE) -> list[Edge]:
    """
    Sends a request to the WFS server to retrieve the Level of Detail 1 (LOD1) CityGML data
    for the specified position.

    Args:
        pos (PointSet): The position to retrieve the data for.
        nrange (float, optional): The range around the position to retrieve the CityGML data for.
                                  Defaults to N_RANGE.

    Returns:
        list[Edge]: A list of Edge objects representing the retrieved CityGML data.

    Raises:
        requests.RequestException: If the WFS request fails.
    """
    pos.to_epsg(WFS_EPSG)
    logger.info(
        "Position in WFS EPSG: %.3f, %.3f, %.3f], EPSG: %i",
        pos.x,
        pos.y,
        pos.z,
        WFS_EPSG,
    )
    request_url = create_request(pos=pos, nrange=nrange)
    logger.debug("Sending request %s", request_url)
    response = requests.get(request_url, timeout=10)
    logger.debug("received answer. Status code: %s", response.status_code)

    if response.status_code != 200:
        raise requests.RequestException("WFS request failed!")

    return parse_response(response)


def create_request(pos: PointSet, nrange: float) -> str:
    """
    Creates a WFS request URL for the specified position and range.

    Args:
        pos (PointSet): The position to retrieve the data for.
        nrange (float): The range around the position to retrieve the CityGML data for.

    Returns:
        str: The WFS request URL.

    """
    bbox_bl = [pos.x - nrange, pos.y - nrange]
    bbox_tr = [pos.x + nrange, pos.y + nrange]
    bbox = f"BBOX={bbox_bl[0]},{bbox_bl[1]},{bbox_tr[0]},{bbox_tr[1]},urn:ogc:def:crs:EPSG::{WFS_EPSG}"
    return f"{WFS_URL}?{WFS_BASE_REQUEST}&{bbox}"


def parse_response(response: requests.Response) -> list[Edge]:
    """
    Parses the response from the WFS server and returns a list of edges representing
    the building roof footprints.

    Args:
        response (Response): The response object from the WFS server.

    Returns:
        list[Edge]: A list of edges representing the building roof footprints.
    """
    logger.debug("parsing response ...")
    building_coordinates: np.ndarray = np.array(extract_lod1_coords(str(response.content, encoding="utf-8")))

    return [Edge(start=edge_coord[:3], end=edge_coord[3:]) for edge_coord in building_coordinates]
