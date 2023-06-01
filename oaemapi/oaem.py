import logging
import numpy as np
import oaemapi.util as util
from oaemapi.neighborhood import Neighborhood

# logger configuration
logger = logging.getLogger("root")

OAEM_PARAM = 1.5
GRID_RES = 1e-4
WIN_SIZE = 3


class Oaem:
    def __init__(
        self,
        azimuth: np.ndarray = np.linspace(0, 2 * np.pi, 360),
        elevation: np.ndarray = np.zeros((360, 1)),
    ):
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
            return Oaem()

        # create raw oaem
        azimuth, elevation = util.compute_az_el(
            pcloud=neighborhood.all_boundaries(key="interp") - neighborhood.pos.xyz
        )
        azimuth_base_grid, elevation_base_grid = cls.__fill_base_grid(
            res=GRID_RES, azimuth=azimuth, elevation=elevation
        )

        # filter based on convex hull
        azimuth_vs, elevation_vs = cls.__filter_grid(azimuth_base_grid, elevation_base_grid)

        # interpolate
        az_sort_idx = np.argsort(azimuth_vs)
        azimuth_grid = np.arange(-np.pi, np.pi + np.deg2rad(output_res), np.deg2rad(output_res))
        elevation_interp = np.interp(x=azimuth_grid, xp=azimuth_vs[az_sort_idx], fp=elevation_vs[az_sort_idx])
        elevation_interp = util.moving(x=elevation_interp, win_size=WIN_SIZE, function=np.mean)

        # wrap around
        elevation_interp[-1] = elevation_interp[0]
        # no negative mask
        elevation_interp[elevation_interp < 0] = 0

        # unwrap and sort
        azimuth_wraped = util.wrap_to_2pi(azimuth_grid)
        srt_idx = np.argsort(azimuth_wraped)

        logger.debug("done.")
        return cls(azimuth=azimuth_wraped[srt_idx], elevation=elevation_interp[srt_idx])

    @classmethod
    def __filter_grid(cls, azimuth_base_grid, elevation_base_grid):
        # polar coordinates
        oaem_polar = util.azel_to_polar(azimuth_base_grid, elevation_base_grid)

        # convex hull of spherical flipped coordinates (hpr)
        oaem_vs_idx = util.hidden_point_removal(
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
