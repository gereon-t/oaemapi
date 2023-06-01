import logging
from functools import lru_cache

import numpy as np
import requests
import xmltodict
from pointset import PointSet

from oaemapi.config import WFS_BASE_REQUEST, WFS_EPSG, WFS_URL
from oaemapi.util import interp_face

# logger configuration
logger = logging.getLogger("root")


@lru_cache(maxsize=256)
def request_wfs_lod1(pos: PointSet, nrange: float = 100) -> list:
    pos.to_epsg(WFS_EPSG)

    request_url = create_request(pos=pos, nrange=nrange)
    logger.debug(f"Sending request {request_url}")
    response = requests.get(request_url)
    logger.debug(f"received answer. Status code: {response.status_code}")

    if response.status_code != 200:
        raise requests.RequestException("WFS request failed!")

    logger.debug("parsing response ...")
    buildings: list = parse_gml(
        gml=xmltodict.parse(response.content),
    )
    logger.debug("done.")
    return buildings


def create_request(pos: PointSet, nrange: float) -> str:
    bbox_bl = [pos.x - nrange, pos.y - nrange]
    bbox_tr = [pos.x + nrange, pos.y + nrange]
    bbox = f"BBOX={bbox_bl[0]},{bbox_bl[1]},{bbox_tr[0]},{bbox_tr[1]},urn:ogc:def:crs:EPSG::{WFS_EPSG}"
    return f"{WFS_URL}?{WFS_BASE_REQUEST}&{bbox}"


def parse_lod1solid(lod1solid: dict) -> dict:
    surface_members = (
        lod1solid.get("gml:Solid", {})
        .get("gml:exterior", {})
        .get("gml:CompositeSurface", {})
        .get("gml:surfaceMember", {})
    )

    if not surface_members:
        return {}

    roof = surface_members[0]
    linear_ring_str: str = roof["gml:Polygon"]["gml:exterior"]["gml:LinearRing"]["gml:posList"]
    linear_ring_arr = np.array(linear_ring_str.split(" "), dtype=float)

    face_boundary = np.c_[linear_ring_arr[::3], linear_ring_arr[1::3], linear_ring_arr[2::3]]

    interp = interp_face(face_boundary)
    return {
        "boundary": face_boundary,
        "interp": interp,
    }


def parse_gml(gml: dict) -> list:
    """
    Converts the very nested gml dict to a more useful dict
    """

    bldg_list = []
    cityobject_members = gml.get("core:CityModel", {}).get("core:cityObjectMember", {})

    if len(cityobject_members) == 0:
        return bldg_list

    if not isinstance(cityobject_members, list):
        cityobject_members = [cityobject_members]

    for cobj in cityobject_members:
        bldg = cobj.get("bldg:Building", {})

        # single lod1Solid
        if lod1solid := bldg.get("bldg:lod1Solid", {}):
            if face := parse_lod1solid(lod1solid):
                bldg_list.append(face)

        # multiple lod1Solids
        if bldg_parts := bldg.get("bldg:consistsOfBuildingPart", {}):
            for bpart in bldg_parts:
                lod1solid = bpart.get("bldg:BuildingPart", {}).get("bldg:lod1Solid", {})
                if face := parse_lod1solid(lod1solid):
                    bldg_list.append(face)

    return bldg_list
