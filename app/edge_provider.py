from typing import Protocol
import logging
import numpy as np
import pandas as pd
from app.edge import Edge
from app.wfs import edge_list_from_wfs
from app.config import N_RANGE, EDGE_FILE

from pointset import PointSet
from scipy.spatial import KDTree

logger = logging.getLogger("root")


class EdgeProvider(Protocol):
    def get_edges(self, pos: PointSet) -> list[Edge]:
        ...


class LocalEdgeProvider:
    def __init__(self, filepath: str = EDGE_FILE, epsg: int = 25832) -> None:
        self.filepath = filepath
        self.epsg = epsg
        self.edge_data = pd.read_csv(filepath, header=None).to_numpy(dtype=float)
        logger.info("Loaded %i edges from %s", len(self.edge_data), filepath)

        self.kd_tree = KDTree(
            data=np.r_[self.edge_data[:, 0:3], self.edge_data[:, 3:]][:, 0:2]
        )
        logger.info("Created KDTree")

    def query(self, pos: PointSet, n_range: float = N_RANGE) -> list[int]:
        pos.to_epsg(self.epsg)
        return self.kd_tree.query_ball_point(pos.xyz[:, 0:2].flatten(), r=n_range)

    def get_edges(self, pos: PointSet) -> list[Edge]:
        edge_indices = self.query(pos)

        start_indices = {index % len(self.edge_data) for index in edge_indices}

        return [
            Edge(start=self.edge_data[index, :3], end=self.edge_data[index, 3:])
            for index in start_indices
        ]


class WFSEdgeProvider:
    def __init__(self) -> None:
        pass

    def get_edges(self, pos: PointSet) -> list[Edge]:
        return edge_list_from_wfs(pos)
