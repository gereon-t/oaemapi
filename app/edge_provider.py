import logging
from functools import lru_cache
from typing import Protocol

from pointset import PointSet

from app.edge import Edge
from app.gml import (
    GMLData,
    GMLFileList,
    gml_file_picker,
    parse_citycml_lod1,
    parse_citycml_lod2,
)
from app.wfs import edge_list_from_wfs

logger = logging.getLogger("root")

LOD_PARSER = {1: parse_citycml_lod1, 2: parse_citycml_lod2}


class EdgeProvider(Protocol):
    def get_edges(self, pos: PointSet) -> list[Edge]:
        ...


class LocalEdgeProvider:
    def __init__(self, data_path: str, epsg: int = 25832, lod: int = 2) -> None:
        self.data_path = data_path
        self.epsg = epsg
        self.lod = lod

    @lru_cache(maxsize=128)
    def build_gml_data(self, filepaths: GMLFileList) -> GMLData:
        coords = []

        for file in filepaths.files:
            coords.extend(LOD_PARSER[self.lod](file))

        return GMLData(coordinates=coords)

    @lru_cache(maxsize=512)
    def get_edges(self, pos: PointSet) -> list[Edge]:
        pos.to_epsg(self.epsg)
        utm_zone = int(pos.crs.utm_zone[:-1])
        filepaths = gml_file_picker(
            data_path=self.data_path,
            pos=pos.xyz.flatten().tolist(),
            utm_zone=utm_zone,
            lod=self.lod,
        )
        gml_data = self.build_gml_data(filepaths)
        return gml_data.query_edges(pos.xyz)


class WFSEdgeProvider:
    def __init__(self) -> None:
        pass

    @lru_cache(maxsize=512)
    def get_edges(self, pos: PointSet) -> list[Edge]:
        return edge_list_from_wfs(pos)
