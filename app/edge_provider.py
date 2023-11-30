import logging
from functools import lru_cache
from typing import Protocol

from pointset import PointSet

from app.edge import Edge
from app.gml import GMLData, GMLFileList, gml_file_picker, parse_citygml
from app.wfs import edge_list_from_wfs

logger = logging.getLogger("root")


class EdgeProvider(Protocol):
    """
    Protocol for edge providers.

    Edge providers are used to retrieve building edges from a given position.
    They need to implement the get_edges method.
    """

    def get_edges(self, pos: PointSet) -> list[Edge]:
        ...


class LocalEdgeProvider:
    """
    Edge provider for local CityGML data.

    This edge provider uses local CityGML data to retrieve building edges from a given position.
    The level of detail (LOD) of the data can be specified as 1 or 2. The path to the corresponding
    LOD1 or LOD2 data needs to be provided.
    """

    def __init__(self, data_path: str, epsg: int = 25832, lod: int = 2) -> None:
        self.data_path = data_path
        self.epsg = epsg
        self.lod = lod

    @lru_cache(maxsize=128)
    def build_gml_data(self, filepaths: GMLFileList) -> GMLData:
        """
        Builds a GMLData object from a list of filepaths.

        The GMLData object is cached to avoid unnecessary parsing of the same file(s).
        """
        coords: list[list[float]] = []

        for file in filepaths.files:
            coords.extend(parse_citygml(file, self.lod))

        return GMLData(coordinates=coords)

    @lru_cache(maxsize=512)
    def get_edges(self, pos: PointSet) -> list[Edge]:
        """
        Returns a list of edges for a given position.
        """
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
    """
    Edge provider for WFS data.

    This edge provider uses the WFS API to retrieve building edges from a given position.
    By default, the WFS API of North Rhine-Westphalia (NRW), Germany is used. This API
    only provides LOD1 data.
    """

    def __init__(self) -> None:
        pass

    @lru_cache(maxsize=512)
    def get_edges(self, pos: PointSet) -> list[Edge]:
        return edge_list_from_wfs(pos)
