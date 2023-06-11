from functools import lru_cache
import requests
from pointset import PointSet

from app.config import N_RANGE, WFS_BASE_REQUEST, WFS_EPSG, WFS_URL, logger
from app.core.edge import Edge

import numpy as np
import xmltodict


@lru_cache(maxsize=1024)
def request_wfs_lod1(pos: PointSet, nrange: float = N_RANGE) -> list[Edge]:
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
    logger.info(f"Position in WFS EPSG: [{pos.x:.3f}, {pos.y:.3f}, {pos.z:.3f}], EPSG: {WFS_EPSG}")
    request_url = create_request(pos=pos, nrange=nrange)
    logger.debug(f"Sending request {request_url}")
    response = requests.get(request_url)
    logger.debug(f"received answer. Status code: {response.status_code}")

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
    gml = xmltodict.parse(response.content)

    edge_list = []
    cityobject_members = gml.get("core:CityModel", {}).get("core:cityObjectMember", {})

    if len(cityobject_members) == 0:
        return edge_list

    if not isinstance(cityobject_members, list):
        cityobject_members = [cityobject_members]

    for cobj in cityobject_members:
        bldg = cobj.get("bldg:Building", {})

        # single lod1Solid
        if lod1solid := bldg.get("bldg:lod1Solid", {}):
            if (face := parse_lod1solid(lod1solid)) is not None:
                edge_list.extend(Edge(start=face[i], end=face[i + 1]) for i in range(len(face) - 1))

        # multiple lod1Solids
        if bldg_parts := bldg.get("bldg:consistsOfBuildingPart", {}):
            for bpart in bldg_parts:
                lod1solid = bpart.get("bldg:BuildingPart", {}).get("bldg:lod1Solid", {})
                if (face := parse_lod1solid(lod1solid)) is not None:
                    edge_list.extend(Edge(start=face[i], end=face[i + 1]) for i in range(len(face) - 1))

    logger.debug("parsing response ... done")
    return edge_list


def parse_lod1solid(lod1solid: dict) -> np.ndarray | None:
    """
    Parses the lod1Solid element of a building and returns a numpy array of vertices
    representing the roof footprint.

    Args:
        lod1solid (dict): The lod1Solid element of a building.

    Returns:
        np.ndarray | None: A numpy array of vertices representing the roof footprint,
        or None if the lod1Solid element is empty.
    """
    surface_members = (
        lod1solid.get("gml:Solid", {})
        .get("gml:exterior", {})
        .get("gml:CompositeSurface", {})
        .get("gml:surfaceMember", {})
    )

    if not surface_members:
        return None

    roof = surface_members[0]
    linear_ring_str: str = roof["gml:Polygon"]["gml:exterior"]["gml:LinearRing"]["gml:posList"]
    linear_ring_arr = np.array(linear_ring_str.split(" "), dtype=float)

    return np.c_[linear_ring_arr[::3], linear_ring_arr[1::3], linear_ring_arr[2::3]]
