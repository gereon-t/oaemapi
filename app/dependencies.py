import numpy as np
from app.edge import Edge, csv2edges
from app.geoid import Geoid
from app.config import GEOID_FILE, GEOID_EPSG, EDGE_FILE, EDGE_SOURCE

from pointset import PointSet

from app.wfs import edge_list_from_wfs

geoid = Geoid(filename=GEOID_FILE, epsg=GEOID_EPSG)

if EDGE_SOURCE == "FILE":
    EDGES = csv2edges(EDGE_FILE)


async def get_edge_list(
    pos_x: float, pos_y: float, pos_z: float, epsg: int
) -> list[Edge]:
    if EDGE_SOURCE == "WFS":
        return edge_list_from_wfs(
            pos=PointSet(np.array([pos_x, pos_y, pos_z]), epsg=epsg)
        )

    if EDGE_SOURCE == "FILE":
        return


async def get_geoid(pos_x: float, pos_y: float, pos_z: float, epsg: int) -> float:
    pos = PointSet(np.array([pos_x, pos_y, pos_z]), epsg=epsg)
    return geoid.interpolate(pos)
