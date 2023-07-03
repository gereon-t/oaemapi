import time
from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np
from intervaltree import Interval, IntervalTree
from pointset import PointSet

from app.config import WFS_EPSG, GEOID_RES, N_RES, OAEM_RES, logger
from app.core.edge import Edge
from app.core.wfs import request_wfs_lod1
from app.data import geoid, area_of_operation
from shapely.geometry import Point


@dataclass
class Oaem:
    """
    Represents an Obstruction Adaptive Elevation Model (OAEM) that stores the elevation data for a given position in space.
    The OAEM is computed from a set of edges that define the building roof footprints.
    """

    pos: PointSet
    azimuth: np.ndarray = field(
        default_factory=lambda: np.arange(0, 2 * np.pi, OAEM_RES)
    )
    elevation: np.ndarray = field(
        default_factory=lambda: np.zeros_like(np.arange(0, 2 * np.pi, OAEM_RES))
    )

    @property
    def az_el_str(self) -> str:
        return "".join(
            f"{az:.3f}:{el:.3f}," for az, el in zip(self.azimuth, self.elevation)
        )

    def interpolate(self, azimuths: list[float] or np.ndarray) -> "Oaem":
        interp_elevation = np.interp(azimuths, self.azimuth, self.elevation)
        return Oaem(pos=self.pos.copy(), azimuth=azimuths, elevation=interp_elevation)


@lru_cache(maxsize=16384)
def compute_oaem(
    pos_x: float, pos_y: float, pos_z: float, epsg: int
) -> tuple[Oaem, bool]:
    """
    Computes an Obstruction Adaptive Elevation Model (OAEM) for a given position in space.

    Args:
        pos_x (float): The x-coordinate of the position in the specified EPSG.
        pos_y (float): The y-coordinate of the position in the specified EPSG.
        pos_z (float): The z-coordinate of the position in the specified EPSG.
        epsg (int): The EPSG code of the position.

    Returns:
        Oaem: An Obstruction Adaptive Elevation Model (OAEM) that stores the elevation data for the given position in space.
        bool: True if the position is inside the area of operation, False otherwise.
    """
    pos = PointSet(
        xyz=np.array([pos_x, pos_y, pos_z]), epsg=epsg, init_local_transformer=False
    ).to_epsg(WFS_EPSG)

    if (
        area_of_operation is not None
        and not area_of_operation.geometry.contains(Point(pos.x, pos.y))[0]
    ):
        logger.warning(
            f"Position [{pos.x:.3f}, {pos.y:.3f}, {pos.z:.3f}] is outside the area of operation."
        )
        return Oaem(), False

    pos.z -= geoid.interpolate(pos=pos.round_to(GEOID_RES))
    logger.info(
        f"Position in APP EPSG (orthometric): [{pos.x:.3f}, {pos.y:.3f}, {pos.z:.3f}], EPSG: {pos.epsg}"
    )
    logger.info(f"Geoid cache info: {geoid.interpolate.cache_info()}")

    edge_list = request_wfs_lod1(pos=pos.round_to(N_RES))
    logger.info(f"Neighborhood cache info: {request_wfs_lod1.cache_info()}")
    return oaem_from_edge_list(edge_list=edge_list, pos=pos), True


def oaem_from_edge_list(edge_list: list[Edge], pos: PointSet) -> Oaem:
    """
    Computes an Obstruction Adaptive Elevation Model (OAEM) for a given position in space from a list of edges that define
    the building roof footprints.

    Args:
        edge_list (list[Edge]): A list of edges that define the building roof footprints.
        pos (PointSet): The position in space.

    Returns:
        Oaem: An Obstruction Adaptive Elevation Model (OAEM) that stores the elevation data for the given position in space.
    """
    if not edge_list:
        return Oaem()
    interval_tree = build_interval_tree(edge_list=edge_list, pos=pos.xyz.ravel())
    oaem_grid = np.arange(-np.pi, np.pi, OAEM_RES)
    oaem_temp = np.zeros((len(oaem_grid) + 1, 2), dtype=np.float64)

    for i, az in enumerate(oaem_grid):
        overlaps: set[Interval] = interval_tree[az]
        oaem_temp[i, 0] = az
        oaem_temp[i, 1] = max(
            0,
            max(
                (edge_list[overlap.data].get_elevation(az) for overlap in overlaps),
                default=0,
            ),
        )
    oaem_temp[-1, :] = oaem_temp[0, :]
    return Oaem(pos=pos, azimuth=oaem_temp[:, 0], elevation=oaem_temp[:, 1])


def build_interval_tree(edge_list: list[Edge], pos: np.ndarray) -> IntervalTree:
    """
    Builds an interval tree from a list of edges that define the building roof footprints and a position in space.

    Args:
        edge_list (list[Edge]): A list of edges that define the building roof footprints.
        pos (np.ndarray): The position in space as a numpy array of shape (3,) in the format (x, y, z).

    Returns:
        IntervalTree: An interval tree that stores the intervals of azimuth angles that intersect with the edges.
    """

    def add_to_interval_tree(
        interval_tree: IntervalTree, start: float, end: float, data: float
    ) -> None:
        if start == end:
            return
        interval_tree.addi(start, end, data)

    interval_tree = IntervalTree()
    start_time = time.time()
    for i, edge in enumerate(edge_list):
        edge.set_position(pos=pos)
        az_1 = np.arctan2(edge.start[0] - pos[0], edge.start[1] - pos[1])
        az_2 = np.arctan2(edge.end[0] - pos[0], edge.end[1] - pos[1])
        if np.sign(az_1) != np.sign(az_2) and np.abs(az_1 - az_2) > np.pi:
            add_to_interval_tree(
                interval_tree=interval_tree, start=-np.pi, end=min(az_1, az_2), data=i
            )
            add_to_interval_tree(
                interval_tree=interval_tree, start=max(az_1, az_2), end=np.pi, data=i
            )
        else:
            add_to_interval_tree(
                interval_tree=interval_tree,
                start=min(az_1, az_2),
                end=max(az_1, az_2),
                data=i,
            )

    logger.debug(
        f"Building interval tree with {len(interval_tree)} intervals took {time.time() - start_time} seconds"
    )
    return interval_tree
