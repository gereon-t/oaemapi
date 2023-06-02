from functools import lru_cache

import requests
from pointset import PointSet

from app.config import WFS_BASE_REQUEST, WFS_EPSG, WFS_URL, logger


@lru_cache(maxsize=256)
def request_wfs_lod1(pos: PointSet, nrange: float = 100) -> requests.Response:
    pos.to_epsg(WFS_EPSG)

    request_url = create_request(pos=pos, nrange=nrange)
    logger.debug(f"Sending request {request_url}")
    response = requests.get(request_url)
    logger.debug(f"received answer. Status code: {response.status_code}")

    if response.status_code != 200:
        raise requests.RequestException("WFS request failed!")

    return response


def create_request(pos: PointSet, nrange: float) -> str:
    bbox_bl = [pos.x - nrange, pos.y - nrange]
    bbox_tr = [pos.x + nrange, pos.y + nrange]
    bbox = f"BBOX={bbox_bl[0]},{bbox_bl[1]},{bbox_tr[0]},{bbox_tr[1]},urn:ogc:def:crs:EPSG::{WFS_EPSG}"
    return f"{WFS_URL}?{WFS_BASE_REQUEST}&{bbox}"
