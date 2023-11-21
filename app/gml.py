import os
from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np
import xmltodict
from scipy.spatial import KDTree

from app.config import N_RANGE
from app.edge import Edge


@dataclass
class GMLFileList:
    data_path: str
    files: list[str] = field(default_factory=list)

    def add(self, file: str) -> None:
        self.files.append(os.path.join(self.data_path, file))

    def __hash__(self) -> int:
        return "".join(sorted(self.files)).__hash__()


class GMLData:
    def __init__(self, coordinates: list[float]) -> None:
        self.coordinates = np.array(coordinates)
        self.kdtree = KDTree(np.r_[self.coordinates[:, :2], self.coordinates[:, 3:5]])
        self.edges = [
            Edge(start=edge_coord[:3], end=edge_coord[3:])
            for edge_coord in self.coordinates
        ]

    def query_edges(self, pos: np.ndarray, n_range: float = N_RANGE) -> list[Edge]:
        query_indices = self.kdtree.query_ball_point(pos[:, :2].flatten(), r=n_range)
        unique_indices = {index % len(self.edges) for index in query_indices}
        return [self.edges[index] for index in unique_indices]


def gml_file_picker(
    data_path: str, pos: list[float], utm_zone: int = 32, lod: int = 2
) -> GMLFileList:
    """
    Returns the relevant gml file(s) for the given position.

    Args:
        pos (list[float]): Position in UTM coordinates.
        utm_zone (int, optional): UTM zone. Defaults to 32.

    Returns:
        list[str]: List of relevant gml files.
    """
    file_list = GMLFileList(data_path=data_path)
    x_val = int(np.floor(pos[0] / 1000))
    y_val = int(np.floor(pos[1] / 1000))

    file_list.add(f"LoD{lod}_{utm_zone}_{x_val}_{y_val}_1_NW.gml")

    if (pos[0] - x_val * 1000) < N_RANGE:
        file_list.add(f"LoD{lod}_{utm_zone}_{x_val-1}_{y_val}_1_NW.gml")

    if (pos[1] - y_val * 1000) < N_RANGE:
        file_list.add(f"LoD{lod}_{utm_zone}_{x_val}_{y_val-1}_1_NW.gml")

    if (pos[0] - x_val * 1000) > (1000 - N_RANGE):
        file_list.add(f"LoD{lod}_{utm_zone}_{x_val+1}_{y_val}_1_NW.gml")

    if (pos[1] - y_val * 1000) > (1000 - N_RANGE):
        file_list.add(f"LoD{lod}_{utm_zone}_{x_val}_{y_val+1}_1_NW.gml")

    return file_list


def handle_surface_member(surface_member: dict) -> list[float]:
    polygon = (
        surface_member.get("gml:Polygon", {})
        .get("gml:exterior", {})
        .get("gml:LinearRing", {})
        .get("gml:posList", {})
    )

    if isinstance(polygon, dict):
        polygon = polygon.get("#text", None)

    if polygon is None:
        return []

    coords = [float(c) for c in polygon.split(" ")]

    if len(coords) % 3 != 0:
        return []

    if len(coords) < 6:
        return []

    return [coords[i : i + 6] for i in range(0, len(coords) - 3, 3)]


def extract_surface_members(surface: dict) -> list[float]:
    surface_members = (
        surface.get("bldg:lod2MultiSurface", {})
        .get("gml:MultiSurface", {})
        .get("gml:surfaceMember", [])
    )

    if not surface_members:
        return []

    coords = []

    if isinstance(surface_members, list):
        for surface_member in surface_members:
            coords.extend(handle_surface_member(surface_member))
    else:
        coords.extend(handle_surface_member(surface_members))

    return coords


def parse_building_bounds(bounds: dict) -> list[float]:
    building_coordinates = []
    for surfaces in bounds:
        for surface in surfaces.values():
            building_coordinates.extend(extract_surface_members(surface))

    return building_coordinates


def parse_building_data(building_data: dict) -> list[float]:
    if "bldg:Building" not in building_data:
        return []

    building = building_data["bldg:Building"]

    building_coordinates = []
    if "bldg:boundedBy" in building:
        bounded_by = [building["bldg:boundedBy"]]
        for bounds in bounded_by:
            building_coordinates.extend(parse_building_bounds(bounds))

    if "bldg:consistsOfBuildingPart" in building:
        building_parts = building["bldg:consistsOfBuildingPart"]
        for part in building_parts:
            building_part = part["bldg:BuildingPart"]
            bounds = building_part["bldg:boundedBy"]
            building_coordinates.extend(parse_building_bounds(bounds))

    return building_coordinates


def extract_lod2_coords(gml: str) -> list[float]:
    data = xmltodict.parse(gml)

    if "core:CityModel" not in data:
        return ""

    if "core:cityObjectMember" not in data["core:CityModel"]:
        return ""

    building_coordinates = []

    buildings = data["core:CityModel"]["core:cityObjectMember"]

    if not isinstance(buildings, list):
        buildings = [buildings]

    for bdata in buildings:
        building_coordinates.extend(parse_building_data(bdata))

    return building_coordinates


def extract_lod1_coords(gml: str) -> list[float]:
    data = xmltodict.parse(gml)
    cityobject_members = data.get("core:CityModel", {}).get("core:cityObjectMember", {})

    building_coordinates = []
    if not cityobject_members:
        return building_coordinates

    if not isinstance(cityobject_members, list):
        cityobject_members = [cityobject_members]

    for cobj in cityobject_members:
        bldg = cobj.get("bldg:Building", {})

        # single lod1Solid
        if lod1solid := bldg.get("bldg:lod1Solid", {}):
            building_coordinates.extend(parse_lod1solid(lod1solid))

        # multiple lod1Solids
        if bldg_parts := bldg.get("bldg:consistsOfBuildingPart", {}):
            for bpart in bldg_parts:
                lod1solid = bpart.get("bldg:BuildingPart", {}).get("bldg:lod1Solid", {})
                building_coordinates.extend(parse_lod1solid(lod1solid))

    return building_coordinates


def parse_lod1solid(lod1solid: dict) -> list[float]:
    """
    Parses the lod1Solid element of a building

    Args:
        lod1solid (dict): The lod1Solid element of a building.

    Returns:
        list[float]: A list representing the start and end points of the building edges
    """
    surface_members = (
        lod1solid.get("gml:Solid", {})
        .get("gml:exterior", {})
        .get("gml:CompositeSurface", {})
        .get("gml:surfaceMember", {})
    )

    if not surface_members:
        return []

    building_coordinates = []

    for surface in surface_members:
        building_coordinates.extend(handle_surface_member(surface))

    return building_coordinates


@lru_cache(maxsize=128)
def parse_citycml_lod2(filepath: str) -> list[float]:
    if not filepath.endswith(".gml"):
        return []

    with open(filepath, "r", encoding="utf-8") as f:
        data = f.read()
        return extract_lod2_coords(data)


@lru_cache(maxsize=128)
def parse_citycml_lod1(filepath: str) -> list[float]:
    if not filepath.endswith(".gml"):
        return []

    with open(filepath, "r", encoding="utf-8") as f:
        data = f.read()
        return extract_lod1_coords(data)


def main() -> None:
    data_path = "data/bonn_lod1/"
    file_list = gml_file_picker(
        data_path=data_path, pos=[364937.1665, 5621232.2154, 107.9581], lod=1
    )
    coords = []

    for file in file_list.files:
        coords.extend(parse_citycml_lod1(file))

    print(f"Read {len(coords)} coordinates from {file_list.files}")


if __name__ == "__main__":
    main()
