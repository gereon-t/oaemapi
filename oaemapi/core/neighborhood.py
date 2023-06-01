import logging
import numpy as np
from pointset import PointSet
from oaemapi.config import N_MAX_DIST, N_RANGE, N_RES, WFS_EPSG

from oaemapi.wfs.request import request_wfs_lod1
from oaemapi.wfs.response import parse_response

# logger configuration
logger = logging.getLogger("root")


class Neighborhood:
    """
    Class representing the neighborhood of a requested position
    """

    def __init__(self, pos: PointSet, nrange: float = N_RANGE) -> None:
        self.pos = pos.to_epsg(WFS_EPSG, inplace=False)
        self.neighborhood_pos = pos.round_to(N_MAX_DIST)
        self.oaem_pos = pos.round_to(N_RES)
        self.nrange = nrange

        self.buildings = self.request_buildings()

    def request_buildings(self) -> list:
        response = request_wfs_lod1(pos=self.neighborhood_pos, nrange=self.nrange)
        return parse_response(response)

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

    def __key(self):
        return self.oaem_pos

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if isinstance(other, Neighborhood):
            return self.__key() == other.__key()
        return NotImplemented