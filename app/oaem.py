import time
from dataclasses import dataclass, field

import numpy as np
from intervaltree import Interval, IntervalTree
from pointset import PointSet

from app.config import GEOID_RES, N_RES, OAEM_RES, ROUNDING_EPSG, logger
from app.edge import Edge
from app.edge_provider import EdgeProvider
from app.geoid import Geoid


@dataclass
class Oaem:
    """
    Represents an Obstruction Adaptive Elevation Model (OAEM) that stores the elevation data for a given position in space.
    The OAEM is computed from a set of edges that define the building roof footprints.
    """

    pos: PointSet
    azimuth: np.ndarray = field(default_factory=lambda: np.arange(-np.pi, np.pi, OAEM_RES))
    elevation: np.ndarray = field(default_factory=lambda: np.zeros_like(np.arange(0, 2 * np.pi, OAEM_RES)))
    res: float = OAEM_RES

    def __post_init__(self) -> None:
        az_idx = np.argsort(self.azimuth)
        self.azimuth = self.azimuth[az_idx]
        self.elevation = self.elevation[az_idx]

    @property
    def az_el_str(self) -> str:
        return "".join(f"{az:.3f}:{el:.3f}," for az, el in zip(self.azimuth, self.elevation))

    def query(self, azimuth: float) -> np.ndarray:
        if azimuth > np.pi:
            azimuth -= 2 * np.pi

        return np.interp(azimuth, self.azimuth, self.elevation)


def compute_oaem(
    geoid: Geoid,
    edge_provider: EdgeProvider,
    pos_x: float,
    pos_y: float,
    pos_z: float,
    epsg: int,
) -> Oaem:
    """
    Computes an Obstruction Adaptive Elevation Model (OAEM) for a given position.

    Args:
        geoid (Geoid): The geoid object that provides the geoid height for a given position.
        edge_provider (EdgeProvider): The edge provider object that provides the edges for a given position.
        pos_x (float): The x-coordinate of the position.
        pos_y (float): The y-coordinate of the position.
        pos_z (float): The z-coordinate of the position.
        epsg (int): The EPSG code of the position.

    Returns:
        Oaem: An Obstruction Adaptive Elevation Model (OAEM) that stores the elevation data for the given position in space.
    """
    query_time = time.time()
    pos = PointSet(xyz=np.array([pos_x, pos_y, pos_z]), epsg=epsg, init_local_transformer=False)
    pos.to_epsg(ROUNDING_EPSG)
    pos.z -= geoid.interpolate(pos.round_to(GEOID_RES))
    edge_list = edge_provider.get_edges(pos.round_to(N_RES))
    oaem = oaem_from_edge_list(edge_list, pos)
    response_time = time.time()

    logger.debug(
        "Computed OAEM for position [%.3f, %.3f, %.3f], EPSG: %i in %.3f ms",
        pos_x,
        pos_y,
        pos_z,
        epsg,
        (response_time - query_time) * 1000,
    )
    return oaem


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
        return Oaem(pos=pos)

    interval_tree = build_interval_tree(edge_list=edge_list, pos=pos.xyz.ravel())
    oaem_grid = np.arange(-np.pi, np.pi, OAEM_RES)
    oaem_temp = np.zeros((len(oaem_grid), 2), dtype=np.float64)

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

    def add_to_interval_tree(interval_tree: IntervalTree, start: float, end: float, data: float) -> None:
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
            add_to_interval_tree(interval_tree=interval_tree, start=-np.pi, end=min(az_1, az_2), data=i)
            add_to_interval_tree(interval_tree=interval_tree, start=max(az_1, az_2), end=np.pi, data=i)
        else:
            add_to_interval_tree(
                interval_tree=interval_tree,
                start=min(az_1, az_2),
                end=max(az_1, az_2),
                data=i,
            )

    logger.debug(
        "Building interval tree with %i intervals took %.3f seconds",
        len(interval_tree),
        time.time() - start_time,
    )
    return interval_tree
