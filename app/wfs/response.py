import logging

import numpy as np
import xmltodict
from requests import Response

from app.config import FACE_INTERP_RES


# logger configuration
logger = logging.getLogger("root")


def lengths_from_xyz(xyz: np.ndarray) -> np.ndarray:
    """
    Returns trajectory lengths for given positions
    """
    xyz_1 = xyz[0:-1, :]
    xyz_2 = xyz[1:, :]

    diff = xyz_2 - xyz_1

    dists = np.linalg.norm(diff, axis=1)
    return np.r_[0, np.cumsum(dists)]


def interp_face(face_boundary):
    dists = lengths_from_xyz(face_boundary)
    grid = np.arange(0, np.sum(dists), FACE_INTERP_RES)

    x_interp = np.interp(grid, dists, face_boundary[:, 0])
    y_interp = np.interp(grid, dists, face_boundary[:, 1])
    z_interp = np.interp(grid, dists, face_boundary[:, 2])

    interp = np.c_[x_interp, y_interp, z_interp]
    return interp


def parse_response(response: Response) -> list:
    """
    Converts the very nested gml dict to a more useful dict
    """
    logger.debug("parsing response ...")
    gml = xmltodict.parse(response.content)

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

    logger.debug("parsing response ... done")
    return bldg_list


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
