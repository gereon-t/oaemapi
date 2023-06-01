import logging

import matplotlib.pyplot as plt
import numpy as np
from pointset import PointSet
from oaemapi.config import N_MAX_DIST, N_RANGE, N_RES, WFS_EPSG

from oaemapi.wfs_lod1 import request_wfs_lod1

# logger configuration
logger = logging.getLogger("root")


class Neighborhood:
    """
    Class representing the neighborhood of a requested position
    """

    def __init__(self, pos: PointSet, nrange: float= N_RANGE) -> None:
        pos.to_epsg(WFS_EPSG)
        self.pos = pos
        # round pos
        neighborhood_pos = pos.round_to(N_MAX_DIST)
        # round pos
        self.oaem_pos = pos.round_to(N_RES)

        self.nrange = nrange
        self.buildings = request_wfs_lod1(pos=neighborhood_pos, nrange=nrange)

    def all_boundaries(self, key: str = "boundary") -> np.ndarray:
        all_list = []

        for bldg in self.buildings:
            bldg_interp = bldg.get(key)
            if len(bldg_interp) > 0:
                all_list.append(bldg_interp)

        if all_list:
            all_array = np.row_stack(all_list)
            return np.unique(all_array, axis=0)

        return np.array([])

    def plot_2d(self) -> None:

        bndrs = self.all_boundaries()

        if len(bndrs) > 0:
            plt.figure()
            plt.axis("equal")
            plt.xlabel("x [m]")
            plt.ylabel("y [m]")
            plt.plot(bndrs[:, 0], bndrs[:, 1], "k")
            plt.plot(self.pos.x, self.pos.y, ".r")

    def __key(self):
        return self.oaem_pos

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if isinstance(other, Neighborhood):
            return self.__key() == other.__key()
        return NotImplemented
