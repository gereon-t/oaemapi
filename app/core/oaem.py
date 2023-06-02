from functools import lru_cache
from typing import Callable, Tuple

import numpy as np
from pointset import PointSet
from scipy.spatial import ConvexHull

from app.config import GRID_RES, OAEM_PARAM, WIN_SIZE, logger
from app.core.neighborhood import Neighborhood


@lru_cache(maxsize=4096)
def oaem_from_pointset(pos: PointSet) -> "Oaem":
    logger.debug(f"computing elevation mask for {pos.x:.3f}, {pos.y:.3f}, {pos.z:.3f}, EPSG: {pos.epsg}")
    neighborhood = Neighborhood(pos=pos)
    return Oaem.from_neighborhood(neighborhood=neighborhood)


class Oaem:
    def __init__(self, azimuth: np.ndarray, elevation: np.ndarray):
        self.azimuth = azimuth
        self.elevation = elevation

    @classmethod
    def from_neighborhood(cls: "Oaem", neighborhood: Neighborhood, output_res: float = 0.5) -> "Oaem":
        """
        Create an OAEM from an neighborhood object
        """
        logger.debug(
            f"computing elevation mask for {neighborhood.pos.x:.3f}, {neighborhood.pos.y:.3f}, {neighborhood.pos.z:.3f}, EPSG: {neighborhood.pos.epsg}"
        )
        if not neighborhood.buildings:
            logger.warning("No buildings within specified range!")
            azimuth = np.arange(0, 2 * np.pi, np.deg2rad(output_res))
            return Oaem(azimuth=np.arange(0, 2 * np.pi, np.deg2rad(output_res)), elevation=np.zeros(len(azimuth)))

        # create raw oaem
        azimuth, elevation = compute_az_el(pcloud=neighborhood.all_boundaries(key="interp") - neighborhood.pos.xyz)
        azimuth_base_grid, elevation_base_grid = cls.__fill_base_grid(
            res=GRID_RES, azimuth=azimuth, elevation=elevation
        )

        # filter based on convex hull
        azimuth_vs, elevation_vs = cls.__filter_grid(azimuth_base_grid, elevation_base_grid)

        # interpolate
        az_sort_idx = np.argsort(azimuth_vs)
        azimuth_grid = np.arange(-np.pi, np.pi + np.deg2rad(output_res), np.deg2rad(output_res))
        elevation_interp = np.interp(x=azimuth_grid, xp=azimuth_vs[az_sort_idx], fp=elevation_vs[az_sort_idx])
        elevation_interp = moving(x=elevation_interp, win_size=WIN_SIZE, function=np.mean)

        # wrap around
        elevation_interp[-1] = elevation_interp[0]
        # no negative mask
        elevation_interp[elevation_interp < 0] = 0

        # unwrap and sort
        azimuth_wraped = wrap_to_2pi(azimuth_grid)
        srt_idx = np.argsort(azimuth_wraped)

        logger.debug("done.")
        return cls(azimuth=azimuth_wraped[srt_idx], elevation=elevation_interp[srt_idx])

    @classmethod
    def __filter_grid(cls, azimuth_base_grid, elevation_base_grid):
        # polar coordinates
        oaem_polar = azel_to_polar(azimuth_base_grid, elevation_base_grid)

        # convex hull of spherical flipped coordinates (hpr)
        oaem_vs_idx = hidden_point_removal(
            pcloud=oaem_polar,
            param=OAEM_PARAM,
        )

        azimuth_vs = azimuth_base_grid[oaem_vs_idx]
        elevation_vs = elevation_base_grid[oaem_vs_idx]

        return azimuth_vs, elevation_vs

    @classmethod
    def __fill_base_grid(cls, res: float, azimuth: np.ndarray, elevation: np.ndarray):
        # create empty base grid
        azimuth_base_grid = np.arange(-np.pi, np.pi + res, res)
        elevation_base_grid = np.zeros(azimuth_base_grid.shape)
        az_indices = np.searchsorted(azimuth_base_grid, azimuth)

        # populate base grid
        azimuth_base_grid[az_indices] = azimuth
        elevation_base_grid[az_indices] = elevation
        return azimuth_base_grid, elevation_base_grid

    @property
    def az_el_str(self) -> str:
        return "".join(f"{az:.3f}:{el:.3f}," for az, el in zip(self.azimuth, self.elevation))


def hidden_point_removal(pcloud: np.ndarray, param: float) -> np.ndarray:
    """
    Hidden Point Removal (Katz et al.)

    pcloud points must be centered around viewpoint
    Returns numpy array with indices of visible points
    """
    normp = np.linalg.norm(pcloud, axis=1, keepdims=True)
    radius = np.tile(np.max(normp) * (10**param), (len(pcloud), 1))
    spherical_flip = pcloud + 2 * (radius - normp) * pcloud / normp
    hull = ConvexHull(spherical_flip)
    return hull.vertices


def compute_az_el(pcloud: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Computes azimuth and elevation from points centered around the viewpoint
    """
    azimuth = np.arctan2(pcloud[:, 0], pcloud[:, 1])
    elevation = np.arctan2(
        pcloud[:, 2],
        np.sqrt(np.power(pcloud[:, 0], 2) + np.power(pcloud[:, 1], 2)),
    )
    return azimuth, elevation


def wrap_to_2pi(angles: np.ndarray) -> np.ndarray:
    """
    Converts angles from interval [-pi, pi] to  [0 2pi]
    """
    return (angles + 2 * np.pi) % (2 * np.pi)


def azel_to_polar(azimuth: np.ndarray, elevation: np.ndarray) -> np.ndarray:
    """
    Converts azimuth and elevation to polar "sky-plot" coordinates
    """
    return np.c_[
        (np.pi / 2 - elevation) * np.cos(azimuth),
        (np.pi / 2 - elevation) * np.sin(azimuth),
    ]


def moving(*, x: np.ndarray, win_size: int, function: Callable[[np.ndarray], float]) -> np.ndarray:
    """
    Function to compute values with
    a given window size and function.
    For example, if function=np.std this method computes the moving
    standard deviation.

    Returns a list.
    """
    if not callable(function):
        raise TypeError("'function' must be Callable[[np.ndarray], float]")

    if win_size == 1:
        return x

    ext = int(np.floor(win_size / 2))

    # extend array
    x = np.r_[x[-ext:], x, x[: ext + 1]]

    # moving
    mov = [function(x[i - ext : i + ext + 1]) for i in range(ext, len(x) - ext - 1)]

    return np.array(mov)
